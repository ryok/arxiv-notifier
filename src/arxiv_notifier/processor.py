"""メイン処理ロジック.

arXiv論文の取得、フィルタリング、通知を統合的に処理する。
"""

from datetime import datetime

from loguru import logger

from .arxiv_client import ArxivClient
from .config import settings
from .database import DatabaseManager
from .models import Paper
from .notion_client import NotionClient
from .project_relevance import get_evaluator
from .slack_client import SlackClient
from .summarizer import get_summarizer


class PaperProcessor:
    """論文処理の統合クラス."""

    def __init__(self) -> None:
        """初期化."""
        self.arxiv_client: ArxivClient | None = None
        self.slack_client: SlackClient | None = None
        self.notion_client: NotionClient | None = None
        self.db_manager: DatabaseManager | None = None
        self.summarizer = get_summarizer()
        self.relevance_evaluator = get_evaluator()

    def __enter__(self) -> "PaperProcessor":
        """コンテキストマネージャー開始."""
        self.arxiv_client = ArxivClient()
        self.db_manager = DatabaseManager().__enter__()

        # Slack/Notionは設定されている場合のみ初期化
        if settings.is_slack_enabled():
            self.slack_client = SlackClient()
        if settings.is_notion_enabled():
            self.notion_client = NotionClient()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャー終了."""
        if self.arxiv_client:
            self.arxiv_client.__exit__(exc_type, exc_val, exc_tb)
        if self.slack_client:
            self.slack_client.__exit__(exc_type, exc_val, exc_tb)
        if self.notion_client:
            self.notion_client.__exit__(exc_type, exc_val, exc_tb)
        if self.db_manager:
            self.db_manager.__exit__(exc_type, exc_val, exc_tb)

    def fetch_papers(self) -> list[Paper]:
        """arXivから論文を取得.

        Returns:
            取得した論文リスト

        """
        if not self.arxiv_client:
            raise RuntimeError("ArxivClient not initialized")

        logger.info("Fetching papers from arXiv...")
        papers = self.arxiv_client.get_recent_papers()
        logger.info(f"Fetched {len(papers)} papers from arXiv")
        return papers

    def filter_new_papers(self, papers: list[Paper]) -> list[Paper]:
        """新規論文のみをフィルタリング.

        Args:
            papers: 論文リスト

        Returns:
            未処理の論文リスト

        """
        if not self.db_manager:
            raise RuntimeError("DatabaseManager not initialized")

        logger.info("Filtering new papers...")
        new_papers = self.db_manager.get_unprocessed_papers(papers)
        logger.info(f"Found {len(new_papers)} new papers")
        return new_papers

    def post_to_slack(self, papers: list[Paper]) -> dict:
        """Slackに論文を投稿.

        Args:
            papers: 論文リスト

        Returns:
            投稿結果

        """
        if not self.slack_client:
            logger.warning("Slack client not initialized, skipping Slack posting")
            return {"success": [], "failed": []}

        logger.info(f"Posting {len(papers)} papers to Slack...")

        # サマリーを投稿
        self.slack_client.post_summary(papers)

        # 投稿する論文を制限
        papers_to_post = papers[:10]  # 最大10件

        if len(papers) > 10:
            logger.warning(f"Limiting posts to 10 papers out of {len(papers)}")

        # 個別論文を投稿（日本語要約付き）
        results = {"success": [], "failed": []}

        for paper in papers_to_post:
            # 日本語要約を生成
            japanese_summary = None
            if self.summarizer.is_enabled():
                try:
                    japanese_summary = self.summarizer.generate_summary(paper)
                    if japanese_summary:
                        logger.debug(f"Generated Japanese summary for paper {paper.id}")
                except Exception as e:
                    logger.warning(
                        f"Failed to generate summary for paper {paper.id}: {e}"
                    )

            # プロジェクト関連性を評価
            project_relevance = None
            if self.relevance_evaluator and self.relevance_evaluator.is_enabled():
                try:
                    import asyncio
                    project_relevance = asyncio.run(
                        self.relevance_evaluator.evaluate_relevance(paper)
                    )
                    if project_relevance:
                        logger.debug(f"Generated project relevance for paper {paper.id}")
                except Exception as e:
                    logger.warning(
                        f"Failed to evaluate project relevance for paper {paper.id}: {e}"
                    )

            # Slackに投稿
            if self.slack_client.post_paper(paper, japanese_summary, project_relevance):
                results["success"].append(paper)
            else:
                results["failed"].append(paper)

        logger.info(
            f"Batch posting completed: "
            f"{len(results['success'])} success, {len(results['failed'])} failed"
        )

        # 成功した論文をデータベースに記録（関連性コメント含む）
        if self.db_manager:
            for i, paper in enumerate(results["success"]):
                # 対応する関連性コメントを取得
                project_relevance = None
                if i < len(papers_to_post) and self.relevance_evaluator and self.relevance_evaluator.is_enabled():
                    try:
                        import asyncio
                        project_relevance = asyncio.run(
                            self.relevance_evaluator.evaluate_relevance(paper)
                        )
                    except Exception:
                        pass
                self.db_manager.update_paper_status(
                    paper.id, 
                    slack_posted=True, 
                    project_relevance_comment=project_relevance
                )

        return results

    def add_to_notion(self, papers: list[Paper]) -> dict:
        """Notionに論文を追加.

        Args:
            papers: 論文リスト

        Returns:
            追加結果

        """
        if not self.notion_client:
            logger.warning("Notion client not initialized, skipping Notion adding")
            return {"success": [], "failed": [], "skipped": []}

        logger.info(f"Adding {len(papers)} papers to Notion...")

        # 日本語要約を含むプロパティで論文を追加
        results = {"success": [], "failed": [], "skipped": []}

        for paper in papers:
            try:
                # 日本語要約を生成
                japanese_summary = None
                if self.summarizer.is_enabled():
                    try:
                        japanese_summary = self.summarizer.generate_summary(paper)
                    except Exception as e:
                        logger.warning(
                            f"Failed to generate summary for paper {paper.id}: {e}"
                        )

                # プロジェクト関連性を評価
                project_relevance = None
                if self.relevance_evaluator and self.relevance_evaluator.is_enabled():
                    try:
                        import asyncio
                        project_relevance = asyncio.run(
                            self.relevance_evaluator.evaluate_relevance(paper)
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to evaluate project relevance for paper {paper.id}: {e}"
                        )

                # Notionに追加（要約・関連性コメントを含める）
                if self.notion_client.add_paper(paper, japanese_summary, project_relevance):
                    results["success"].append(paper)
                else:
                    results["failed"].append(paper)

            except Exception as e:
                logger.error(f"Error adding paper {paper.id} to Notion: {e}")
                results["failed"].append(paper)

        # 成功した論文をデータベースに記録
        if self.db_manager:
            for paper in results["success"]:
                self.db_manager.update_paper_status(paper.id, notion_added=True)

        return results

    def process_papers(self) -> dict:
        """論文処理のメインフロー.

        Returns:
            処理結果のサマリー

        """
        start_time = datetime.now()
        results = {
            "fetched": 0,
            "new": 0,
            "slack_posted": 0,
            "notion_added": 0,
            "errors": [],
        }

        try:
            # 1. arXivから論文を取得
            papers = self.fetch_papers()
            results["fetched"] = len(papers)

            if not papers:
                logger.info("No papers found")
                return results

            # 2. 新規論文をフィルタリング
            new_papers = self.filter_new_papers(papers)
            results["new"] = len(new_papers)

            if not new_papers:
                logger.info("No new papers to process")
                return results

            # 3. データベースに記録
            if self.db_manager:
                for paper in new_papers:
                    self.db_manager.mark_paper_as_processed(paper)
                # 変更をコミットして、後続の処理で参照できるようにする
                if self.db_manager.session:
                    self.db_manager.session.commit()

            # 4. Slackに投稿
            if self.slack_client:
                slack_results = self.post_to_slack(new_papers)
                results["slack_posted"] = len(slack_results["success"])
                if slack_results["failed"]:
                    results["errors"].append(
                        f"Failed to post {len(slack_results['failed'])} papers to Slack"
                    )

            # 5. Notionに追加
            if self.notion_client:
                notion_results = self.add_to_notion(new_papers)
                results["notion_added"] = len(notion_results["success"])
                if notion_results["failed"]:
                    results["errors"].append(
                        f"Failed to add {len(notion_results['failed'])} papers to Notion"
                    )

            # 6. 古いレコードをクリーンアップ
            if self.db_manager:
                deleted = self.db_manager.cleanup_old_records()
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old records")

        except Exception as e:
            logger.error(f"Error in paper processing: {e}")
            results["errors"].append(str(e))

        # 処理時間を記録
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time_seconds"] = processing_time

        # サマリーログ
        logger.info(
            f"Processing completed in {processing_time:.2f} seconds. "
            f"Fetched: {results['fetched']}, "
            f"New: {results['new']}, "
            f"Slack: {results['slack_posted']}, "
            f"Notion: {results['notion_added']}"
        )

        if results["errors"]:
            logger.warning(f"Errors occurred: {results['errors']}")

        return results

    def test_connections(self) -> dict:
        """各サービスへの接続をテスト.

        Returns:
            テスト結果

        """
        results = {
            "arxiv": False,
            "database": False,
            "slack": False,
            "notion": False,
            "openai": False,
        }

        # arXiv接続テスト
        try:
            if self.arxiv_client:
                test_papers = self.arxiv_client.search_papers(
                    keywords=["test"], max_results=1
                )
                results["arxiv"] = True
                logger.info("arXiv connection test: OK")
        except Exception as e:
            logger.error(f"arXiv connection test failed: {e}")

        # データベース接続テスト
        try:
            if self.db_manager:
                stats = self.db_manager.get_statistics()
                results["database"] = True
                logger.info(
                    f"Database connection test: OK ({stats['total_papers']} papers)"
                )
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")

        # Slack接続テスト
        try:
            if self.slack_client:
                results["slack"] = self.slack_client.test_connection()
                logger.info(
                    f"Slack connection test: {'OK' if results['slack'] else 'Failed'}"
                )
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")

        # Notion接続テスト
        try:
            if self.notion_client:
                results["notion"] = self.notion_client.test_connection()
                logger.info(
                    f"Notion connection test: {'OK' if results['notion'] else 'Failed'}"
                )
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")

        # OpenAI接続テスト
        try:
            if self.summarizer.is_enabled():
                # 簡単なテスト論文で要約生成を試す
                test_paper = Paper(
                    id="test123",
                    title="Test Paper",
                    authors=["Test Author"],
                    abstract="This is a test abstract for connection testing.",
                    categories=["cs.LG"],
                    published_date=datetime.now(),
                    updated_date=datetime.now(),
                    pdf_url="https://example.com/test.pdf",
                    arxiv_url="https://arxiv.org/abs/test123",
                )
                summary = self.summarizer.generate_summary(test_paper)
                results["openai"] = summary is not None
                logger.info(
                    f"OpenAI connection test: {'OK' if results['openai'] else 'Failed'}"
                )
            else:
                logger.info("OpenAI connection test: Skipped (not configured)")
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")

        # プロジェクト関連性評価テスト
        results["project_relevance"] = False
        try:
            if self.relevance_evaluator and self.relevance_evaluator.is_enabled():
                # 簡単なテスト論文で関連性評価を試す
                test_paper = Paper(
                    id="test123",
                    title="Test Paper",
                    authors=["Test Author"],
                    abstract="This is a test abstract for connection testing.",
                    categories=["cs.LG"],
                    published_date=datetime.now(),
                    updated_date=datetime.now(),
                    pdf_url="https://example.com/test.pdf",
                    arxiv_url="https://arxiv.org/abs/test123",
                )
                import asyncio
                relevance = asyncio.run(self.relevance_evaluator.evaluate_relevance(test_paper))
                results["project_relevance"] = True  # 例外が発生しなければ成功
                logger.info("Project relevance evaluation test: OK")
            else:
                logger.info("Project relevance evaluation test: Skipped (not configured)")
        except Exception as e:
            logger.error(f"Project relevance evaluation test failed: {e}")

        return results
