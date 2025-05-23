"""ロギングモジュールのテスト。

このモジュールは、ロギングモジュール（src.core.logger）のテストを提供します。
"""

import io
import logging
import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.logger import Logger


class TestLogger(unittest.TestCase):
    """Loggerクラスのテスト。"""

    def setUp(self) -> None:
        """テスト前の準備を行います。"""
        # 既存のハンドラをクリア
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_init_default(self) -> None:
        """デフォルト設定で初期化した場合のテスト。"""
        logger = Logger("test")
        self.assertEqual(logger.logger.name, "test")
        self.assertEqual(logger.logger.level, logging.INFO)
        self.assertEqual(len(logger.logger.handlers), 1)
        self.assertIsInstance(logger.logger.handlers[0], logging.StreamHandler)

    def test_init_with_level(self) -> None:
        """ログレベルを指定して初期化した場合のテスト。"""
        logger = Logger("test", level="DEBUG")
        self.assertEqual(logger.logger.level, logging.DEBUG)

        logger = Logger("test", level="WARNING")
        self.assertEqual(logger.logger.level, logging.WARNING)

        logger = Logger("test", level="ERROR")
        self.assertEqual(logger.logger.level, logging.ERROR)

        logger = Logger("test", level="CRITICAL")
        self.assertEqual(logger.logger.level, logging.CRITICAL)

    def test_init_with_invalid_level(self) -> None:
        """不正なログレベルを指定して初期化した場合のテスト。"""
        with self.assertRaises(ValueError):
            Logger("test", level="INVALID")

    def test_init_with_log_file(self) -> None:
        """ログファイルを指定して初期化した場合のテスト。"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger = Logger("test", log_file=temp_file_path)
            self.assertEqual(len(logger.logger.handlers), 2)
            self.assertIsInstance(logger.logger.handlers[0], logging.StreamHandler)
            self.assertIsInstance(
                logger.logger.handlers[1], logging.handlers.RotatingFileHandler
            )
        finally:
            os.unlink(temp_file_path)

    def test_init_with_format(self) -> None:
        """フォーマットを指定して初期化した場合のテスト。"""
        format_string = "%(levelname)s - %(message)s"
        logger = Logger("test", format_string=format_string)
        self.assertEqual(logger.logger.handlers[0].formatter._fmt, format_string)

    def test_debug(self) -> None:
        """debugメソッドのテスト。"""
        with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
            logger = Logger("test", level="DEBUG")
            logger.debug("Debug message")
            self.assertIn("DEBUG", fake_stdout.getvalue())
            self.assertIn("Debug message", fake_stdout.getvalue())

    def test_info(self) -> None:
        """infoメソッドのテスト。"""
        with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
            logger = Logger("test")
            logger.info("Info message")
            self.assertIn("INFO", fake_stdout.getvalue())
            self.assertIn("Info message", fake_stdout.getvalue())

    def test_warning(self) -> None:
        """warningメソッドのテスト。"""
        with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
            logger = Logger("test")
            logger.warning("Warning message")
            self.assertIn("WARNING", fake_stdout.getvalue())
            self.assertIn("Warning message", fake_stdout.getvalue())

    def test_error(self) -> None:
        """errorメソッドのテスト。"""
        with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
            logger = Logger("test")
            logger.error("Error message")
            self.assertIn("ERROR", fake_stdout.getvalue())
            self.assertIn("Error message", fake_stdout.getvalue())

    def test_critical(self) -> None:
        """criticalメソッドのテスト。"""
        with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
            logger = Logger("test")
            logger.critical("Critical message")
            self.assertIn("CRITICAL", fake_stdout.getvalue())
            self.assertIn("Critical message", fake_stdout.getvalue())

    def test_log_level_filtering(self) -> None:
        """ログレベルによるフィルタリングのテスト。"""
        with patch("sys.stdout", new=io.StringIO()) as fake_stdout:
            logger = Logger("test", level="WARNING")
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")

            output = fake_stdout.getvalue()
            self.assertNotIn("Debug message", output)
            self.assertNotIn("Info message", output)
            self.assertIn("Warning message", output)


if __name__ == "__main__":
    unittest.main()
