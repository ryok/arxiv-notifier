"""データモデル定義.

論文情報と処理済み論文の管理に使用するデータモデルを定義する。
"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import Boolean, Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# SQLAlchemy Base
Base = declarative_base()

# データベースエンジンとセッション
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Paper(BaseModel):
    """arXiv論文情報モデル."""

    id: str = Field(..., description="arXiv ID (例: 2301.00001)")
    title: str = Field(..., description="論文タイトル")
    authors: list[str] = Field(..., description="著者リスト")
    abstract: str = Field(..., description="要約")
    categories: list[str] = Field(..., description="カテゴリリスト")
    published_date: datetime = Field(..., description="公開日時")
    updated_date: datetime = Field(..., description="更新日時")
    pdf_url: HttpUrl = Field(..., description="PDFダウンロードURL")
    arxiv_url: HttpUrl = Field(..., description="arXivページURL")

    def get_formatted_authors(self, max_authors: int = 3) -> str:
        """著者リストをフォーマット済み文字列として取得.

        Args:
            max_authors: 表示する最大著者数

        Returns:
            フォーマット済み著者文字列

        """
        if len(self.authors) <= max_authors:
            return ", ".join(self.authors)
        displayed = self.authors[:max_authors]
        remaining = len(self.authors) - max_authors
        return f"{', '.join(displayed)} and {remaining} others"

    def get_primary_category(self) -> str:
        """主要カテゴリを取得.

        Returns:
            主要カテゴリ文字列

        """
        return self.categories[0] if self.categories else "Unknown"

    def to_slack_message(self) -> dict:
        """Slack投稿用メッセージフォーマットに変換.

        Returns:
            Slack Block Kit形式のメッセージ

        """
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📄 {self.title}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Authors:*\n{self.get_formatted_authors()}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Category:*\n{self.get_primary_category()}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Abstract:*\n{self.abstract[:500]}..."
                        if len(self.abstract) > 500
                        else f"*Abstract:*\n{self.abstract}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Published:*\n{self.published_date.strftime('%Y-%m-%d')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*arXiv ID:*\n{self.id}",
                        },
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View on arXiv",
                                "emoji": True,
                            },
                            "url": str(self.arxiv_url),
                            "style": "primary",
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Download PDF",
                                "emoji": True,
                            },
                            "url": str(self.pdf_url),
                        },
                    ],
                },
                {"type": "divider"},
            ]
        }

    def to_notion_properties(self) -> dict:
        """Notion データベースプロパティ形式に変換.

        Returns:
            Notion API用のプロパティ辞書

        """
        return {
            "Title": {"title": [{"text": {"content": self.title}}]},
            "Authors": {
                "rich_text": [{"text": {"content": self.get_formatted_authors(10)}}]
            },
            "Abstract": {"rich_text": [{"text": {"content": self.abstract}}]},
            "Categories": {
                "multi_select": [{"name": cat} for cat in self.categories[:5]]
            },
            "Published Date": {"date": {"start": self.published_date.isoformat()}},
            "Updated Date": {"date": {"start": self.updated_date.isoformat()}},
            "arXiv ID": {"rich_text": [{"text": {"content": self.id}}]},
            "arXiv URL": {"url": str(self.arxiv_url)},
            "PDF URL": {"url": str(self.pdf_url)},
        }


class ProcessedPaper(Base):
    """処理済み論文記録モデル（SQLAlchemy）."""

    __tablename__ = "processed_papers"

    arxiv_id = Column(String, primary_key=True, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    slack_posted = Column(Boolean, default=False)
    notion_added = Column(Boolean, default=False)
    title = Column(String)
    published_date = Column(DateTime)

    def __repr__(self) -> str:
        """文字列表現."""
        return (
            f"<ProcessedPaper(arxiv_id='{self.arxiv_id}', "
            f"processed_at={self.processed_at}, "
            f"slack_posted={self.slack_posted}, "
            f"notion_added={self.notion_added})>"
        )


# テーブル作成
Base.metadata.create_all(bind=engine)
