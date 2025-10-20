import configparser
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

config = configparser.ConfigParser()
config.read('config.ini')

# Tokens - Use environment variables for security
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CR_API_TOKEN = os.getenv('CR_API_TOKEN')

# Roles - Read from config.ini (not sensitive)
ROLE_UNDER_5K = int(config.get('Roles', 'ROLE_UNDER_5K', fallback='0'))
ROLE_ABOVE_5K = int(config.get('Roles', 'ROLE_ABOVE_5K', fallback='0'))
ROLE_ABOVE_10K = int(config.get('Roles', 'ROLE_ABOVE_10K', fallback='0'))

# Emojis - Read from config.ini (not sensitive)
EMOJI_LAUGH = config.get('Emojis', 'EMOJI_LAUGH', fallback='�')
EMOJI_TROPHY = config.get('Emojis', 'EMOJI_TROPHY', fallback='�')
EMOJI_SAD = config.get('Emojis', 'EMOJI_SAD', fallback='�')
EMOJI_THINK = config.get('Emojis', 'EMOJI_THINK', fallback='�')
EMOJI_COOL = config.get('Emojis', 'EMOJI_COOL', fallback='�')

# Paths - Read from config.ini (not sensitive)
DATA_FILE = config.get('Paths', 'DATA_FILE', fallback='data/players.json')
FONT_PATH = config.get('Paths', 'FONT_PATH', fallback='fonts/Supercell-Magic-Regular.ttf')

# Firebase config - Add these for Firebase integration
# Store sensitive Firebase credentials in .env for security (e.g., FIREBASE_CREDENTIALS_PATH)
FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON')
FIREBASE_DATABASE_URL = "https://crdz-players-default-rtdb.europe-west1.firebasedatabase.app/"