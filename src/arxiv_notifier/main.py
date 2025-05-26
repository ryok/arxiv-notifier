"""メインエントリーポイント.

CLIコマンドを提供し、各種機能を実行する。
"""

import sys
from pathlib import Path

import click
from loguru import logger

from .config import settings
from .scheduler import create_scheduler


def setup_logging() -> None:
    """ログ設定をセットアップ."""
    # 既存のハンドラーを削除
    logger.remove()

    # コンソール出力
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # ファイル出力
    log_file = settings.log_file
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
    )


@click.group()
@click.version_option(version="0.1.0", prog_name="arxiv-notifier")
def cli() -> None:
    """arXiv論文自動収集・通知システム."""
    setup_logging()


@cli.command()
@click.option(
    "--immediately",
    "-i",
    is_flag=True,
    help="起動時に即座に実行する",
)
def run(immediately: bool) -> None:
    """スケジューラーを起動して定期実行."""
    logger.info("Starting arXiv Notifier...")

    # 設定を表示
    logger.info(f"Keywords: {', '.join(settings.arxiv_keywords)}")
    logger.info(f"Categories: {', '.join(settings.arxiv_categories)}")
    logger.info(f"Days back: {settings.arxiv_days_back}")

    if settings.is_slack_enabled():
        logger.info("Slack notifications: Enabled")
    else:
        logger.info("Slack notifications: Disabled")

    if settings.is_notion_enabled():
        logger.info("Notion integration: Enabled")
    else:
        logger.info("Notion integration: Disabled")

    # スケジューラーを起動
    scheduler = create_scheduler()

    try:
        scheduler.run(run_immediately=immediately)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="エラー以外のログ出力を抑制する（外部スケジューラー用）",
)
@click.option(
    "--exit-code-on-no-new",
    is_flag=True,
    help="新しい論文がない場合に終了コード1で終了する",
)
def once(quiet: bool, exit_code_on_no_new: bool) -> None:
    """一度だけ実行."""
    if quiet:
        # quietモードの場合、ログレベルをWARNINGに設定
        from loguru import logger as loguru_logger

        loguru_logger.remove()
        loguru_logger.add(
            sys.stderr,
            level="WARNING",
            format="<level>{level}: {message}</level>",
        )
        logger.info("Running one-time execution (quiet mode)...")
    else:
        logger.info("Running one-time execution...")

    scheduler = create_scheduler()
    results = scheduler.run_once()

    # 結果を表示
    if results.get("errors"):
        logger.error(f"Execution failed with errors: {results['errors']}")
        sys.exit(1)
    else:
        if not quiet:
            logger.info(
                f"Execution completed successfully. "
                f"Fetched: {results.get('fetched', 0)}, "
                f"New: {results.get('new', 0)}, "
                f"Slack: {results.get('slack_posted', 0)}, "
                f"Notion: {results.get('notion_added', 0)}"
            )

        # 新しい論文がない場合の処理
        if exit_code_on_no_new and results.get("new", 0) == 0:
            if not quiet:
                logger.info("No new papers found, exiting with code 1")
            sys.exit(1)


@cli.command()
def test() -> None:
    """接続テストを実行."""
    logger.info("Running connection tests...")

    scheduler = create_scheduler()
    results = scheduler.test_connections()

    # 結果をサマリー表示
    all_ok = all(status for service, status in results.items() if service != "error")

    if all_ok:
        logger.info("All connection tests passed!")
    else:
        logger.error("Some connection tests failed")
        sys.exit(1)


