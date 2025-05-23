"""コマンドラインインターフェースモジュール。

このモジュールは、アプリケーションのコマンドラインインターフェースを提供します。
argparseを使用したコマンドライン引数の処理、サブコマンドのサポート、
およびヘルプメッセージの提供を行います。
"""

import argparse
import sys
from typing import List, Optional

from src.core.main import Application


class CLI:
    """コマンドラインインターフェースを提供するクラス。

    このクラスは、コマンドライン引数の解析と、対応するアプリケーション機能の
    呼び出しを行います。

    Attributes:
        parser: 引数パーサー
    """

    def __init__(self) -> None:
        """CLIを初期化します。"""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """引数パーサーを作成します。

        Returns:
            作成された引数パーサー
        """
        parser = argparse.ArgumentParser(
            description="Pythonボイラープレートアプリケーション",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        # グローバルオプション
        parser.add_argument(
            "-c",
            "--config",
            help="設定ファイルのパス",
            default=None,
        )
        parser.add_argument(
            "-l",
            "--log-level",
            help="ログレベル",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
        )
        parser.add_argument(
            "-v", "--version", action="store_true", help="バージョン情報を表示して終了"
        )

        # サブコマンド
        subparsers = parser.add_subparsers(
            dest="command", help="実行するコマンド", required=False
        )

        # runコマンド
        run_parser = subparsers.add_parser("run", help="アプリケーションを実行")
        run_parser.add_argument(
            "--option", help="オプション引数の例", default="default_value"
        )

        # initコマンド
        init_parser = subparsers.add_parser("init", help="アプリケーションを初期化")
        init_parser.add_argument(
            "--force", action="store_true", help="既存の設定を上書き"
        )

        return parser

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """コマンドライン引数を解析します。

        Args:
            args: コマンドライン引数のリスト。指定されない場合は sys.argv[1:] を使用。

        Returns:
            解析された引数
        """
        return self.parser.parse_args(args)

    def run(self, args: Optional[List[str]] = None) -> int:
        """CLIを実行します。

        Args:
            args: コマンドライン引数のリスト。指定されない場合は sys.argv[1:] を使用。

        Returns:
            終了コード。0は成功、それ以外は失敗。
        """
        parsed_args = self.parse_args(args)

        # バージョン情報の表示
        if parsed_args.version:
            from src import __version__

            print(f"Python Boilerplate v{__version__}")
            return 0

        # コマンドの実行
        try:
            if parsed_args.command == "run":
                app = Application(
                    config_path=parsed_args.config, log_level=parsed_args.log_level
                )
                app.run()
            elif parsed_args.command == "init":
                self._init_command(parsed_args)
            else:
                # デフォルトはrunコマンドと同じ
                app = Application(
                    config_path=parsed_args.config, log_level=parsed_args.log_level
                )
                app.run()
            return 0
        except Exception as e:
            print(f"エラー: {e}", file=sys.stderr)
            return 1

    def _init_command(self, args: argparse.Namespace) -> None:
        """initコマンドを実行します。

        Args:
            args: 解析された引数
        """
        print("アプリケーションを初期化しています...")
        # ここに初期化処理を実装
        # 例: 設定ファイルの作成、ディレクトリ構造の作成など
        print("初期化が完了しました。")


def main() -> int:
    """CLIのエントリーポイント。

    このメソッドは、CLIのエントリーポイントとして機能します。
    コマンドラインから直接実行された場合に呼び出されます。

    Returns:
        終了コード。0は成功、それ以外は失敗。
    """
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
