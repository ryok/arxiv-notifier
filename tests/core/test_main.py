"""メインモジュールのテスト。

このモジュールは、メインモジュール（src.core.main）のテストを提供します。
"""

import unittest
from unittest.mock import MagicMock, patch

from src.core.main import Application, main


class TestApplication(unittest.TestCase):
    """Applicationクラスのテスト。"""

    @patch("src.core.main.ConfigManager")
    @patch("src.core.main.Logger")
    def test_init(self, mock_logger, mock_config_manager) -> None:
        """初期化のテスト。"""
        # モックの設定
        mock_config_instance = mock_config_manager.return_value
        mock_config_instance.get.return_value = "/path/to/log.file"
        mock_logger_instance = mock_logger.return_value

        # テスト対象の実行
        app = Application(config_path="/path/to/config.json", log_level="DEBUG")

        # 検証
        mock_config_manager.assert_called_once_with("/path/to/config.json")
        mock_config_instance.get.assert_called_once_with("logging.file")
        mock_logger.assert_called_once_with(
            name="app", level="DEBUG", log_file="/path/to/log.file"
        )
        mock_logger_instance.info.assert_called_once_with(
            "アプリケーションを初期化しました"
        )

    @patch("src.core.main.ConfigManager")
    @patch("src.core.main.Logger")
    def test_run(self, mock_logger, mock_config_manager) -> None:
        """runメソッドのテスト。"""
        # モックの設定
        mock_logger_instance = mock_logger.return_value

        # テスト対象の実行
        app = Application()
        app._process = MagicMock()  # _processメソッドをモック化
        app.run()

        # 検証
        mock_logger_instance.info.assert_any_call("アプリケーションを実行します")
        app._process.assert_called_once()
        mock_logger_instance.info.assert_any_call(
            "アプリケーションの実行が完了しました"
        )

    @patch("src.core.main.ConfigManager")
    @patch("src.core.main.Logger")
    def test_run_with_exception(self, mock_logger, mock_config_manager) -> None:
        """例外発生時のrunメソッドのテスト。"""
        # モックの設定
        mock_logger_instance = mock_logger.return_value

        # テスト対象の実行
        app = Application()
        app._process = MagicMock(
            side_effect=ValueError("テストエラー")
        )  # 例外を発生させる

        # 例外が再送出されることを確認
        with self.assertRaises(ValueError):
            app.run()

        # 検証
        mock_logger_instance.error.assert_called_once_with(
            "アプリケーションの実行中にエラーが発生しました: テストエラー"
        )

    @patch("src.core.main.ConfigManager")
    @patch("src.core.main.Logger")
    def test_process(self, mock_logger, mock_config_manager) -> None:
        """_processメソッドのテスト。"""
        # モックの設定
        mock_logger_instance = mock_logger.return_value

        # テスト対象の実行
        app = Application()
        app._process()

        # 検証
        mock_logger_instance.info.assert_any_call("内部処理を実行します")


class TestMain(unittest.TestCase):
    """mainメソッドのテスト。"""

    @patch("src.core.main.Application")
    def test_main(self, mock_application) -> None:
        """mainメソッドのテスト。"""
        # モックの設定
        mock_app_instance = mock_application.return_value

        # テスト対象の実行
        main()

        # 検証
        mock_application.assert_called_once_with()
        mock_app_instance.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
