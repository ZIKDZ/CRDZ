import firebase_admin
from firebase_admin import credentials, db
import json
import os
import config
import logging
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        if not firebase_admin._apps:
            if not config.FIREBASE_CREDENTIALS_JSON:
                logger.error("FIREBASE_CREDENTIALS_JSON not set in environment")
                raise ValueError("FIREBASE_CREDENTIALS_JSON not set")
            # Validate JSON string
            try:
                credentials_dict = json.loads(config.FIREBASE_CREDENTIALS_JSON)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid FIREBASE_CREDENTIALS_JSON format: {e}")
                raise
            # Write JSON to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(credentials_dict, temp_file, indent=2)
                temp_file_path = temp_file.name
            try:
                cred = credentials.Certificate(temp_file_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': config.FIREBASE_DATABASE_URL
                })
                logger.info("Firebase initialized successfully.")
            finally:
                os.unlink(temp_file_path)  # Clean up temporary file
        else:
            logger.info("Firebase already initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise

initialize_firebase()

def load_data(path=''):
    """Load player data from Firebase Realtime Database."""
    try:
        ref = db.reference(path)
        data = ref.get()
        if data:
            logger.info(f"Loaded {len(data)} items from Firebase")
        else:
            logger.warning(f"No data found at Firebase path: {path or 'root'}")
        return data if data else {}
    except Exception as e:
        logger.error(f"Error loading data from Firebase: {e}")
        logger.info("Attempting to load from local JSON fallback...")
        if os.path.exists(config.DATA_FILE):
            try:
                with open(config.DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded data from local file: {config.DATA_FILE}")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Local JSON file is corrupted: {e}")
                return {}
        logger.warning(f"No local file found at: {config.DATA_FILE}")
        return {}

def save_data(data, path=''):
    """Save player data to Firebase Realtime Database."""
    try:
        ref = db.reference(path)
        ref.set(data)
        logger.info(f"Successfully saved data to Firebase path: {path or 'root'}")
        os.makedirs(os.path.dirname(config.DATA_FILE), exist_ok=True)
        with open(config.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Synced data to local file: {config.DATA_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to Firebase: {e}")
        return False

def update_data(path, key, value):
    """Update a specific key in Firebase."""
    try:
        ref = db.reference(path).child(key)
        ref.set(value)
        logger.info(f"Successfully updated data at: {path}/{key}")
        return True
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        return False

def push_data(data, path=''):
    """Push new data with auto-generated key."""
    try:
        ref = db.reference(path).push(data)
        logger.info(f"Pushed data to Firebase, key: {ref.key}")
        return ref.key
    except Exception as e:
        logger.error(f"Error pushing data: {e}")
        return None

def delete_data(path, key=None):
    """Delete data from Firebase."""
    target = f"{path}/{key}" if key else path or 'root'
    try:
        if key:
            ref = db.reference(path).child(key)
        else:
            ref = db.reference(path)
        ref.delete()
        logger.info(f"Successfully deleted data from: {target}")
        return True
    except Exception as e:
        logger.error(f"Error deleting data: {e}")
        return False