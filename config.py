"""
Configuration and initialization module for Shelfie app.
Handles environment setup, logging, and service initialization.
"""
import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import speech, texttospeech, vision, translate_v2 as translate, bigquery

# Make pyttsx3 optional
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Note: pyttsx3 is not installed. Text-to-speech functionality will be disabled.")

# Load environment variables
load_dotenv()

# Configure logging for token tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nutrition_app_tokens.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure the Google APIs
GEMINI_API_KEY = os.getenv("AIzaSyA-84WzEBpPmh7PFYUGZyNIii_1QpFEIhQ")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
# Using the latest Gemini model that supports image analysis
model = genai.GenerativeModel("gemini-2.5-flash")

# Initialize Google Cloud services (optional, requires credentials)
GOOGLE_CLOUD_ENABLED = False
vision_client = None
translate_client = None
tts_client = None
speech_client = None
bq_client = None

try:
    vision_client = vision.ImageAnnotatorClient()
    translate_client = translate.Client()
    tts_client = texttospeech.TextToSpeechClient()
    speech_client = speech.SpeechClient()
    bq_client = bigquery.Client()
    GOOGLE_CLOUD_ENABLED = True
except Exception as e:
    GOOGLE_CLOUD_ENABLED = False
    logger.warning(f"Google Cloud services not configured: {e}")

