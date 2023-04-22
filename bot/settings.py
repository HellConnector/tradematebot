import os

from dotenv import load_dotenv

load_dotenv()

# Database
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Currency API
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

# Docker registry
DOCKER_HUB_TOKEN = os.getenv("DOCKER_HUB_TOKEN")
