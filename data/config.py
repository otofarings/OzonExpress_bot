from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
BOT_NAME = env.str("BOT_NAME")

CREATORS = [int(env.str("CREATOR1")), int(env.str("CREATOR2"))]
CREATOR_SECRET = env.str("CREATOR_SECRET")
MODER_LOGS = env.str("MODERATOR_LOGGING")
ADMINS_LOGS = env.str("ADMINS_LOGGING")

IP = env.str("IP")
DB_CONN_INFO = {"user":     env.str("DB_USER"),
                "password": env.str("DB_PASS"),
                "host":     env.str("DB_HOST"),
                "database": env.str("DB_NAME")}

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

API_URL = "https://api-seller.ozon.ru"
USER_AGENT = "Mozilla/5.0 (Linux; 12; SM-G988B) AppleWebKit/537.36 (KHTML%2C like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36"
MAX_DISTANCE = 5000
TIMEOUT_POLLING = 5
TIMEOUT_SMALL_ERROR = 5
TIMEOUT_BIG_ERROR = 15
NEW_SELLER = False

DEBUG = False
DEBUG_FOLDER = env.str("DEBUG_FOLDER")
