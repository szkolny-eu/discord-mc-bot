import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID"))
STATUS_MESSAGE_ID = int(os.getenv("STATUS_MESSAGE_ID"))
CHAT_CHANNEL_ID = int(os.getenv("CHAT_CHANNEL_ID"))
OP_USER_ID = int(os.getenv("OP_USER_ID"))
DATE_FORMAT = os.getenv("DATE_FORMAT")

HOMEPAGE_URL = os.getenv("HOMEPAGE_URL")
SKINS_URL = os.getenv("SKINS_URL")
EMBED_IMAGE_URL = os.getenv("EMBED_IMAGE_URL")
SERVER_IP = os.getenv("SERVER_IP")
SERVER_VERSION = os.getenv("SERVER_VERSION")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
