"""設定管理モジュール。

このモジュールは、アプリケーションの設定を管理するための機能を提供します。
YAML/JSON形式の設定ファイルの読み込み、環境変数からの設定値取得、
およびデフォルト設定の提供をサポートします。
"""

import json
import os
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """設定を管理するクラス。

    このクラスは、設定ファイルの読み込み、環境変数からの設定値取得、
    およびデフォルト設定の提供を行います。

    Attributes:
        config: 設定値を格納する辞書
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """ConfigManagerを初期化します。

        Args:
            config_path: 設定ファイルのパス。指定された場合は、初期化時に読み込みます。
        """
        self.config: Dict[str, Any] = {}
        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """設定ファイルを読み込みます。

        Args:
            config_path: 設定ファイルのパス。

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合。
            ValueError: 設定ファイルの形式が不正な場合。
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

        file_ext = os.path.splitext(config_path)[1].lower()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if file_ext == ".json":
                    self.config = json.load(f)
                elif file_ext in (".yaml", ".yml"):
                    self.config = yaml.safe_load(f)
                else:
                    raise ValueError(
                        f"サポートされていないファイル形式です: {file_ext}"
                    )
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"設定ファイルの解析に失敗しました: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得します。

        環境変数に同名のキーが存在する場合は、環境変数の値を優先します。
        環境変数名は "APP_" プレフィックスの後に、キーを大文字にしたものです。
        例: "database.host" -> "APP_DATABASE_HOST"

        Args:
            key: 設定キー。ドットで区切られた階層構造をサポートします。
            default: キーが存在しない場合のデフォルト値。

        Returns:
            設定値。キーが存在しない場合はデフォルト値。
        """
        # 環境変数から取得を試みる
        env_key = "APP_" + key.upper().replace(".", "_")
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value

        # 設定から取得
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """設定値を設定します。

        Args:
            key: 設定キー。ドットで区切られた階層構造をサポートします。
            value: 設定値。
        """
        keys = key.split(".")
        config = self.config
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                # 途中のキーが辞書でない場合は、辞書に置き換える
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
