"""arXiv APIクライアント.

arXiv APIを使用して論文を検索・取得する機能を提供する。
"""

import re
import time
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree as ET

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .models import Paper


class ArxivClient:
    """arXiv APIクライアント."""

    BASE_URL = "http://export.arxiv.org/api/query"
    NAMESPACE = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    def __init__(self) -> None:
        """初期化."""
        self.client = httpx.Client(timeout=settings.api_timeout)

    def __enter__(self) -> "ArxivClient":
        """コンテキストマネージャー開始."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャー終了."""
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _make_request(self, params: dict) -> str:
        """APIリクエストを実行.

        Args:
            params: クエリパラメータ

        Returns:
            レスポンスのXML文字列

        Raises:
            httpx.HTTPError: HTTPエラーが発生した場合

        """
        logger.debug(f"Making request to arXiv API with params: {params}")
        response = self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.text

    def _parse_paper(self, entry: ET.Element) -> Paper | None:
        """XMLエントリから論文情報をパース.

        Args:
            entry: XMLエントリ要素

        Returns:
            論文情報オブジェクト、パース失敗時はNone

        """
        try:
            # ID抽出
            id_elem = entry.find("atom:id", self.NAMESPACE)
            if id_elem is None or id_elem.text is None:
                logger.warning("Paper ID not found")
                return None

            arxiv_id = id_elem.text.split("/")[-1]

            # タイトル抽出（改行・余分な空白を除去）
            title_elem = entry.find("atom:title", self.NAMESPACE)
            if title_elem is None or title_elem.text is None:
                logger.warning(f"Title not found for paper {arxiv_id}")
                return None

            title = re.sub(r"\s+", " ", title_elem.text.strip())

            # 著者抽出
            authors = []
            for author in entry.findall("atom:author", self.NAMESPACE):
                name_elem = author.find("atom:name", self.NAMESPACE)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            if not authors:
                logger.warning(f"No authors found for paper {arxiv_id}")
                return None

            # 要約抽出（改行・余分な空白を除去）
            summary_elem = entry.find("atom:summary", self.NAMESPACE)
            if summary_elem is None or summary_elem.text is None:
                logger.warning(f"Summary not found for paper {arxiv_id}")
                return None

            abstract = re.sub(r"\s+", " ", summary_elem.text.strip())

            # カテゴリ抽出
            categories = []
            for category in entry.findall("atom:category", self.NAMESPACE):
                term = category.get("term")
                if term:
                    categories.append(term)

            # 日付抽出
            published_elem = entry.find("atom:published", self.NAMESPACE)
            updated_elem = entry.find("atom:updated", self.NAMESPACE)

            if published_elem is None or published_elem.text is None:
                logger.warning(f"Published date not found for paper {arxiv_id}")
                return None

            published_date = datetime.fromisoformat(
                published_elem.text.replace("Z", "+00:00")
            )
            updated_date = (
                datetime.fromisoformat(updated_elem.text.replace("Z", "+00:00"))
                if updated_elem is not None and updated_elem.text
                else published_date
            )

            # URL構築
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"

            return Paper(
                id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                categories=categories,
                published_date=published_date,
                updated_date=updated_date,
                pdf_url=pdf_url,
                arxiv_url=arxiv_url,
            )

        except Exception as e:
            logger.error(f"Error parsing paper entry: {e}")
            return None

    def search_papers(
        self,
        keywords: list[str] | None = None,
        categories: list[str] | None = None,
        start_date: datetime | None = None,
        max_results: int = 50,
        start_index: int = 0,
    ) -> list[Paper]:
        """論文を検索.

        Args:
            keywords: 検索キーワードリスト
            categories: カテゴリリスト
            start_date: 検索開始日（これ以降の論文を取得）
            max_results: 最大取得件数
            start_index: 開始インデックス（ページネーション用）

        Returns:
            論文リスト

        """
        # クエリ構築
        query_parts = []

        # キーワード検索
        if keywords:
            keyword_query = " OR ".join([f'all:"{kw}"' for kw in keywords])
            query_parts.append(f"({keyword_query})")

        # カテゴリ検索
        if categories:
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            query_parts.append(f"({cat_query})")

        # 日付フィルタ（submittedDateを使用）
        if start_date:
            date_str = start_date.strftime("%Y%m%d")
            end_date_str = datetime.now(UTC).strftime("%Y%m%d")
            query_parts.append(f"submittedDate:[{date_str} TO {end_date_str}]")

        # クエリが空の場合はデフォルトクエリ
        if not query_parts:
            query = "all:*"
        else:
            query = " AND ".join(query_parts)

        params = {
            "search_query": query,
            "start": start_index,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            # APIリクエスト
            xml_response = self._make_request(params)

            # XMLパース
            root = ET.fromstring(xml_response)

            # エントリ抽出
            papers = []
            for entry in root.findall("atom:entry", self.NAMESPACE):
                paper = self._parse_paper(entry)
                if paper:
                    papers.append(paper)

            logger.info(f"Found {len(papers)} papers")

            # レート制限対応（3秒待機）
            time.sleep(3)

            return papers

        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []

    def get_recent_papers(
        self,
        days_back: int | None = None,
        keywords: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> list[Paper]:
        """最近の論文を取得.

        Args:
            days_back: 何日前までの論文を取得するか
            keywords: 検索キーワードリスト
            categories: カテゴリリスト

        Returns:
            論文リスト

        """
        days_back = days_back or settings.arxiv_days_back
        keywords = keywords or settings.arxiv_keywords
        categories = categories or settings.arxiv_categories

        # タイムゾーン付きのdatetimeを使用
        start_date = datetime.now(UTC) - timedelta(days=days_back)

        all_papers = []
        start_index = 0
        max_results = settings.arxiv_max_results

        while True:
            papers = self.search_papers(
                keywords=keywords,
                categories=categories,
                start_date=start_date,
                max_results=max_results,
                start_index=start_index,
            )

            if not papers:
                break

            all_papers.extend(papers)

            # 取得件数が最大件数未満なら終了
            if len(papers) < max_results:
                break

            start_index += max_results

            # 総取得数が多すぎる場合は打ち切り
            if len(all_papers) >= 500:
                logger.warning("Reached maximum paper limit (500)")
                break

        # 日付でフィルタリング（APIの日付フィルタが不完全な場合の対策）
        filtered_papers = [
            paper
            for paper in all_papers
            if paper.published_date >= start_date or paper.updated_date >= start_date
        ]

        logger.info(
            f"Retrieved {len(filtered_papers)} papers from the last {days_back} days"
        )

        return filtered_papers
