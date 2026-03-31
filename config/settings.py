# -*- coding: utf-8 -*-
"""应用配置"""

# 窗口配置
WINDOW_TITLE = "API Client"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_POS_X = 150
WINDOW_POS_Y = 100

# 颜色配置 (清新浅色主题)
COLORS = {
    'bg_primary': '#F8F9FA',      # 主背景
    'bg_secondary': '#FFFFFF',    # 次级背景
    'bg_surface': '#E9ECEF',      # 表面
    'bg_hover': '#DEE2E6',        # 悬停
    'text_primary': '#212529',    # 主文字
    'text_secondary': '#6C757D',  # 次级文字
    'accent_primary': '#4DABF7',  # 主强调色 (蓝色)
    'accent_hover': '#339AF0',    # 强调色悬停
    'accent_success': '#51CF66',  # 成功 (绿色)
    'accent_warning': '#FFB84D',  # 警告 (橙色)
    'accent_danger': '#FF6B6B',   # 危险 (红色)
    'accent_purple': '#CC5DE8',   # 紫色
    'border': '#CED4DA',          # 边框
    'shadow': 'rgba(0,0,0,0.1)',  # 阴影
}

# 请求配置
DEFAULT_TIMEOUT = 60
DEFAULT_MODEL = "claude-sonnet-4-5-20251001"

# 字体配置
FONT_FAMILY = "Consolas"
FONT_SIZE = 11
FONT_FAMILY_UI = "Microsoft YaHei"
FONT_FAMILY_UI_LIGHT = "Microsoft YaHei Light"

# 默认 API 配置
DEFAULT_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7

# 模型列表 (支持 Claude 全系列)
MODELS = [
    # Claude 4.6 系列 (最新)
    "claude-opus-4-6-20260331",
    "claude-sonnet-4-6-20260331",
    # Claude 4.5 系列
    "claude-opus-4-5-20251001",
    "claude-sonnet-4-5-20251001",
    # Claude 3.5 系列
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    # Claude 3 系列
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
]

# 根据 API URL 自动检测可用模型
def get_models_for_api(api_url: str) -> list:
    """根据 API URL 返回合适的模型列表"""
    url_lower = api_url.lower()

    # Anthropic 官方 API
    if 'anthropic' in url_lower:
        return MODELS

    # OpenAI 兼容 API
    if 'openai' in url_lower or 'v1/chat' in url_lower:
        return [
            "gpt-4.5-preview",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    # 自定义 API - 返回通用列表
    return MODELS + [
        "gpt-4.5-preview",
        "gpt-4-turbo",
        "deepseek-chat",
        "deepseek-coder",
    ]
