"""設定管理モジュールのテスト。

このモジュールは、設定管理モジュール（src.core.config）のテストを提供します。
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import yaml

from src.core.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    """ConfigManagerクラスのテスト。"""

    def setUp(self) -> None:
        """テスト前の準備を行います。"""
        self.test_config = {
            "app": {
                "name": "TestApp",
                "version": "1.0.0",
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "user",
                "password": "password",
            },
            "logging": {
                "level": "INFO",
                "file": "/var/log/app.log",
            },
        }

    def test_init_without_config(self) -> None:
        """設定ファイルなしで初期化した場合のテスト。"""
        config_manager = ConfigManager()
        self.assertEqual(config_manager.config, {})

    def test_init_with_json_config(self) -> None:
        """JSON設定ファイルで初期化した場合のテスト。"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            json.dump(self.test_config, temp_file)
            temp_file_path = temp_file.name

        try:
            config_manager = ConfigManager(temp_file_path)
            self.assertEqual(config_manager.config, self.test_config)
        finally:
            os.unlink(temp_file_path)

    def test_init_with_yaml_config(self) -> None:
        """YAML設定ファイルで初期化した場合のテスト。"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            yaml.dump(self.test_config, temp_file)
            temp_file_path = temp_file.name

        try:
            config_manager = ConfigManager(temp_file_path)
            self.assertEqual(config_manager.config, self.test_config)
        finally:
            os.unlink(temp_file_path)

    def test_load_config_file_not_found(self) -> None:
        """存在しない設定ファイルを読み込もうとした場合のテスト。"""
        config_manager = ConfigManager()
        with self.assertRaises(FileNotFoundError):
            config_manager.load_config("/path/to/nonexistent/config.json")

    def test_load_config_invalid_format(self) -> None:
        """サポートされていない形式の設定ファイルを読み込もうとした場合のテスト。"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is not a valid config file")
            temp_file_path = temp_file.name

        try:
            config_manager = ConfigManager()
            with self.assertRaises(ValueError):
                config_manager.load_config(temp_file_path)
        finally:
            os.unlink(temp_file_path)

    def test_get_existing_key(self) -> None:
        """存在するキーの値を取得するテスト。"""
        config_manager = ConfigManager()
        config_manager.config = self.test_config
        self.assertEqual(config_manager.get("app.name"), "TestApp")
        self.assertEqual(config_manager.get("database.port"), 5432)
        self.assertEqual(config_manager.get("logging.level"), "INFO")

    def test_get_nonexistent_key(self) -> None:
        """存在しないキーの値を取得するテスト。"""
        config_manager = ConfigManager()
        config_manager.config = self.test_config
        self.assertIsNone(config_manager.get("nonexistent.key"))
        self.assertEqual(config_manager.get("nonexistent.key", "default"), "default")

    def test_get_from_environment(self) -> None:
        """環境変数から値を取得するテスト。"""
        config_manager = ConfigManager()
        config_manager.config = self.test_config

        with patch.dict(os.environ, {"APP_DATABASE_HOST": "env-host"}):
            self.assertEqual(config_manager.get("database.host"), "env-host")

    def test_set_new_key(self) -> None:
        """新しいキーに値を設定するテスト。"""
        config_manager = ConfigManager()
        config_manager.set("new.key", "value")
        self.assertEqual(config_manager.get("new.key"), "value")

    def test_set_existing_key(self) -> None:
        """既存のキーの値を更新するテスト。"""
        config_manager = ConfigManager()
        config_manager.config = self.test_config
        config_manager.set("app.name", "NewName")
        self.assertEqual(config_manager.get("app.name"), "NewName")

    def test_set_nested_key(self) -> None:
        """ネストされたキーに値を設定するテスト。"""
        config_manager = ConfigManager()
        config_manager.set("a.b.c.d", "value")
        self.assertEqual(config_manager.get("a.b.c.d"), "value")


if __name__ == "__main__":
    unittest.main()
