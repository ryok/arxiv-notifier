"""Notion連携クライアント.

Notion APIを使用して論文情報をデータベースに保存する機能を提供する。
"""

import time

from loguru import logger
from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .models import Paper


class NotionClient:
    """Notion連携クライアント."""

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

        self.client = Client(
            auth=self.api_key,
            timeout_ms=int(settings.api_timeout * 1000),  # ミリ秒に変換
        )

        # プロパティ確認済みフラグ
        self._properties_ensured = False

    def __enter__(self) -> "NotionClient":
        """コンテキストマネージャー開始."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャー終了."""
        # notion-clientは自動的にリソースを管理するため、明示的なクローズは不要

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _handle_api_call(self, func, *args, **kwargs) -> dict:
        """Notion APIコールを実行してエラーハンドリングを行う.

        Args:
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数

        Returns:
            APIレスポンス

        Raises:
            APIResponseError: API呼び出しエラーが発生した場合

        """
        try:
            return func(*args, **kwargs)
        except (APIResponseError, RequestTimeoutError) as e:
            logger.error(f"Notion API call failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Notion API call: {e}")
            raise

    def get_database_schema(self) -> dict:
        """データベーススキーマを取得.

        Returns:
            データベーススキーマ情報

        """
        try:
            result = self._handle_api_call(
                self.client.databases.retrieve, database_id=self.database_id
            )
            logger.debug(f"Retrieved database schema: {result.get('title', 'Unknown')}")
            return result
        except Exception as e:
            logger.error(f"Failed to get database schema: {e}")
            raise

    def _ensure_database_properties(self) -> bool:
        """データベースに必要なプロパティが存在することを確認し、不足している場合は作成.

        Returns:
            プロパティの確認・作成が成功した場合True

        """
        try:
            schema = self.get_database_schema()
            existing_properties = schema.get("properties", {})

            # 必要なプロパティの定義
            required_properties = {
                "Title": {"title": {}},
                "Authors": {"rich_text": {}},
                "Abstract": {"rich_text": {}},
                "Japanese Summary": {"rich_text": {}},
                "Project Relevance": {"rich_text": {}},
                "Categories": {"multi_select": {}},
                "Published Date": {"date": {}},
                "Updated Date": {"date": {}},
                "arXiv ID": {"rich_text": {}},
                "arXiv URL": {"url": {}},
                "PDF URL": {"url": {}},
            }

            # 不足しているプロパティを特定
            missing_properties = {}
            for prop_name, prop_config in required_properties.items():
                if prop_name not in existing_properties:
                    missing_properties[prop_name] = prop_config
                    logger.info(f"Missing property detected: {prop_name}")

            # 不足しているプロパティがある場合は追加
            if missing_properties:
                logger.info(
                    f"Adding {len(missing_properties)} missing properties to database"
                )

                # データベースを更新
                update_data = {"properties": missing_properties}

                self._handle_api_call(
                    self.client.databases.update,
                    database_id=self.database_id,
                    **update_data,
                )

                logger.info("Successfully added missing properties to database")
            else:
                logger.debug("All required properties exist in database")

            return True

        except Exception as e:
            logger.error(f"Failed to ensure database properties: {e}")
            return False

    def add_paper(
        self, 
        paper: Paper, 
        japanese_summary: str | None = None,
        project_relevance_comment: str | None = None
    ) -> dict | None:
        """論文をNotionデータベースに追加.

        Args:
            paper: 論文情報
            japanese_summary: 日本語要約（オプション）
            project_relevance_comment: プロジェクト関連性コメント（オプション）

        Returns:
            作成されたページ情報、失敗時はNone

        """
        try:
            # データベースプロパティの確認・作成（初回のみ）
            if not self._properties_ensured:
                if not self._ensure_database_properties():
                    logger.error("Failed to ensure database properties")
                    return None
                self._properties_ensured = True

            # プロパティを構築
            properties = paper.to_notion_properties(project_relevance_comment)

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

            result = self._handle_api_call(self.client.pages.create, **page_data)

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

            result = self._handle_api_call(
                self.client.databases.query, database_id=self.database_id, **search_data
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
            title = "Unknown"
            if schema.get("title"):
                title = schema["title"][0].get("plain_text", "Unknown")

            logger.info(f"Notion connection test successful. Database: {title}")
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
                if self.database_id:
                    return self.database_id
                raise ValueError("Database ID is not configured")
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

            result = self._handle_api_call(
                self.client.databases.create, **database_data
            )
            new_database_id = result["id"]

            logger.info(f"Created new database: {new_database_id}")
            return new_database_id

        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
