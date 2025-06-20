"""設定管理モジュール.

環境変数から設定を読み込み、アプリケーション全体で使用する設定を管理する。
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定.

    環境変数から設定を読み込む。.envファイルもサポート。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # arXiv設定
    arxiv_keywords: str | list[str] = Field(
        default=["machine learning", "deep learning"],
        description="検索キーワードリスト",
    )
    arxiv_keyword_operator: str = Field(
        default="OR",
        description="キーワード間の論理演算子（AND/OR）",
    )
    arxiv_categories: str | list[str] = Field(
        default=["cs.LG", "cs.AI", "stat.ML"],
        description="検索カテゴリリスト",
    )
    arxiv_max_results: int = Field(
        default=50,
        description="一度に取得する最大論文数",
    )
    arxiv_days_back: int = Field(
        default=7,
        description="何日前までの論文を取得するか",
    )

    # Slack設定
    slack_webhook_url: str | None = Field(
        default=None,
        description="Slack Webhook URL",
    )
    slack_channel: str | None = Field(
        default=None,
        description="投稿先チャンネル（Webhook URLで指定済みの場合は不要）",
    )
    slack_username: str = Field(
        default="arXiv Bot",
        description="Slack投稿時のユーザー名",
    )
    slack_icon_emoji: str = Field(
        default=":robot_face:",
        description="Slack投稿時のアイコン絵文字",
    )

    # Notion設定
    notion_api_key: str | None = Field(
        default=None,
        description="Notion Integration Token",
    )
    notion_database_id: str | None = Field(
        default=None,
        description="論文を保存するNotionデータベースID",
    )

    # データベース設定
    database_url: str = Field(
        default="sqlite:///./arxiv_papers.db",
        description="SQLiteデータベースURL",
    )
    database_cleanup_days: int = Field(
        default=90,
        description="何日前の処理済みデータを削除するか",
    )

    # スケジューラー設定
    schedule_interval_hours: int = Field(
        default=24,
        description="実行間隔（時間）",
    )
    schedule_time: str | None = Field(
        default="09:00",
        description="実行時刻（HH:MM形式）",
    )

    # ログ設定
    log_level: str = Field(
        default="INFO",
        description="ログレベル",
    )
    log_file: Path = Field(
        default=Path("logs/arxiv_notifier.log"),
        description="ログファイルパス",
    )
    log_rotation: str = Field(
        default="1 day",
        description="ログローテーション設定",
    )
    log_retention: str = Field(
        default="30 days",
        description="ログ保持期間",
    )

    # API設定
    api_timeout: int = Field(
        default=30,
        description="API通信のタイムアウト（秒）",
    )
    api_retry_count: int = Field(
        default=3,
        description="APIリトライ回数",
    )
    api_retry_delay: int = Field(
        default=5,
        description="APIリトライ間隔（秒）",
    )

    # OpenAI設定
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI APIキー",
    )
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        description="使用するOpenAIモデル",
    )

    # プロジェクト概要設定
    project_overview_file: Path | None = Field(
        default=None,
        description="プロジェクト概要マークダウンファイルのパス",
    )
    enable_project_relevance: bool = Field(
        default=False,
        description="プロジェクト関連性評価機能を有効にするか",
    )

    @field_validator("arxiv_keywords", "arxiv_categories", mode="after")
    @classmethod
    def ensure_list(cls, v: str | list[str]) -> list[str]:
        """文字列またはリストをリストに変換."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("arxiv_keyword_operator")
    @classmethod
    def validate_keyword_operator(cls, v: str) -> str:
        """キーワード演算子の検証."""
        v_upper = v.upper()
        if v_upper not in ["AND", "OR"]:
            raise ValueError(f"Invalid keyword operator: {v}. Must be 'AND' or 'OR'")
        return v_upper

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """ログレベルの検証."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("schedule_time")
    @classmethod
    def validate_schedule_time(cls, v: str | None) -> str | None:
        """スケジュール時刻の検証."""
        if v is None:
            return v
        try:
            hour, minute = v.split(":")
            hour_int = int(hour)
            minute_int = int(minute)
            if not (0 <= hour_int <= 23 and 0 <= minute_int <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid schedule time: {v}. Must be in HH:MM format (00:00-23:59)"
            )
        return v

    def is_slack_enabled(self) -> bool:
        """Slack通知が有効かどうか."""
        return bool(self.slack_webhook_url)

    def is_notion_enabled(self) -> bool:
        """Notion連携が有効かどうか."""
        return bool(self.notion_api_key and self.notion_database_id)

    def is_project_relevance_enabled(self) -> bool:
        """プロジェクト関連性評価が有効かどうか."""
        return (
            self.enable_project_relevance
            and self.project_overview_file is not None
            and self.project_overview_file.exists()
            and bool(self.openai_api_key)
        )


# グローバル設定インスタンス
settings = Settings()
