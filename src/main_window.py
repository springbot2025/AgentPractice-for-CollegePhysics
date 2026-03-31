# -*- coding: utf-8 -*-
"""Main window for the API chat client."""

import json
import os
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from config.settings import (
    COLORS,
    DEFAULT_API_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    FONT_FAMILY_UI,
    WINDOW_HEIGHT,
    WINDOW_POS_X,
    WINDOW_POS_Y,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    MODELS,
    get_models_for_api,
)


CONFIG_DIR = os.path.expanduser("~/.api_client")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


class MessageBubble(QFrame):
    """Single message card in the chat area."""

    def __init__(self, role, content, timestamp):
        super().__init__()
        self.role = role
        self._setup_ui(content, timestamp)

    def _setup_ui(self, content, timestamp):
        c = COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        name = "Assistant" if self.role == "assistant" else "You"
        color = c["accent_primary"] if self.role == "assistant" else c["accent_purple"]
        role_label = QLabel(name)
        role_label.setStyleSheet(f"font-weight: bold; color: {color};")
        header.addWidget(role_label)
        header.addStretch()
        time_label = QLabel(timestamp)
        time_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px;")
        header.addWidget(time_label)
        layout.addLayout(header)

        body = QLabel(content)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        body.setStyleSheet(f"color: {c['text_primary']}; font-size: 13px;")
        layout.addWidget(body)

        if self.role == "assistant":
            self.setStyleSheet(
                f"QFrame {{ background: {c['bg_primary']}; border-radius: 12px; "
                f"border-left: 3px solid {c['accent_primary']}; }}"
            )
        else:
            self.setStyleSheet(
                f"QFrame {{ background: {c['bg_surface']}; border-radius: 12px; "
                f"border-right: 3px solid {c['accent_purple']}; }}"
            )


