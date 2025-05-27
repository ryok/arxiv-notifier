"""NotionClientのテスト."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from notion_client.errors import APIResponseError

from src.arxiv_notifier.models import Paper
from src.arxiv_notifier.notion_client import NotionClient


class TestNotionClient:
    """NotionClientのテスト."""

    @pytest.fixture
    def sample_paper(self) -> Paper:
        """サンプル論文データ."""
        return Paper(
            id="2301.00001",
            title="Test Paper Title",
            authors=["Author One", "Author Two"],
            abstract="This is a test abstract for the paper.",
            categories=["cs.LG", "cs.AI"],
            published_date=datetime(2023, 1, 1, 12, 0, 0),
            updated_date=datetime(2023, 1, 2, 12, 0, 0),
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            arxiv_url="https://arxiv.org/abs/2301.00001",
        )

    @pytest.fixture
    def mock_notion_client(self) -> MagicMock:
        """モックされたNotion Client."""
        return MagicMock()

    def test_init_with_valid_credentials(self) -> None:
        """有効な認証情報での初期化テスト."""
        with patch("src.arxiv_notifier.notion_client.settings") as mock_settings:
            mock_settings.notion_api_key = "test_api_key"
            mock_settings.notion_database_id = "test_database_id"
            mock_settings.api_timeout = 30

            with patch("src.arxiv_notifier.notion_client.Client") as mock_client_class:
                client = NotionClient()

                assert client.api_key == "test_api_key"
                assert client.database_id == "test_database_id"
                mock_client_class.assert_called_once_with(
                    auth="test_api_key", timeout_ms=30000
                )

    def test_init_without_api_key(self) -> None:
        """API keyなしでの初期化エラーテスト."""
        with patch("src.arxiv_notifier.notion_client.settings") as mock_settings:
            mock_settings.notion_api_key = None
            mock_settings.notion_database_id = "test_database_id"

            with pytest.raises(ValueError, match="Notion API key is not configured"):
                NotionClient()

    def test_init_without_database_id(self) -> None:
        """Database IDなしでの初期化エラーテスト."""
        with patch("src.arxiv_notifier.notion_client.settings") as mock_settings:
            mock_settings.notion_api_key = "test_api_key"
            mock_settings.notion_database_id = None

            with pytest.raises(
                ValueError, match="Notion database ID is not configured"
            ):
                NotionClient()

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_get_database_schema_success(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """データベーススキーマ取得成功テスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # データベース取得のモック
        expected_schema = {"title": [{"plain_text": "Test Database"}]}
        mock_notion_client.databases.retrieve.return_value = expected_schema

        client = NotionClient()
        result = client.get_database_schema()

        assert result == expected_schema
        mock_notion_client.databases.retrieve.assert_called_once_with(
            database_id="test_database_id"
        )

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_get_database_schema_error(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """データベーススキーマ取得エラーテスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # エラーのモック
        mock_notion_client.databases.retrieve.side_effect = APIResponseError(
            message="Database not found", code="object_not_found", response=MagicMock()
        )

        client = NotionClient()

        with pytest.raises(Exception):  # RetryErrorまたはAPIResponseErrorをキャッチ
            client.get_database_schema()

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    @patch("src.arxiv_notifier.notion_client.time.sleep")
    def test_add_paper_success(
        self,
        mock_sleep,
        mock_settings,
        mock_client_class,
        mock_notion_client,
        sample_paper,
    ) -> None:
        """論文追加成功テスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # ページ作成のモック
        expected_result = {"id": "page_id_123"}
        mock_notion_client.pages.create.return_value = expected_result

        client = NotionClient()
        result = client.add_paper(sample_paper)

        assert result == expected_result
        mock_notion_client.pages.create.assert_called_once()
        mock_sleep.assert_called_once_with(0.34)

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_add_paper_with_japanese_summary(
        self, mock_settings, mock_client_class, mock_notion_client, sample_paper
    ) -> None:
        """日本語要約付き論文追加テスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # ページ作成のモック
        expected_result = {"id": "page_id_123"}
        mock_notion_client.pages.create.return_value = expected_result

        client = NotionClient()
        japanese_summary = "これは日本語の要約です。"
        result = client.add_paper(sample_paper, japanese_summary)

        assert result == expected_result

        # 呼び出し引数を確認
        call_args = mock_notion_client.pages.create.call_args
        properties = call_args.kwargs["properties"]
        assert "Japanese Summary" in properties
        assert (
            properties["Japanese Summary"]["rich_text"][0]["text"]["content"]
            == japanese_summary
        )

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_search_paper_success(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """論文検索成功テスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # 検索結果のモック
        expected_results = [{"id": "page_1"}, {"id": "page_2"}]
        mock_notion_client.databases.query.return_value = {"results": expected_results}

        client = NotionClient()
        results = client.search_paper("2301.00001")

        assert results == expected_results
        mock_notion_client.databases.query.assert_called_once_with(
            database_id="test_database_id",
            filter={
                "property": "arXiv ID",
                "rich_text": {"contains": "2301.00001"},
            },
            page_size=10,
        )

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_paper_exists_true(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """論文存在確認（存在する場合）テスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # 検索結果のモック（結果あり）
        mock_notion_client.databases.query.return_value = {
            "results": [{"id": "page_1"}]
        }

        client = NotionClient()
        exists = client.paper_exists("2301.00001")

        assert exists is True

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_paper_exists_false(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """論文存在確認（存在しない場合）テスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # 検索結果のモック（結果なし）
        mock_notion_client.databases.query.return_value = {"results": []}

        client = NotionClient()
        exists = client.paper_exists("2301.00001")

        assert exists is False

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_test_connection_success(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """接続テスト成功."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # データベース取得のモック
        mock_notion_client.databases.retrieve.return_value = {
            "title": [{"plain_text": "Test Database"}]
        }

        client = NotionClient()
        result = client.test_connection()

        assert result is True

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_test_connection_failure(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """接続テスト失敗."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # エラーのモック
        mock_notion_client.databases.retrieve.side_effect = APIResponseError(
            message="Unauthorized", code="unauthorized", response=MagicMock()
        )

        client = NotionClient()
        result = client.test_connection()

        assert result is False

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_ensure_database_properties_missing(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """不足しているプロパティの自動作成テスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # 不完全なスキーマのモック（一部プロパティが不足）
        incomplete_schema = {
            "properties": {
                "Title": {"title": {}},
                "Authors": {"rich_text": {}},
                # その他のプロパティが不足
            }
        }
        mock_notion_client.databases.retrieve.return_value = incomplete_schema
        mock_notion_client.databases.update.return_value = {"id": "updated"}

        client = NotionClient()
        result = client._ensure_database_properties()

        assert result is True
        # データベース更新が呼ばれたことを確認
        mock_notion_client.databases.update.assert_called_once()

    @patch("src.arxiv_notifier.notion_client.Client")
    @patch("src.arxiv_notifier.notion_client.settings")
    def test_ensure_database_properties_complete(
        self, mock_settings, mock_client_class, mock_notion_client
    ) -> None:
        """すべてのプロパティが存在する場合のテスト."""
        # 設定のモック
        mock_settings.notion_api_key = "test_api_key"
        mock_settings.notion_database_id = "test_database_id"
        mock_settings.api_timeout = 30

        # Clientクラスのモック
        mock_client_class.return_value = mock_notion_client

        # 完全なスキーマのモック
        complete_schema = {
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
            }
        }
        mock_notion_client.databases.retrieve.return_value = complete_schema

        client = NotionClient()
        result = client._ensure_database_properties()

        assert result is True
        # データベース更新は呼ばれないことを確認
        mock_notion_client.databases.update.assert_not_called()
