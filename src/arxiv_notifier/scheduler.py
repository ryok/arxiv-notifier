"""スケジューラーモジュール.

定期的な論文取得・通知処理をスケジューリングする。
"""

import signal
import time

import schedule
from loguru import logger

from .config import settings
from .processor import PaperProcessor


class Scheduler:
    """スケジューラークラス."""

    def __init__(self) -> None:
        """初期化."""
        self.running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """シグナルハンドラーを設定."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """シグナルハンドラー.

        Args:
            signum: シグナル番号
            frame: 現在のスタックフレーム

        """
        logger.info(f"Received signal {signum}, stopping scheduler...")
        self.running = False

    def run_job(self) -> None:
        """ジョブを実行."""
        logger.info("Starting scheduled job...")

        try:
            with PaperProcessor() as processor:
                results = processor.process_papers()

                # エラーがあった場合は警告
                if results.get("errors"):
                    logger.warning(f"Job completed with errors: {results['errors']}")
                else:
                    logger.info("Job completed successfully")

        except Exception as e:
            logger.error(f"Job failed with exception: {e}")

    def run_once(self) -> dict:
        """一度だけ実行.

        Returns:
            処理結果

        """
        logger.info("Running one-time execution...")

        try:
            with PaperProcessor() as processor:
                results = processor.process_papers()
                return results
        except Exception as e:
            logger.error(f"One-time execution failed: {e}")
            return {"errors": [str(e)]}

    def test_connections(self) -> dict:
        """接続テストを実行.

        Returns:
            テスト結果

        """
        logger.info("Testing connections...")

        try:
            with PaperProcessor() as processor:
                results = processor.test_connections()

                # 結果をログ出力
                for service, status in results.items():
                    status_text = "OK" if status else "Failed"
                    logger.info(f"{service}: {status_text}")

                return results
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {"error": str(e)}

    def schedule_jobs(self) -> None:
        """ジョブをスケジュール."""
        # 既存のジョブをクリア
        schedule.clear()

        # 設定に基づいてスケジュール
        if settings.schedule_time:
            # 特定時刻での実行
            schedule.every().day.at(settings.schedule_time).do(self.run_job)
            logger.info(f"Scheduled daily job at {settings.schedule_time}")
        else:
            # 間隔での実行
            schedule.every(settings.schedule_interval_hours).hours.do(self.run_job)
            logger.info(f"Scheduled job every {settings.schedule_interval_hours} hours")

    def run(self, run_immediately: bool = False) -> None:
        """スケジューラーを開始.

        Args:
            run_immediately: 起動時に即座に実行するか

        """
        logger.info("Starting scheduler...")
        self.running = True

        # ジョブをスケジュール
        self.schedule_jobs()

        # 即座に実行
        if run_immediately:
            logger.info("Running initial job...")
            self.run_job()

        # 次回実行時刻を表示
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"Next scheduled run: {next_run}")

        # メインループ
        logger.info("Scheduler is running. Press Ctrl+C to stop.")

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック

                # 次回実行時刻が変わった場合は表示
                new_next_run = schedule.next_run()
                if new_next_run and new_next_run != next_run:
                    next_run = new_next_run
                    logger.debug(f"Next scheduled run: {next_run}")

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)

        logger.info("Scheduler stopped")

    def run_with_retry(self, max_retries: int = 3, retry_delay: int = 300) -> None:
        """リトライ機能付きでスケジューラーを実行.

        Args:
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）

        """
        retry_count = 0

        while retry_count < max_retries:
            try:
                self.run(run_immediately=True)
                break  # 正常終了
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Scheduler crashed (attempt {retry_count}/{max_retries}): {e}"
                )

                if retry_count < max_retries:
                    logger.info(f"Restarting in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached, giving up")
                    raise


def create_scheduler() -> Scheduler:
    """スケジューラーインスタンスを作成.

    Returns:
        スケジューラーインスタンス

    """
    return Scheduler()
