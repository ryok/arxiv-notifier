"""CLIモジュールのテスト。

このモジュールは、CLIモジュール（src.cli）のテストを提供します。
"""

import sys
import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch

from src.cli import CLI, main


class TestCLI(unittest.TestCase):
    """CLIクラスのテスト。"""

    def setUp(self) -> None:
        """テスト前の準備を行います。"""
        self.cli = CLI()

    def test_create_parser(self) -> None:
        """_create_parserメソッドのテスト。"""
        parser = self.cli._create_parser()
        self.assertEqual(parser.description, "Pythonボイラープレートアプリケーション")

    def test_parse_args_default(self) -> None:
        """デフォルト引数でparse_argsメソッドのテスト。"""
        args = self.cli.parse_args([])
        self.assertIsNone(args.config)
        self.assertEqual(args.log_level, "INFO")
        self.assertFalse(args.version)
        self.assertIsNone(args.command)

    def test_parse_args_with_config(self) -> None:
        """設定ファイルを指定してparse_argsメソッドのテスト。"""
        args = self.cli.parse_args(["-c", "config.json"])
        self.assertEqual(args.config, "config.json")

    def test_parse_args_with_log_level(self) -> None:
        """ログレベルを指定してparse_argsメソッドのテスト。"""
        args = self.cli.parse_args(["-l", "DEBUG"])
        self.assertEqual(args.log_level, "DEBUG")

    def test_parse_args_with_version(self) -> None:
        """バージョン表示オプションを指定してparse_argsメソッドのテスト。"""
        args = self.cli.parse_args(["-v"])
        self.assertTrue(args.version)

    def test_parse_args_with_run_command(self) -> None:
        """runコマンドを指定してparse_argsメソッドのテスト。"""
        args = self.cli.parse_args(["run", "--option", "value"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.option, "value")

    def test_parse_args_with_init_command(self) -> None:
        """initコマンドを指定してparse_argsメソッドのテスト。"""
        args = self.cli.parse_args(["init", "--force"])
        self.assertEqual(args.command, "init")
        self.assertTrue(args.force)

    @patch("src.cli.Application")
    def test_run_default(self, mock_application) -> None:
        """デフォルト引数でrunメソッドのテスト。"""
        # モックの設定
        mock_app_instance = mock_application.return_value

        # テスト対象の実行
        result = self.cli.run([])

        # 検証
        self.assertEqual(result, 0)
        mock_application.assert_called_once_with(config_path=None, log_level="INFO")
        mock_app_instance.run.assert_called_once()

    @patch("src.cli.print")
    @patch("src.__version__", "0.1.0")
    def test_run_with_version(self, mock_print) -> None:
        """バージョン表示オプションを指定してrunメソッドのテスト。"""
        # テスト対象の実行
        result = self.cli.run(["-v"])

        # 検証
        self.assertEqual(result, 0)
        mock_print.assert_called_once_with("Python Boilerplate v0.1.0")

    @patch("src.cli.Application")
    def test_run_with_run_command(self, mock_application) -> None:
        """runコマンドを指定してrunメソッドのテスト。"""
        # モックの設定
        mock_app_instance = mock_application.return_value

        # テスト対象の実行
        result = self.cli.run(["run", "--option", "value"])

        # 検証
        self.assertEqual(result, 0)
        mock_application.assert_called_once_with(config_path=None, log_level="INFO")
        mock_app_instance.run.assert_called_once()

    @patch("src.cli.CLI._init_command")
    def test_run_with_init_command(self, mock_init_command) -> None:
        """initコマンドを指定してrunメソッドのテスト。"""
        # テスト対象の実行
        result = self.cli.run(["init", "--force"])

        # 検証
        self.assertEqual(result, 0)
        mock_init_command.assert_called_once()
        args = mock_init_command.call_args[0][0]
        self.assertEqual(args.command, "init")
        self.assertTrue(args.force)

    @patch("src.cli.print")
    def test_run_with_exception(self, mock_print) -> None:
        """例外発生時のrunメソッドのテスト。"""
        # モックの設定
        self.cli.parse_args = MagicMock(side_effect=ValueError("テストエラー"))

        # テスト対象の実行
        result = self.cli.run([])

        # 検証
        self.assertEqual(result, 1)
        mock_print.assert_called_once_with("エラー: テストエラー", file=sys.stderr)

    @patch("src.cli.print")
    def test_init_command(self, mock_print) -> None:
        """_init_commandメソッドのテスト。"""
        # テスト対象の実行
        args = Namespace(force=True)
        self.cli._init_command(args)

        # 検証
        mock_print.assert_any_call("アプリケーションを初期化しています...")
        mock_print.assert_any_call("初期化が完了しました。")


class TestMain(unittest.TestCase):
    """mainメソッドのテスト。"""

    @patch("src.cli.CLI")
    @patch("sys.exit")
    def test_main(self, mock_exit, mock_cli) -> None:
        """mainメソッドのテスト。"""
        # モックの設定
        mock_cli_instance = mock_cli.return_value
        mock_cli_instance.run.return_value = 42

        # テスト対象の実行
        main()

        # 検証
        mock_cli.assert_called_once_with()
        mock_cli_instance.run.assert_called_once_with()
        mock_exit.assert_called_once_with(42)


if __name__ == "__main__":
    unittest.main()