@cli.command()
def config() -> None:
    """現在の設定を表示."""
    logger.info("Current configuration:")

    # arXiv設定
    click.echo("\n[arXiv Settings]")
    click.echo(f"Keywords: {', '.join(settings.arxiv_keywords)}")
    click.echo(f"Categories: {', '.join(settings.arxiv_categories)}")
    click.echo(f"Max results: {settings.arxiv_max_results}")
    click.echo(f"Days back: {settings.arxiv_days_back}")

    # Slack設定
    click.echo("\n[Slack Settings]")
    if settings.is_slack_enabled():
        click.echo("Status: Enabled")
        click.echo(f"Username: {settings.slack_username}")
        click.echo(f"Icon: {settings.slack_icon_emoji}")
        if settings.slack_channel:
            click.echo(f"Channel: {settings.slack_channel}")
    else:
        click.echo("Status: Disabled (SLACK_WEBHOOK_URL not set)")

    # Notion設定
    click.echo("\n[Notion Settings]")
    if settings.is_notion_enabled():
        click.echo("Status: Enabled")
        click.echo(f"Database ID: {settings.notion_database_id}")
    else:
        click.echo("Status: Disabled (NOTION_API_KEY or NOTION_DATABASE_ID not set)")

    # OpenAI設定
    click.echo("\n[OpenAI Settings]")
    if settings.openai_api_key:
        click.echo("Status: Enabled")
        click.echo(f"Model: {settings.openai_model}")
    else:
        click.echo("Status: Disabled (OPENAI_API_KEY not set)")

    # スケジュール設定
    click.echo("\n[Schedule Settings]")
    if settings.schedule_time:
        click.echo(f"Schedule: Daily at {settings.schedule_time}")
    else:
        click.echo(f"Schedule: Every {settings.schedule_interval_hours} hours")

    # データベース設定
    click.echo("\n[Database Settings]")
    click.echo(f"Database URL: {settings.database_url}")
    click.echo(f"Cleanup days: {settings.database_cleanup_days}")

    # ログ設定
    click.echo("\n[Log Settings]")
    click.echo(f"Log level: {settings.log_level}")
    click.echo(f"Log file: {settings.log_file}")
    click.echo(f"Rotation: {settings.log_rotation}")
    click.echo(f"Retention: {settings.log_retention}")


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path(".env.example"),
    help="出力ファイルパス",
)
def generate_env(output: Path) -> None:
    """環境変数のサンプルファイルを生成."""
    env_content = """# arXiv Notifier Configuration

# arXiv Settings
ARXIV_KEYWORDS="machine learning,deep learning,neural network"
ARXIV_CATEGORIES="cs.LG,cs.AI,stat.ML"
ARXIV_MAX_RESULTS=50
ARXIV_DAYS_BACK=7

# Slack Settings (Optional)
# Get webhook URL from: https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL=
SLACK_CHANNEL=
SLACK_USERNAME="arXiv Bot"
SLACK_ICON_EMOJI=":robot_face:"

# Notion Settings (Optional)
# Create integration at: https://www.notion.so/my-integrations
NOTION_API_KEY=
NOTION_DATABASE_ID=

# OpenAI Settings (Optional)
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=
OPENAI_MODEL="gpt-3.5-turbo"

# Schedule Settings
SCHEDULE_INTERVAL_HOURS=24
SCHEDULE_TIME="09:00"

# Database Settings
DATABASE_URL="sqlite:///./arxiv_papers.db"
DATABASE_CLEANUP_DAYS=90

# Log Settings
LOG_LEVEL="INFO"
LOG_FILE="logs/arxiv_notifier.log"
LOG_ROTATION="1 day"
LOG_RETENTION="30 days"

# API Settings
API_TIMEOUT=30
API_RETRY_COUNT=3
API_RETRY_DELAY=5
"""

    output.write_text(env_content)
    click.echo(f"Generated environment file: {output}")
    click.echo("Please edit this file and rename it to .env")


@cli.group()
def db() -> None:
    """データベース管理コマンド."""


@db.command()
def reset() -> None:
    """データベースをリセット（全データ削除）."""
    from .database import DatabaseManager

    click.confirm("本当にデータベースをリセットしますか？", abort=True)

    # データベースファイルを削除
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    if db_path.exists():
        db_path.unlink()
        logger.info(f"Database file deleted: {db_path}")

    # 新しいデータベースを作成
    with DatabaseManager() as db_manager:
        logger.info("New database created")
        stats = db_manager.get_statistics()
        logger.info(f"Database reset complete. Total papers: {stats['total_papers']}")


@db.command()
def stats() -> None:
    """データベースの統計情報を表示."""
    from .database import DatabaseManager

    with DatabaseManager() as db_manager:
        stats = db_manager.get_statistics()

        click.echo("\n[Database Statistics]")
        click.echo(f"Total papers: {stats['total_papers']}")
        click.echo(f"Papers posted to Slack: {stats['slack_posted']}")
        click.echo(f"Papers added to Notion: {stats['notion_added']}")

        if stats["recent_papers"]:
            click.echo("\n[Recent Papers (Last 5)]")
            for paper in stats["recent_papers"][:5]:
                click.echo(f"- {paper.arxiv_id}: {paper.title[:60]}...")
                click.echo(
                    f"  Processed: {paper.processed_at.strftime('%Y-%m-%d %H:%M')}"
                )


@db.command()
@click.option(
    "--days",
    "-d",
    type=int,
    help="何日前のデータを削除するか（デフォルトは設定値）",
)
def cleanup(days: int | None) -> None:
    """古いデータをクリーンアップ."""
    from .database import DatabaseManager

    cleanup_days = days or settings.database_cleanup_days

    with DatabaseManager() as db_manager:
        deleted = db_manager.cleanup_old_records(cleanup_days)
        logger.info(
            f"Cleaned up {deleted} old records (older than {cleanup_days} days)"
        )


@db.command()
@click.argument("arxiv_id")
def remove(arxiv_id: str) -> None:
    """特定の論文をデータベースから削除."""
    from .database import DatabaseManager

    with DatabaseManager() as db_manager:
        # 論文を検索
        from .models import ProcessedPaper

        paper = (
            db_manager.session.query(ProcessedPaper)
            .filter_by(arxiv_id=arxiv_id)
            .first()
        )

        if paper:
            db_manager.session.delete(paper)
            db_manager.session.commit()
            logger.info(f"Removed paper: {arxiv_id}")
        else:
            logger.error(f"Paper not found: {arxiv_id}")


def main() -> None:
    """メイン関数."""
    cli()


if __name__ == "__main__":
    main()
