# -*- coding: utf-8 -*-
"""语法高亮器"""

from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re


class JsonHighlighter(QSyntaxHighlighter):
    """JSON 语法高亮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 字符串 - 绿色
        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#98c379"))
        self.highlighting_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_fmt))

        # 数字 - 橙色
        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#d19a66"))
        self.highlighting_rules.append((r'\b[0-9]+\.?[0-9]*\b', number_fmt))

        # 布尔值和 null - 青色
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#56b6c2"))
        self.highlighting_rules.append((r'\b(true|false|null)\b', keyword_fmt))

        # 键名 - 红色
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#e06c75"))
        self.highlighting_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"(?=\s*:)', key_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown 简易高亮"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 代码块
        self.code_fmt = QTextCharFormat()
        self.code_fmt.setForeground(QColor("#98c379"))
        self.code_fmt.setFontFamily("Consolas")

        # 引用
        self.quote_fmt = QTextCharFormat()
        self.quote_fmt.setForeground(QColor("#6c7086"))

        # 粗体
        self.bold_fmt = QTextCharFormat()
        self.bold_fmt.setFontWeight(QFont.Bold)
        self.bold_fmt.setForeground(QColor("#cba6f7"))

        # 链接
        self.link_fmt = QTextCharFormat()
        self.link_fmt.setForeground(QColor("#89b4fa"))
        self.link_fmt.setFontUnderline(True)

    def highlightBlock(self, text):
        # 代码块 ```
        if text.strip().startswith('```'):
            self.setFormat(0, len(text), self.code_fmt)

        # 行内代码 `
        for match in re.finditer(r'`[^`]+`', text):
            self.setFormat(match.start(), match.end() - match.start(), self.code_fmt)

        # 引用 >
        if text.strip().startswith('>'):
            self.setFormat(0, len(text), self.quote_fmt)

        # 粗体 **
        for match in re.finditer(r'\*\*[^*]+\*\*', text):
            self.setFormat(match.start(), match.end() - match.start(), self.bold_fmt)
