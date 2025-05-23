"""アプリケーションのメインモジュール。

このモジュールは、アプリケーションのメインロジックを提供します。
他のモジュールを統合し、アプリケーションの実行フローを制御します。
"""

from typing import Optional

from src.core.config import ConfigManager
from src.core.logger import Logger


class Application:
    """アプリケーションのメインクラス。

    このクラスは、アプリケーションのメインロジックを実装し、
    他のモジュールを統合します。

    Attributes:
        config: 設定マネージャ
        logger: ロガー
    """

    def __init__(
        self, config_path: Optional[str] = None, log_level: str = "INFO"
    ) -> None:
        """Applicationを初期化します。

        Args:
            config_path: 設定ファイルのパス。指定された場合は、初期化時に読み込みます。
            log_level: ログレベル
        """
        # 設定の初期化
        self.config = ConfigManager(config_path)

        # ロガーの初期化
        log_file = self.config.get("logging.file")
        self.logger = Logger(
            name="app",
            level=log_level,
            log_file=log_file,
        )
        self.logger.info("アプリケーションを初期化しました")

    def run(self) -> None:
        """アプリケーションを実行します。

        このメソッドは、アプリケーションのメインロジックを実行します。
        """
        self.logger.info("アプリケーションを実行します")
        try:
            # ここにアプリケーションのメインロジックを実装
            self._process()
            self.logger.info("アプリケーションの実行が完了しました")
        except Exception as e:
            self.logger.error(f"アプリケーションの実行中にエラーが発生しました: {e}")
            raise

    def _process(self) -> None:
        """内部処理を実行します。

        このメソッドは、アプリケーションの内部処理を実行します。
        サブクラスでオーバーライドして、具体的な処理を実装することを想定しています。
        """
        self.logger.info("内部処理を実行します")
        # ここにアプリケーション固有の処理を実装
        # 例: データの処理、外部APIの呼び出し、計算の実行など
        pass


def main() -> None:
    """アプリケーションのエントリーポイント。

    このメソッドは、アプリケーションのエントリーポイントとして機能します。
    コマンドラインから直接実行された場合に呼び出されます。
    """
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
