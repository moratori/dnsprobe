#!/usr/bin/env python3

"""
プロジェクトに必要な定数を定義する
"""

import os

if __name__ != "__main__":

    PROJECT_ROOT = \
        os.path.dirname(os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../")))

    TMP_DIR = os.path.join("/tmp", os.path.basename(PROJECT_ROOT))
    LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
    STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
    TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")
    CONFIG_DIR = os.path.join(PROJECT_ROOT, "conf")
