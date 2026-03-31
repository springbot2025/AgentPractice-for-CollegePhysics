# -*- coding: utf-8 -*-
"""API client thread for chat completion calls."""

import json
import time

import requests
from PyQt5.QtCore import QThread, pyqtSignal


class ApiClientThread(QThread):
    """Send API request in a background thread and emit parsed result."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api_key, base_url, model, messages, max_tokens, temperature):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.messages = messages
        self.max_tokens = max_tokens
        self.temperature = temperature

    @staticmethod
    def _fix_mojibake(text):
        """Best-effort fix for UTF-8 text decoded as latin1-like gibberish."""
        if not isinstance(text, str) or not text:
            return text

        # Typical mojibake markers, e.g. "ä½ å¥½".
        if any(ch in text for ch in ("ä", "å", "æ", "ç", "è", "é")):
            try:
                fixed = text.encode("latin1").decode("utf-8")
                if any("\u4e00" <= ch <= "\u9fff" for ch in fixed):
                    return fixed
            except Exception:
                pass
        return text

    @staticmethod
    def _to_text(value):
        """Convert common response payloads to plain text."""
        if value is None:
            return ""

        if isinstance(value, str):
            return ApiClientThread._fix_mojibake(value).strip()

        if isinstance(value, list):
            parts = []
            for item in value:
                text = ApiClientThread._to_text(item)
                if text:
                    parts.append(text)
            return "\n".join(parts).strip()

        if isinstance(value, dict):
            for key in ("text", "content", "output_text", "reasoning_content"):
                if key in value:
                    text = ApiClientThread._to_text(value.get(key))
                    if text:
                        return text

            for key in ("message", "delta"):
                if key in value:
                    text = ApiClientThread._to_text(value.get(key))
                    if text:
                        return text

        return ""

    @classmethod
    def _extract_content(cls, data):
        """Extract assistant content from heterogeneous API response formats."""
        if not isinstance(data, dict):
            return ""

        content = cls._to_text(data.get("content"))
        if content:
            return content

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            content = cls._to_text(choices[0])
            if content:
                return content

        for key in ("output_text", "text"):
            content = cls._to_text(data.get(key))
            if content:
                return content

        return ""

    @staticmethod
    def _parse_json_response(response):
        """Parse JSON from raw bytes to avoid bad charset guesses."""
        tested = []
        encodings = []
        if response.encoding:
            encodings.append(response.encoding)
        encodings.extend(["utf-8", "utf-8-sig", "gb18030"])

        for enc in encodings:
            if enc in tested:
                continue
            tested.append(enc)
            try:
                return json.loads(response.content.decode(enc))
            except Exception:
                continue

        return response.json()

    def run(self):
        try:
            start_time = time.time()
            url_lower = self.base_url.lower()
            is_openai = (
                "openai" in url_lower
                or "v1/chat" in url_lower
                or "v1/chat/completions" in url_lower
            )

            if is_openai:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                }
            else:
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                }

            body = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": self.messages,
                "temperature": self.temperature,
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=body,
                timeout=120,
            )
            elapsed = (time.time() - start_time) * 1000

            if response.status_code != 200:
                self.error.emit(f"HTTP {response.status_code}: {response.text[:500]}")
                return

            try:
                data = self._parse_json_response(response)
            except Exception:
                self.error.emit(f"Invalid JSON response: {response.text[:500]}")
                return

            content = self._extract_content(data)
            if not content:
                content = json.dumps(data, ensure_ascii=False, indent=2)

            result = {
                "success": True,
                "content": content,
                "raw": json.dumps(data, ensure_ascii=False, indent=2),
                "time": f"{elapsed:.2f}ms",
                "tokens_used": data.get("usage", {}).get("output_tokens", 0),
            }
            self.finished.emit(result)

        except requests.exceptions.Timeout:
            self.error.emit("Request timed out. Please check your network.")
        except requests.exceptions.ConnectionError as exc:
            self.error.emit(f"Connection failed: {exc}")
        except Exception as exc:
            self.error.emit(f"Request error: {exc}")
