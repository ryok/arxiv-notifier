"""ArxivClientのテスト."""

from unittest.mock import patch

import pytest

from src.arxiv_notifier.arxiv_client import ArxivClient


class TestArxivClient:
    """ArxivClientのテスト."""

    @pytest.fixture
    def arxiv_client(self) -> ArxivClient:
        """ArxivClientインスタンス."""
        with patch("src.arxiv_notifier.arxiv_client.settings") as mock_settings:
            mock_settings.api_timeout = 30
            mock_settings.arxiv_keyword_operator = "OR"
            return ArxivClient()

    def test_parse_keyword_query_simple_or(self, arxiv_client: ArxivClient) -> None:
        """シンプルなORクエリのテスト."""
        keywords = ["machine learning", "deep learning"]
        result = arxiv_client._parse_keyword_query(keywords, "OR")
        expected = '(all:"machine learning" OR all:"deep learning")'
        assert result == expected

    def test_parse_keyword_query_simple_and(self, arxiv_client: ArxivClient) -> None:
        """シンプルなANDクエリのテスト."""
        keywords = ["machine learning", "deep learning"]
        result = arxiv_client._parse_keyword_query(keywords, "AND")
        expected = '(all:"machine learning" AND all:"deep learning")'
        assert result == expected

    def test_parse_keyword_query_complex_expression(
        self, arxiv_client: ArxivClient
    ) -> None:
        """複雑な論理式のテスト."""
        keywords = ["machine learning AND deep learning"]
        result = arxiv_client._parse_keyword_query(keywords, "OR")
        expected = '(all:"machine" all:"learning" AND all:"deep" all:"learning")'
        assert result == expected

    def test_parse_keyword_query_with_parentheses(
        self, arxiv_client: ArxivClient
    ) -> None:
        """括弧を含む論理式のテスト."""
        keywords = ["(computer vision OR image processing) AND deep learning"]
        result = arxiv_client._parse_keyword_query(keywords, "OR")
        expected = '((all:"computer" all:"vision" OR all:"image" all:"processing") AND all:"deep" all:"learning")'
        assert result == expected

    def test_parse_keyword_query_empty(self, arxiv_client: ArxivClient) -> None:
        """空のキーワードリストのテスト."""
        keywords = []
        result = arxiv_client._parse_keyword_query(keywords, "OR")
        assert result == ""

    def test_parse_keyword_query_whitespace_handling(
        self, arxiv_client: ArxivClient
    ) -> None:
        """空白文字の処理テスト."""
        keywords = ["  machine learning  ", "", "  deep learning  "]
        result = arxiv_client._parse_keyword_query(keywords, "OR")
        expected = '(all:"machine learning" OR all:"deep learning")'
        assert result == expected

    def test_parse_keyword_query_case_insensitive_operators(
        self, arxiv_client: ArxivClient
    ) -> None:
        """大文字小文字を区別しない演算子のテスト."""
        keywords = ["machine learning and deep learning"]
        result = arxiv_client._parse_keyword_query(keywords, "OR")
        expected = '(all:"machine" all:"learning" AND all:"deep" all:"learning")'
        assert result == expected

    @patch("src.arxiv_notifier.arxiv_client.settings")
    def test_search_papers_with_keyword_operator(
        self, mock_settings, arxiv_client: ArxivClient
    ) -> None:
        """キーワード演算子を使用した検索のテスト."""
        mock_settings.arxiv_keyword_operator = "AND"

        with patch.object(arxiv_client, "_make_request") as mock_request:
            mock_request.return_value = """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <title>ArXiv Query</title>
                <opensearch:totalResults xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">0</opensearch:totalResults>
            </feed>"""

            keywords = ["machine learning", "deep learning"]
            arxiv_client.search_papers(keywords=keywords)

            # リクエストが呼ばれたことを確認
            mock_request.assert_called_once()
            call_args = mock_request.call_args[0][0]

            # ANDクエリが構築されていることを確認
            assert (
                'all:"machine learning" AND all:"deep learning"'
                in call_args["search_query"]
            )

    @patch("src.arxiv_notifier.arxiv_client.settings")
    def test_search_papers_with_complex_query(
        self, mock_settings, arxiv_client: ArxivClient
    ) -> None:
        """複雑なクエリを使用した検索のテスト."""
        mock_settings.arxiv_keyword_operator = "OR"

        with patch.object(arxiv_client, "_make_request") as mock_request:
            mock_request.return_value = """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <title>ArXiv Query</title>
                <opensearch:totalResults xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">0</opensearch:totalResults>
            </feed>"""

            keywords = ["machine learning AND (neural network OR transformer)"]
            arxiv_client.search_papers(keywords=keywords)

            # リクエストが呼ばれたことを確認
            mock_request.assert_called_once()
            call_args = mock_request.call_args[0][0]

            # 複雑なクエリが構築されていることを確認
            query = call_args["search_query"]
            assert 'all:"machine"' in query
            assert 'all:"learning"' in query
            assert "AND" in query
            assert "OR" in query

    def test_operator_validation_and(self, arxiv_client: ArxivClient) -> None:
        """AND演算子の大文字小文字処理テスト."""
        keywords = ["keyword1", "keyword2"]
        result = arxiv_client._parse_keyword_query(keywords, "and")
        expected = '(all:"keyword1" AND all:"keyword2")'
        assert result == expected

    def test_operator_validation_or(self, arxiv_client: ArxivClient) -> None:
        """OR演算子の大文字小文字処理テスト."""
        keywords = ["keyword1", "keyword2"]
        result = arxiv_client._parse_keyword_query(keywords, "or")
        expected = '(all:"keyword1" OR all:"keyword2")'
        assert result == expected

    def test_single_keyword_no_operators(self, arxiv_client: ArxivClient) -> None:
        """演算子を含まない単一キーワードのテスト."""
        keywords = ["machine learning"]
        result = arxiv_client._parse_keyword_query(keywords, "OR")
        expected = '(all:"machine learning")'
        assert result == expected
