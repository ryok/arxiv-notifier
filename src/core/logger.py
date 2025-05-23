"""ロギングモジュール。

このモジュールは、アプリケーションのロギング機能を提供します。
複数レベルのログ出力、ファイル出力とコンソール出力、
およびログフォーマットのカスタマイズをサポートします。
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """ロギングを管理するクラス。

    このクラスは、複数レベルのログ出力、ファイル出力とコンソール出力、
    およびログフォーマットのカスタマイズを行います。

    Attributes:
        logger: ロギングインスタンス
    """

    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        format_string: Optional[str] = None,
    ) -> None:
        """Loggerを初期化します。

        Args:
            name: ロガー名
            level: ログレベル（"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"）
            log_file: ログファイルのパス。指定された場合は、ファイルにもログを出力します。
            max_bytes: ログファイルの最大サイズ（バイト）
            backup_count: 保持するバックアップファイルの数
            format_string: ログフォーマット文字列。指定されない場合はデフォルトフォーマットを使用します。
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_log_level(level))
        self.logger.handlers = []  # 既存のハンドラをクリア

        # フォーマットの設定
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_string)

        # コンソールハンドラの設定
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # ファイルハンドラの設定（指定された場合）
        if log_file:
            # ディレクトリが存在しない場合は作成
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _get_log_level(self, level: str) -> int:
        """文字列のログレベルを数値に変換します。

        Args:
            level: ログレベル文字列

        Returns:
            ログレベル数値

        Raises:
            ValueError: 不正なログレベルが指定された場合
        """
        level_upper = level.upper()
        if level_upper == "DEBUG":
            return logging.DEBUG
        elif level_upper == "INFO":
            return logging.INFO
        elif level_upper == "WARNING":
            return logging.WARNING
        elif level_upper == "ERROR":
            return logging.ERROR
        elif level_upper == "CRITICAL":
            return logging.CRITICAL
        else:
            raise ValueError(f"不正なログレベルです: {level}")

    def debug(self, message: str) -> None:
        """DEBUGレベルのログを出力します。

        Args:
            message: ログメッセージ
        """
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """INFOレベルのログを出力します。

        Args:
            message: ログメッセージ
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """WARNINGレベルのログを出力します。

        Args:
            message: ログメッセージ
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """ERRORレベルのログを出力します。

        Args:
            message: ログメッセージ
        """
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """CRITICALレベルのログを出力します。

        Args:
            message: ログメッセージ
        """
        self.logger.critical(message)