class ChatWidget(QWidget):
    """Scrollable chat message list."""

    def __init__(self):
        super().__init__()
        self.messages = []
        self.thinking_label = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setSpacing(10)
        self.container_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def _scroll_to_bottom(self):
        QTimer.singleShot(
            30,
            lambda: self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().maximum()
            ),
        )

    def add_message(self, role, content):
        self.remove_thinking()
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.append((role, content, timestamp))
        self.container_layout.addWidget(MessageBubble(role, content, timestamp))
        self._scroll_to_bottom()

    def add_thinking(self):
        self.remove_thinking()
        self.thinking_label = QLabel("正在思考中...")
        self.thinking_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-style: italic; padding: 8px;"
        )
        self.container_layout.addWidget(self.thinking_label)
        self._scroll_to_bottom()

    def remove_thinking(self):
        if self.thinking_label is not None:
            self.container_layout.removeWidget(self.thinking_label)
            self.thinking_label.deleteLater()
            self.thinking_label = None

    def clear(self):
        self.messages.clear()
        self.thinking_label = None
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_thread = None
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(WINDOW_POS_X, WINDOW_POS_Y, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(960, 640)
        self._apply_styles()
        self.create_menu()

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        chat_area = self.create_chat_area()
        main_layout.addWidget(chat_area, 1)

        self.statusBar().showMessage("就绪")
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.send_message)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.send_message)

    def _apply_styles(self):
        c = COLORS
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {c['bg_primary']};
            }}
            QLabel {{
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit, QComboBox, QTextEdit {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 8px 10px;
                font-family: {FONT_FAMILY_UI};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {c['accent_primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {c['bg_surface']};
                color: {c['text_secondary']};
            }}
            QGroupBox {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 12px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                left: 10px;
                padding: 0 6px;
                color: {c['accent_primary']};
            }}
            """
        )

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        new_action = QAction("新建对话", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_chat)
        file_menu.addAction(new_action)

        export_action = QAction("导出对话", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_chat)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("设置")
        save_action = QAction("保存配置", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_settings)
        settings_menu.addAction(save_action)

        view_action = QAction("查看配置", self)
        view_action.triggered.connect(self.view_settings)
        settings_menu.addAction(view_action)

        clear_action = QAction("清除配置", self)
        clear_action.triggered.connect(self.clear_settings)
        settings_menu.addAction(clear_action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_sidebar(self):
        box = QGroupBox("配置")
        box.setFixedWidth(300)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel("API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.api_key_input)

        layout.addWidget(QLabel("API URL"))
        self.api_url_combo = QComboBox()
        self.api_url_combo.setEditable(True)
        self.api_url_combo.addItems(
            [
                "https://api.anthropic.com/v1/messages",
                "https://api.openai.com/v1/chat/completions",
                "https://api.ecxwxz.top/v1/messages",
                "https://api.ecxwxz.top/v1/chat/completions",
            ]
        )
        self.api_url_combo.currentTextChanged.connect(self._update_models)
        layout.addWidget(self.api_url_combo)

        layout.addWidget(QLabel("模型"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        layout.addWidget(self.model_combo)

        layout.addWidget(QLabel("温度 (Temperature)"))
        self.temp_input = QLineEdit(str(DEFAULT_TEMPERATURE))
        layout.addWidget(self.temp_input)

        layout.addWidget(QLabel("Max Tokens"))
        self.max_tokens_input = QLineEdit(str(DEFAULT_MAX_TOKENS))
        layout.addWidget(self.max_tokens_input)

        layout.addStretch()

        self.send_btn = QPushButton("发送消息")
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)

        self._update_models()
        return box

    def create_chat_area(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget, 1)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入消息... (Ctrl+Enter 发送)")
        self.input_box.setMinimumHeight(120)
        self.input_box.setMaximumHeight(220)
        layout.addWidget(self.input_box)

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("清空对话")
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: {COLORS['bg_surface']}; color: {COLORS['text_primary']}; }}"
        )
        clear_btn.clicked.connect(self.new_chat)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()

        self.send_btn_main = QPushButton("发送")
        self.send_btn_main.clicked.connect(self.send_message)
        btn_row.addWidget(self.send_btn_main)
        layout.addLayout(btn_row)

        return frame

    def _normalize_api_url(self):
        api_url = self.api_url_combo.currentText().strip()
        if api_url and not api_url.startswith(("http://", "https://")):
            api_url = f"https://{api_url}"
            self.api_url_combo.setCurrentText(api_url)
        return api_url

    def send_message(self):
        content = self.input_box.toPlainText().strip()
        if not content:
            return

        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请输入 API Key")
            return

        api_url = self._normalize_api_url()
        if not api_url:
            QMessageBox.warning(self, "提示", "请输入 API URL")
            return

        self.chat_widget.add_message("user", content)
        self.input_box.clear()
        messages = [{"role": role, "content": msg} for role, msg, _ in self.chat_widget.messages]

        try:
            temperature = float(self.temp_input.text().strip())
        except Exception:
            temperature = DEFAULT_TEMPERATURE
            self.temp_input.setText(str(DEFAULT_TEMPERATURE))

        try:
            max_tokens = int(self.max_tokens_input.text().strip())
        except Exception:
            max_tokens = DEFAULT_MAX_TOKENS
            self.max_tokens_input.setText(str(DEFAULT_MAX_TOKENS))

        model = self.model_combo.currentText().strip() or DEFAULT_MODEL
        self.chat_widget.add_thinking()
        self.send_btn.setEnabled(False)
        self.send_btn_main.setEnabled(False)
        self.statusBar().showMessage("正在发送请求...")

        from utils.api_client import ApiClientThread

        self.api_thread = ApiClientThread(
            api_key=api_key,
            base_url=api_url,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        self.api_thread.finished.connect(self.on_response)
        self.api_thread.error.connect(self.on_error)
        self.api_thread.finished.connect(lambda: self.api_thread.deleteLater())
        self.api_thread.start()

    def on_response(self, result):
        self.send_btn.setEnabled(True)
        self.send_btn_main.setEnabled(True)
        self.statusBar().showMessage(f"请求完成 - {result.get('time', '0ms')}")
        content = result.get("content", "")
        if not content:
            content = "接口返回为空内容，请检查服务端响应格式。"
        self.chat_widget.add_message("assistant", content)

    def on_error(self, error):
        self.chat_widget.remove_thinking()
        self.send_btn.setEnabled(True)
        self.send_btn_main.setEnabled(True)
        self.statusBar().showMessage("请求失败")
        QMessageBox.critical(self, "错误", str(error))

    def new_chat(self):
        self.chat_widget.clear()
        self.statusBar().showMessage("已新建对话")

    def export_chat(self):
        if not self.chat_widget.messages:
            QMessageBox.information(self, "提示", "没有可导出的对话")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出对话", "", "JSON Files (*.json);;Text Files (*.txt)"
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            if file_path.endswith(".json"):
                payload = [
                    {"role": role, "content": content, "time": time}
                    for role, content, time in self.chat_widget.messages
                ]
                json.dump(payload, f, ensure_ascii=False, indent=2)
            else:
                for role, content, time in self.chat_widget.messages:
                    f.write(f"[{time}] {role}: {content}\n\n")

        self.statusBar().showMessage(f"已导出到 {file_path}")

    def save_settings(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        payload = {
            "api_key": self.api_key_input.text().strip(),
            "api_url": self._normalize_api_url(),
            "model": self.model_combo.currentText().strip(),
            "temperature": self.temp_input.text().strip(),
            "max_tokens": self.max_tokens_input.text().strip(),
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        self.statusBar().showMessage("配置已保存")

    def view_settings(self):
        if not os.path.exists(CONFIG_FILE):
            QMessageBox.information(self, "配置", "暂无已保存配置")
            return

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("api_key"):
            key = data["api_key"]
            data["api_key"] = key[:4] + "*" * max(0, len(key) - 8) + key[-4:]
        QMessageBox.information(self, "当前配置", json.dumps(data, ensure_ascii=False, indent=2))

    def load_settings(self):
        self._update_models()
        if not os.path.exists(CONFIG_FILE):
            self.api_url_combo.setCurrentText(DEFAULT_API_URL)
            self.model_combo.setCurrentText(DEFAULT_MODEL)
            return

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.api_key_input.setText(data.get("api_key", ""))
        self.api_url_combo.setCurrentText(data.get("api_url", DEFAULT_API_URL))
        self._update_models()
        self.model_combo.setCurrentText(data.get("model", DEFAULT_MODEL))
        self.temp_input.setText(str(data.get("temperature", DEFAULT_TEMPERATURE)))
        self.max_tokens_input.setText(str(data.get("max_tokens", DEFAULT_MAX_TOKENS)))

    def clear_settings_fields(self):
        self.api_key_input.clear()
        self.api_url_combo.setCurrentText(DEFAULT_API_URL)
        self._update_models()
        self.model_combo.setCurrentText(DEFAULT_MODEL)
        self.temp_input.setText(str(DEFAULT_TEMPERATURE))
        self.max_tokens_input.setText(str(DEFAULT_MAX_TOKENS))

    def clear_settings(self):
        if os.path.exists(CONFIG_FILE):
            reply = QMessageBox.question(self, "确认", "确定要清除本地配置吗？")
            if reply != QMessageBox.Yes:
                return
            os.remove(CONFIG_FILE)
        self.clear_settings_fields()
        self.statusBar().showMessage("配置已清除")

    def _update_models(self):
        api_url = self.api_url_combo.currentText().strip()
        model_list = get_models_for_api(api_url) if api_url else MODELS
        current = self.model_combo.currentText().strip()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItems(model_list)
        if current:
            self.model_combo.setCurrentText(current)
        self.model_combo.blockSignals(False)

    def show_about(self):
        QMessageBox.about(
            self,
            "关于 API Client",
            (
                "<h3>API Client</h3>"
                "<p>一个简洁的 API 聊天调用工具。</p>"
                "<p>支持 Anthropic 与 OpenAI 兼容格式。</p>"
            ),
        )
