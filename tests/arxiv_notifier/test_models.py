"""データモデルのテスト."""

from datetime import datetime

import pytest

from src.arxiv_notifier.models import Paper


class TestPaper:
    """Paperモデルのテスト."""

    @pytest.fixture
    def sample_paper_data(self) -> dict:
        """サンプル論文データ."""
        return {
            "id": "2301.00001",
            "title": "Test Paper Title",
            "authors": ["Author One", "Author Two", "Author Three"],
            "abstract": "This is a test abstract for the paper.",
            "categories": ["cs.LG", "cs.AI"],
            "published_date": datetime(2023, 1, 1, 12, 0, 0),
            "updated_date": datetime(2023, 1, 2, 12, 0, 0),
            "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
            "arxiv_url": "https://arxiv.org/abs/2301.00001",
        }

    def test_paper_creation(self, sample_paper_data: dict) -> None:
        """論文モデルの作成テスト."""
        paper = Paper(**sample_paper_data)

        assert paper.id == "2301.00001"
        assert paper.title == "Test Paper Title"
        assert len(paper.authors) == 3
        assert paper.get_primary_category() == "cs.LG"

    def test_get_formatted_authors_short_list(self, sample_paper_data: dict) -> None:
        """著者リストのフォーマット（短いリスト）."""
        paper = Paper(**sample_paper_data)
        formatted = paper.get_formatted_authors(max_authors=5)

        assert formatted == "Author One, Author Two, Author Three"

    def test_get_formatted_authors_long_list(self, sample_paper_data: dict) -> None:
        """著者リストのフォーマット（長いリスト）."""
        sample_paper_data["authors"] = [f"Author {i}" for i in range(10)]
        paper = Paper(**sample_paper_data)
        formatted = paper.get_formatted_authors(max_authors=3)

        assert formatted == "Author 0, Author 1, Author 2 and 7 others"

    def test_get_primary_category_empty(self, sample_paper_data: dict) -> None:
        """主要カテゴリ取得（カテゴリなし）."""
        sample_paper_data["categories"] = []
        paper = Paper(**sample_paper_data)

        assert paper.get_primary_category() == "Unknown"

    def test_to_slack_message(self, sample_paper_data: dict) -> None:
        """Slackメッセージ形式への変換."""
        paper = Paper(**sample_paper_data)
        message = paper.to_slack_message()

        assert "blocks" in message
        assert len(message["blocks"]) > 0

        # ヘッダーブロックの確認
        header_block = message["blocks"][0]
        assert header_block["type"] == "header"
        assert paper.title in header_block["text"]["text"]

    def test_to_notion_properties(self, sample_paper_data: dict) -> None:
        """Notionプロパティ形式への変換."""
        paper = Paper(**sample_paper_data)
        properties = paper.to_notion_properties()

        # 必須プロパティの確認
        assert "Title" in properties
        assert "Authors" in properties
        assert "Abstract" in properties
        assert "Categories" in properties
        assert "Published Date" in properties
        assert "arXiv ID" in properties

        # タイトルプロパティの確認
        title_prop = properties["Title"]
        assert title_prop["title"][0]["text"]["content"] == paper.title

        # カテゴリプロパティの確認
        categories_prop = properties["Categories"]
        assert len(categories_prop["multi_select"]) == 2
        assert categories_prop["multi_select"][0]["name"] == "cs.LG"

    def test_abstract_truncation_in_slack(self, sample_paper_data: dict) -> None:
        """長い要約のSlackメッセージでの切り詰め."""
        # 長い要約を設定
        sample_paper_data["abstract"] = "A" * 600
        paper = Paper(**sample_paper_data)
        message = paper.to_slack_message()

        # 要約ブロックを探す
        abstract_block = None
        for block in message["blocks"]:
            if block.get("type") == "section" and "*Abstract:*" in block.get(
                "text", {}
            ).get("text", ""):
                abstract_block = block
                break

        assert abstract_block is not None
        assert "..." in abstract_block["text"]["text"]
        assert len(abstract_block["text"]["text"]) < 600
