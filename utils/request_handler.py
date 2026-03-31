# -*- coding: utf-8 -*-
"""API 请求处理"""

import time
import requests
from PyQt5.QtCore import QThread, pyqtSignal


class ApiRequestThread(QThread):
    """API 请求线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, headers, body, timeout=30):
        super().__init__()
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.timeout = timeout

    def run(self):
        try:
            start_time = time.time()

            if self.method in ['GET', 'DELETE']:
                response = getattr(requests, self.method.lower())(
                    self.url, headers=self.headers, timeout=self.timeout
                )
            else:
                response = getattr(requests, self.method.lower())(
                    self.url, headers=self.headers, data=self.body, timeout=self.timeout
                )

            elapsed = (time.time() - start_time) * 1000

            result = {
                'status': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'time': f"{elapsed:.2f}ms",
                'size': f"{len(response.content)} bytes"
            }
            self.finished.emit(result)

        except requests.exceptions.Timeout:
            self.error.emit(f"请求超时 ({self.timeout}秒)")
        except requests.exceptions.ConnectionError as e:
            self.error.emit(f"连接错误：{str(e)}")
        except requests.exceptions.RequestException as e:
            self.error.emit(f"请求失败：{str(e)}")
        except Exception as e:
            self.error.emit(f"未知错误：{str(e)}")
