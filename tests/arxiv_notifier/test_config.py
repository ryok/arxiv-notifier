"""設定管理のテスト."""

from pathlib import Path

import pytest

from src.arxiv_notifier.config import Settings


class TestSettings:
    """設定クラスのテスト."""

    def test_default_settings(self) -> None:
        """デフォルト設定のテスト."""
        settings = Settings()

        # arXiv設定
        assert settings.arxiv_keywords == ["machine learning", "deep learning"]
        assert settings.arxiv_categories == ["cs.LG", "cs.AI", "stat.ML"]
        assert settings.arxiv_max_results == 50
        assert settings.arxiv_days_back == 7

        # Slack設定
        assert settings.slack_webhook_url is None
        assert settings.slack_username == "arXiv Bot"
        assert settings.slack_icon_emoji == ":robot_face:"

        # スケジュール設定
        assert settings.schedule_interval_hours == 24
        assert settings.schedule_time == "09:00"

    def test_env_var_loading(self, monkeypatch) -> None:
        """環境変数からの設定読み込みテスト."""
        # 環境変数を設定
        monkeypatch.setenv("ARXIV_KEYWORDS", "nlp,computer vision")
        monkeypatch.setenv("ARXIV_MAX_RESULTS", "100")
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        settings = Settings()

        assert settings.arxiv_keywords == ["nlp", "computer vision"]
        assert settings.arxiv_max_results == 100
        assert settings.slack_webhook_url == "https://hooks.slack.com/test"
        assert settings.log_level == "DEBUG"

    def test_split_string_list_validator(self) -> None:
        """文字列リスト分割バリデータのテスト."""
        # カンマ区切り文字列
        settings = Settings(arxiv_keywords="ai, ml, dl")
        assert settings.arxiv_keywords == ["ai", "ml", "dl"]

        # リストをそのまま渡す
        settings = Settings(arxiv_keywords=["test1", "test2"])
        assert settings.arxiv_keywords == ["test1", "test2"]

    def test_log_level_validator(self) -> None:
        """ログレベルバリデータのテスト."""
        # 小文字でも大文字に変換される
        settings = Settings(log_level="info")
        assert settings.log_level == "INFO"

        # 無効なログレベル
        with pytest.raises(ValueError, match="Invalid log level"):
            Settings(log_level="INVALID")

    def test_schedule_time_validator(self) -> None:
        """スケジュール時刻バリデータのテスト."""
        # 有効な時刻
        settings = Settings(schedule_time="14:30")
        assert settings.schedule_time == "14:30"

        # Noneも許可
        settings = Settings(schedule_time=None)
        assert settings.schedule_time is None

        # 無効な形式
        with pytest.raises(ValueError, match="Invalid schedule time"):
            Settings(schedule_time="25:00")

        with pytest.raises(ValueError, match="Invalid schedule time"):
            Settings(schedule_time="12:60")

        with pytest.raises(ValueError, match="Invalid schedule time"):
            Settings(schedule_time="invalid")

    def test_is_slack_enabled(self) -> None:
        """Slack有効判定のテスト."""
        # Webhook URLなし
        settings = Settings()
        assert settings.is_slack_enabled() is False

        # Webhook URLあり
        settings = Settings(slack_webhook_url="https://hooks.slack.com/test")
        assert settings.is_slack_enabled() is True

    def test_is_notion_enabled(self) -> None:
        """Notion有効判定のテスト."""
        # 両方なし
        settings = Settings()
        assert settings.is_notion_enabled() is False

        # API keyのみ
        settings = Settings(notion_api_key="secret_key")
        assert settings.is_notion_enabled() is False

        # Database IDのみ
        settings = Settings(notion_database_id="db_id")
        assert settings.is_notion_enabled() is False

        # 両方あり
        settings = Settings(notion_api_key="secret_key", notion_database_id="db_id")
        assert settings.is_notion_enabled() is True

    def test_database_settings(self) -> None:
        """データベース設定のテスト."""
        settings = Settings()

        assert settings.database_url == "sqlite:///./arxiv_papers.db"
        assert settings.database_cleanup_days == 90

    def test_api_settings(self) -> None:
        """API設定のテスト."""
        settings = Settings()

        assert settings.api_timeout == 30
        assert settings.api_retry_count == 3
        assert settings.api_retry_delay == 5

    def test_log_file_path(self) -> None:
        """ログファイルパスのテスト."""
        settings = Settings(log_file="custom/path/app.log")

        assert isinstance(settings.log_file, Path)
        assert str(settings.log_file) == "custom/path/app.log"
