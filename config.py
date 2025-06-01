"""Конфигурация и ключи API.
   ⚠️ В продакшене вынесите секреты в переменные окружения / Vault.
"""
import os

# OpenAI (через прокси-эндпоинт)
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY",
                            "sk-2uHtBOkjr3ZrCn43aUt4WdEZ20JaXu49")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL",
                            "https://api.proxyapi.ru/openai/v1")

# Google Custom Search
GOOGLE_API_KEYS = os.getenv("GOOGLE_API_KEYS",
    "AIzaSyDfSS4_mrxnYunncB8jNrEYhzdG6xKNnVo,"
    "AIzaSyBSm_HIcfRldGzOcXNI0vkR7RsQoOEXGi4").split(",")

GOOGLE_CSE_IDS  = os.getenv("GOOGLE_CSE_IDS",
    "0483b4fa074fb4926,4250878bae6de4310").split(",")

# VK API
VK_TOKEN        = os.getenv("VK_TOKEN",
    "vk1.a.Rkq9-ZoLfau7E-arkUibVjZyysUHGcdNk-"
    "MpzgqzqxOH7ozNxK4dOYyw7FIah4yAAp_yxkvuIkabPg8q3v_2bZRY5"
    "jQ5aMWyMhG4oEKiYQ7RKEnksO79V_S-dV2FIPxm42fg7jb1tlQVgoDF"
    "QcR5BTON4DtTfIJ9EK0UfA7chfu7GIPQbUK3uFAD4_-8ZFzeJvtoU9I"
    "onuRHuQeaznh-Cg")

# Хранилище
DATABASE_URL    = os.getenv("DATABASE_URL",
                            "sqlite:///dance_platform.db")

# Лимиты / настройки
RECOMMENDATION_LIMIT = int(os.getenv("RECOMMENDATION_LIMIT", "20"))
AGGREGATION_LIMIT    = int(os.getenv("AGGREGATION_LIMIT", "20"))
SOCIAL_LIMIT         = int(os.getenv("SOCIAL_LIMIT", "20"))
