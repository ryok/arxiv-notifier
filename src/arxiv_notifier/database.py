"""データベース管理モジュール.

処理済み論文の記録と重複チェックを管理する。
"""

from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy.orm import Session

from .config import settings
from .models import Paper, ProcessedPaper, SessionLocal


class DatabaseManager:
    """データベース管理クラス."""

    def __init__(self) -> None:
        """初期化."""
        self.session: Session | None = None

    def __enter__(self) -> "DatabaseManager":
        """コンテキストマネージャー開始."""
        self.session = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャー終了."""
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()

    def is_paper_processed(self, arxiv_id: str) -> bool:
        """論文が処理済みかチェック.

        Args:
            arxiv_id: arXiv ID

        Returns:
            処理済みの場合True

        """
        if not self.session:
            raise RuntimeError("Database session not initialized")

        exists = (
            self.session.query(ProcessedPaper)
            .filter(ProcessedPaper.arxiv_id == arxiv_id)
            .first()
            is not None
        )
        return exists

    def mark_paper_as_processed(
        self,
        paper: Paper,
        slack_posted: bool = False,
        notion_added: bool = False,
    ) -> ProcessedPaper:
        """論文を処理済みとして記録.

        Args:
            paper: 論文情報
            slack_posted: Slack投稿済みフラグ
            notion_added: Notion追加済みフラグ

        Returns:
            処理済み論文レコード

        """
        if not self.session:
            raise RuntimeError("Database session not initialized")

        # 既存レコードをチェック
        existing = (
            self.session.query(ProcessedPaper)
            .filter(ProcessedPaper.arxiv_id == paper.id)
            .first()
        )

        if existing:
            # 既存レコードを更新
            existing.slack_posted = existing.slack_posted or slack_posted
            existing.notion_added = existing.notion_added or notion_added
            existing.processed_at = datetime.utcnow()
            logger.debug(f"Updated existing record for paper {paper.id}")
            return existing

        # 新規レコード作成
        processed_paper = ProcessedPaper(
            arxiv_id=paper.id,
            title=paper.title,
            published_date=paper.published_date,
            slack_posted=slack_posted,
            notion_added=notion_added,
        )
        self.session.add(processed_paper)
        logger.debug(f"Created new record for paper {paper.id}")
        return processed_paper

    def update_paper_status(
        self,
        arxiv_id: str,
        slack_posted: bool | None = None,
        notion_added: bool | None = None,
        project_relevance_comment: str | None = None,
    ) -> bool:
        """論文の処理ステータスを更新.

        Args:
            arxiv_id: arXiv ID
            slack_posted: Slack投稿済みフラグ（Noneの場合は更新しない）
            notion_added: Notion追加済みフラグ（Noneの場合は更新しない）
            project_relevance_comment: プロジェクト関連性コメント（Noneの場合は更新しない）

        Returns:
            更新成功の場合True

        """
        if not self.session:
            raise RuntimeError("Database session not initialized")

        paper = (
            self.session.query(ProcessedPaper)
            .filter(ProcessedPaper.arxiv_id == arxiv_id)
            .first()
        )

        if not paper:
            logger.warning(f"Paper {arxiv_id} not found in database")
            return False

        if slack_posted is not None:
            paper.slack_posted = slack_posted
        if notion_added is not None:
            paper.notion_added = notion_added
        if project_relevance_comment is not None:
            paper.project_relevance_comment = project_relevance_comment

        paper.processed_at = datetime.utcnow()
        logger.debug(f"Updated status for paper {arxiv_id}")
        return True

    def get_unprocessed_papers(self, papers: list[Paper]) -> list[Paper]:
        """未処理の論文のみをフィルタリング.

        Args:
            papers: 論文リスト

        Returns:
            未処理の論文リスト

        """
        if not self.session:
            raise RuntimeError("Database session not initialized")

        # 処理済みIDのセットを取得
        processed_ids = set(
            row[0]
            for row in self.session.query(ProcessedPaper.arxiv_id)
            .filter(ProcessedPaper.arxiv_id.in_([p.id for p in papers]))
            .all()
        )

        # 未処理の論文をフィルタリング
        unprocessed = [p for p in papers if p.id not in processed_ids]
        logger.info(
            f"Filtered {len(papers)} papers: "
            f"{len(unprocessed)} unprocessed, {len(processed_ids)} already processed"
        )
        return unprocessed

    def cleanup_old_records(self, days: int | None = None) -> int:
        """古い処理済みレコードを削除.

        Args:
            days: 何日前のレコードを削除するか（デフォルトは設定値）

        Returns:
            削除したレコード数

        """
        if not self.session:
            raise RuntimeError("Database session not initialized")

        days = days or settings.database_cleanup_days
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 削除対象を取得
        old_records = (
            self.session.query(ProcessedPaper)
            .filter(ProcessedPaper.processed_at < cutoff_date)
            .all()
        )

        count = len(old_records)
        if count > 0:
            for record in old_records:
                self.session.delete(record)
            logger.info(f"Deleted {count} old records older than {days} days")
        else:
            logger.debug(f"No old records to delete (older than {days} days)")

        return count

    def get_statistics(self) -> dict:
        """データベース統計情報を取得.

        Returns:
            統計情報の辞書

        """
        if not self.session:
            raise RuntimeError("Database session not initialized")

        total_count = self.session.query(ProcessedPaper).count()
        slack_posted_count = (
            self.session.query(ProcessedPaper)
            .filter(ProcessedPaper.slack_posted == True)
            .count()
        )
        notion_added_count = (
            self.session.query(ProcessedPaper)
            .filter(ProcessedPaper.notion_added == True)
            .count()
        )

        # 最近の処理状況
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_count = (
            self.session.query(ProcessedPaper)
            .filter(ProcessedPaper.processed_at >= recent_date)
            .count()
        )

        return {
            "total_papers": total_count,
            "slack_posted": slack_posted_count,
            "notion_added": notion_added_count,
            "recent_papers_7days": recent_count,
        }
