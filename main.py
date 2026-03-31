#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Client - 启动入口
清新浅色主题 API 调用工具
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

from config.settings import (
    FONT_FAMILY, FONT_SIZE, FONT_FAMILY_UI,
    COLORS, WINDOW_TITLE
)
from src.main_window import MainWindow


def main():
    # 启用高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)

    # 设置全局字体
    app.setFont(QFont(FONT_FAMILY_UI, FONT_SIZE))

    # 设置调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.WindowText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Base, QColor(COLORS['bg_secondary']))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Button, QColor(COLORS['bg_secondary']))
    palette.setColor(QPalette.ButtonText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Highlight, QColor(COLORS['accent_primary']))
    palette.setColor(QPalette.HighlightedText, QColor('white'))
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
