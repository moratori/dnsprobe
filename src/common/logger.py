#!/usr/bin/env python3

"""
ロガーのセットアップを行う
"""

import common.config as config
import os
from logging import StreamHandler, basicConfig, getLogger
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG
from logging.handlers import TimedRotatingFileHandler


def setup_logger(module_name, file_path, loglevel, rotation_timing, bkcount):

    """
    logger を初期化し返却する
    本処理は、トップレベルのスクリプトから実行されることを想定している
    """

    loglevel_table = {"CRITICAL": CRITICAL,
                      "ERROR": ERROR,
                      "WARNING": WARNING,
                      "INFO": INFO,
                      "DEBUG": DEBUG}

    rotation_timing_table = set(["S", "M", "H", "D"])

    if loglevel not in loglevel_table:
        loglevel = INFO
    else:
        loglevel = loglevel_table[loglevel]

    if rotation_timing not in rotation_timing_table:
        rotation_timing = "D"
    else:
        rotation_timing = rotation_timing

    if file_path is None:
        handler = StreamHandler()
    else:
        log_file_name = os.path.basename(file_path).replace(".py", ".log")
        handler = TimedRotatingFileHandler(
            filename=os.path.join(config.LOGS_DIR, log_file_name),
            when=rotation_timing,
            backupCount=int(bkcount))

    fmt_str = "%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s"
    basicConfig(format=fmt_str, level=loglevel, handlers=[handler])
    logger = getLogger(module_name)

    return logger
