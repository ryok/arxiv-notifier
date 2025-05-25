"""Notion連携クライアント.

Notion APIを使用して論文情報をデータベースに保存する機能を提供する。
"""

import time
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .models import Paper


class NotionClient:
    """Notion連携クライアント."""

    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(
        self,
        api_key: str | None = None,
        database_id: str | None = None,
    ) -> None:
        """初期化.

        Args:
            api_key: Notion Integration Token（省略時は設定から取得）
            database_id: データベースID（省略時は設定から取得）

        """
        self.api_key = api_key or settings.notion_api_key
        self.database_id = database_id or settings.notion_database_id

        if not self.api_key:
            raise ValueError("Notion API key is not configured")
        if not self.database_id:
            raise ValueError("Notion database ID is not configured")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.API_VERSION,
        }

        self.client = httpx.Client(
            timeout=settings.api_timeout,
            headers=self.headers,
        )

    def __enter__(self) -> "NotionClient":
        """コンテキストマネージャー開始."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャー終了."""
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict:
        """Notion APIリクエストを実行.

        Args:
            method: HTTPメソッド
            endpoint: エンドポイント
            json_data: 送信するJSONデータ

        Returns:
            レスポンスのJSON

        Raises:
            httpx.HTTPError: HTTPエラーが発生した場合

        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            if method == "GET":
                response = self.client.get(url)
            elif method == "POST":
                response = self.client.post(url, json=json_data)
            elif method == "PATCH":
                response = self.client.patch(url, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Notion API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def get_database_schema(self) -> dict:
        """データベーススキーマを取得.

        Returns:
            データベーススキーマ情報

        """
        try:
            result = self._make_request("GET", f"databases/{self.database_id}")
            logger.debug(f"Retrieved database schema: {result.get('title', 'Unknown')}")
            return result
        except Exception as e:
            logger.error(f"Failed to get database schema: {e}")
            raise

    def add_paper(
        self, paper: Paper, japanese_summary: str | None = None
    ) -> dict | None:
        """論文をNotionデータベースに追加.

        Args:
            paper: 論文情報
            japanese_summary: 日本語要約（オプション）

        Returns:
            作成されたページ情報、失敗時はNone

        """
        try:
            # プロパティを構築
            properties = paper.to_notion_properties()

            # 日本語要約がある場合は追加
            if japanese_summary:
                properties["Japanese Summary"] = {
                    "rich_text": [{"text": {"content": japanese_summary}}]
                }

            # ページ作成リクエスト
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
            }

            result = self._make_request("POST", "pages", page_data)

            # レート制限対応（0.33秒待機 = 3リクエスト/秒）
            time.sleep(0.34)

            logger.info(f"Added paper to Notion: {paper.id} - {paper.title}")
            return result

        except Exception as e:
            logger.error(f"Error adding paper {paper.id} to Notion: {e}")
            return None

    def search_paper(self, arxiv_id: str) -> list[dict]:
        """ArXiv IDで論文を検索.

        Args:
            arxiv_id: arXiv ID

        Returns:
            検索結果のページリスト

        """
        try:
            search_data = {
                "filter": {
                    "property": "arXiv ID",
                    "rich_text": {
                        "contains": arxiv_id,
                    },
                },
                "page_size": 10,
            }

            result = self._make_request(
                "POST",
                f"databases/{self.database_id}/query",
                search_data,
            )

            return result.get("results", [])

        except Exception as e:
            logger.error(f"Error searching paper {arxiv_id} in Notion: {e}")
            return []

    def paper_exists(self, arxiv_id: str) -> bool:
        """論文が既に存在するかチェック.

        Args:
            arxiv_id: arXiv ID

        Returns:
            存在する場合True

        """
        results = self.search_paper(arxiv_id)
        return len(results) > 0

    def add_papers_batch(self, papers: list[Paper], skip_existing: bool = True) -> dict:
        """複数の論文をバッチで追加.

        Args:
            papers: 論文リスト
            skip_existing: 既存の論文をスキップするか

        Returns:
            追加結果の辞書 {"success": [成功したPaper], "failed": [失敗したPaper], "skipped": [スキップしたPaper]}

        """
        results = {"success": [], "failed": [], "skipped": []}

        for paper in papers:
            # 既存チェック
            if skip_existing and self.paper_exists(paper.id):
                logger.debug(f"Paper {paper.id} already exists in Notion, skipping")
                results["skipped"].append(paper)
                continue

            # 追加実行
            page = self.add_paper(paper)
            if page:
                results["success"].append(paper)
            else:
                results["failed"].append(paper)

        logger.info(
            f"Batch adding completed: "
            f"{len(results['success'])} success, "
            f"{len(results['failed'])} failed, "
            f"{len(results['skipped'])} skipped"
        )

        return results

    def test_connection(self) -> bool:
        """Notion接続をテスト.

        Returns:
            接続成功の場合True

        """
        try:
            # データベース情報を取得してテスト
            schema = self.get_database_schema()
            logger.info(
                f"Notion connection test successful. "
                f"Database: {schema.get('title', [{}])[0].get('plain_text', 'Unknown')}"
            )
            return True
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return False

    def create_database_if_not_exists(self, parent_page_id: str) -> str:
        """データベースが存在しない場合は作成.

        Args:
            parent_page_id: 親ページのID

        Returns:
            データベースID

        """
        try:
            # 既存のデータベースをチェック
            try:
                self.get_database_schema()
                logger.info("Database already exists")
                return self.database_id
            except Exception:
                pass

            # データベース作成
            database_data = {
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "title": [{"type": "text", "text": {"content": "arXiv Papers"}}],
                "properties": {
                    "Title": {"title": {}},
                    "Authors": {"rich_text": {}},
                    "Abstract": {"rich_text": {}},
                    "Japanese Summary": {"rich_text": {}},
                    "Categories": {"multi_select": {}},
                    "Published Date": {"date": {}},
                    "Updated Date": {"date": {}},
                    "arXiv ID": {"rich_text": {}},
                    "arXiv URL": {"url": {}},
                    "PDF URL": {"url": {}},
                    "Added Date": {"created_time": {}},
                },
            }

            result = self._make_request("POST", "databases", database_data)
            new_database_id = result["id"]

            logger.info(f"Created new database: {new_database_id}")
            return new_database_id

        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
