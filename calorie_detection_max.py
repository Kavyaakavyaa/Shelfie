import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import os
from PIL import Image
import base64
import io
import logging
from datetime import datetime
import json
import requests
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import vision
from google.cloud import translate_v2 as translate
import pandas as pd
from google.cloud import bigquery
import tempfile
import speech_recognition as sr
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Note: pyttsx3 is not installed. Text-to-speech functionality will be disabled.")

import threading

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nutrition_app_tokens.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("AIzaSyA-84WzEBpPmh7PFYUGZyNIii_1QpFEIhQ"))

model = genai.GenerativeModel("gemini-2.5-flash")

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

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def vision_ai_analysis(image):
    if not GOOGLE_CLOUD_ENABLED:
        return None
    
    try:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        vision_image = vision.Image(content=img_byte_arr)
        
        objects = vision_client.object_localization(image=vision_image).localized_object_annotations
        
        labels = vision_client.label_detection(image=vision_image).label_annotations
        
        food_objects = []
        for obj in objects:
            if any(food_term in obj.name.lower() for food_term in ['food', 'fruit', 'vegetable', 'meat', 'bread', 'drink']):
                food_objects.append({
                    'name': obj.name,
                    'confidence': obj.score,
                    'location': [(vertex.x, vertex.y) for vertex in obj.bounding_poly.normalized_vertices]
                })
        
        food_labels = [label.description for label in labels if label.score > 0.7]
        
        return {'objects': food_objects, 'labels': food_labels}
    except Exception as e:
        logger.error(f"Vision AI analysis failed: {e}")
        return None

def translate_response(text, target_language='es'):
    if not GOOGLE_CLOUD_ENABLED:
        return text
    
    try:
        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text

def text_to_speech(text, language_code='en-US'):
    try:
        if not GOOGLE_CLOUD_ENABLED and TTS_AVAILABLE:
            try:
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                return
            except Exception as e:
                logger.warning(f"pyttsx3 TTS failed: {e}")
                print(f"[TTS Error]: {e}")
        
        if GOOGLE_CLOUD_ENABLED:
            try:
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                response = tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    fp.write(response.audio_content)
                    temp_file = fp.name
                    
                os.system(f'afplay {temp_file}')
                
                os.unlink(temp_file)
                return
                
            except Exception as e:
                logger.error(f"Google TTS failed: {e}")
        
        print(f"[TTS not available]: {text}")
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        print(f"[TTS Error]: {text}")

def save_to_bigquery(analysis_data):
    if not GOOGLE_CLOUD_ENABLED:
        return False
    
    try:
        dataset_id = "nutrition_analytics"
        table_id = "meal_analyses"
        
        table_ref = bq_client.dataset(dataset_id).table(table_id)
        
        rows_to_insert = [{
            'timestamp': datetime.now().isoformat(),
            'analysis_text': analysis_data['text'],
            'calories': analysis_data.get('calories', 0),
            'protein': analysis_data.get('protein', 0),
            'carbs': analysis_data.get('carbs', 0),
            'fat': analysis_data.get('fat', 0),
            'health_rating': analysis_data.get('health_rating', 'Unknown')
        }]
        
        errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
        if not errors:
            logger.info("Data saved to BigQuery successfully")
            return True
        else:
            logger.error(f"BigQuery insertion errors: {errors}")
            return False
    except Exception as e:
        logger.error(f"BigQuery save failed: {e}")
        return False

def get_nutritional_info(image_path, use_vision_ai=False, target_language='en'):
    image = Image.open(image_path)
    img_str = encode_image(image)
    
    vision_data = None
    if use_vision_ai:
        vision_data = vision_ai_analysis(image)
    
    system_prompt = f"""You are a certified nutritionist and registered dietitian with 15+ years of experience in food analysis and dietary assessment. Your expertise includes macro and micronutrient analysis, portion estimation, and health evaluation.

{f"ADDITIONAL CONTEXT: Vision AI detected these food items: {vision_data['labels'] if vision_data else 'None'}. Use this to enhance your analysis." if vision_data else ""}

INSTRUCTIONS:
1. Analyze the food image with precision and identify all visible food items
2. Estimate portion sizes using standard serving measurements
3. Calculate nutritional values based on recognized food databases (USDA, etc.)
4. Provide specific numerical values, not ranges
5. Give actionable dietary recommendations
6. Be concise but comprehensive

OUTPUT FORMAT:
**FOOD IDENTIFICATION:**
- List each food item with estimated portion size

**NUTRITIONAL BREAKDOWN:**
- Total Calories: [exact number] kcal
- Total Protein: [number] g
- Total Carbohydrates: [number] g
- Total Fat: [number] g
- Total Fiber: [number] g
- Total Sugar: [number] g
- Sodium: [number] mg
- Key Vitamins & Minerals: [list top 3-4]

**HEALTH ASSESSMENT:**
- Overall Health Rating: [Excellent/Good/Fair/Poor]
- Justification: [2-3 specific reasons]

**PROFESSIONAL RECOMMENDATIONS:**
- Immediate suggestions for meal improvement
- Portion adjustments if needed
- Complementary foods to add nutritional balance

EXAMPLES OF GOOD ANALYSIS:
- "Grilled chicken breast (4 oz) with steamed broccoli (1 cup) and brown rice (0.5 cup)"
- "Total Calories: 425 kcal, Protein: 35g, Carbs: 45g, Fat: 8g"
- "Health Rating: Excellent - balanced macros, high protein, fiber-rich vegetables"

Analyze this meal image and provide the complete nutritional assessment following the format above. No disclaimers or liability statements."""

    input_text_length = len(system_prompt)
    estimated_input_tokens = input_text_length // 4
    
    logger.info(f"=== API CALL START ===")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Input text length: {input_text_length} characters")
    logger.info(f"Estimated input tokens: {estimated_input_tokens}")
    logger.info(f"Vision AI enabled: {use_vision_ai}")
    logger.info(f"Target language: {target_language}")
    
    try:
        response = model.generate_content(
            contents=[
                {"mime_type": "image/png", "data": img_str},
                {"text": system_prompt}
            ]
        )
        
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            logger.info(f"ACTUAL TOKEN USAGE:")
            logger.info(f"Input tokens: {getattr(usage, 'prompt_token_count', 'N/A')}")
            logger.info(f"Output tokens: {getattr(usage, 'candidates_token_count', 'N/A')}")
            logger.info(f"Total tokens: {getattr(usage, 'total_token_count', 'N/A')}")
        else:
            output_text = ""
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        output_text += part.text
            
            output_length = len(output_text)
            estimated_output_tokens = output_length // 4
            estimated_total_tokens = estimated_input_tokens + estimated_output_tokens
            
            logger.info(f"ESTIMATED TOKEN USAGE (API metadata not available):")
            logger.info(f"Input tokens: ~{estimated_input_tokens}")
            logger.info(f"Output tokens: ~{estimated_output_tokens}")
            logger.info(f"Total tokens: ~{estimated_total_tokens}")
            logger.info(f"Output text length: {output_length} characters")
        
        logger.info(f"=== API CALL END ===")
        return response, vision_data
        
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        logger.info(f"=== API CALL FAILED ===")
        raise e

def extract_nutrition_values(text):
    import re
    
    patterns = {
        'calories': r'Total Calories:\s*(\d+)',
        'protein': r'Total Protein:\s*(\d+(?:\.\d+)?)',
        'carbs': r'Total Carbohydrates:\s*(\d+(?:\.\d+)?)',
        'fat': r'Total Fat:\s*(\d+(?:\.\d+)?)',
        'health_rating': r'Overall Health Rating:\s*(\w+)'
    }
    
    values = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if key == 'health_rating':
                values[key] = match.group(1)
            else:
                values[key] = float(match.group(1))
        else:
            values[key] = 0 if key != 'health_rating' else 'Unknown'
    
    return values

def get_meal_suggestions_from_image(image_path, target_language='en'):
    image = Image.open(image_path)
    img_str = encode_image(image)
    
    system_prompt = f"""You are an expert chef and nutritionist with extensive knowledge of global cuisines and recipe creation. Your task is to analyze ingredients and suggest creative, delicious meal options.

INSTRUCTIONS:
1. Identify all visible ingredients in the image
2. Suggest 5-7 diverse meal options that can be made with these ingredients
3. For each meal, provide:
   - Meal name and cuisine type
   - Brief description (1-2 sentences)
   - Estimated prep/cook time
   - Difficulty level (Easy/Medium/Hard)
   - Approximate calories per serving
   - Key ingredients used from the available ones
4. Be creative and suggest meals from different cuisines
5. Consider both simple and more complex recipes
6. If some common ingredients are missing, suggest what could be added (optional)

OUTPUT FORMAT:
**AVAILABLE INGREDIENTS DETECTED:**
- List all ingredients identified

**MEAL SUGGESTIONS:**

**1. [Meal Name]**
- Cuisine: [Type]
- Description: [Brief description]
- Prep Time: [X minutes]
- Cook Time: [X minutes]
- Difficulty: [Easy/Medium/Hard]
- Calories: ~[X] kcal per serving
- Ingredients Used: [List]
- Optional Additions: [If any]

[Repeat for each meal suggestion]

Analyze the ingredients in this image and provide creative meal suggestions following the format above."""

    logger.info(f"=== MEAL SUGGESTION API CALL START ===")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        response = model.generate_content(
            contents=[
                {"mime_type": "image/png", "data": img_str},
                {"text": system_prompt}
            ]
        )
        
        logger.info(f"=== MEAL SUGGESTION API CALL END ===")
        return response
        
    except Exception as e:
        logger.error(f"Meal suggestion API call failed: {str(e)}")
        raise e

def get_meal_suggestions_from_text(ingredients_text, target_language='en'):
    
    system_prompt = f"""You are an expert chef and nutritionist with extensive knowledge of global cuisines and recipe creation. Your task is to analyze ingredients and suggest creative, delicious meal options.

AVAILABLE INGREDIENTS:
{ingredients_text}

INSTRUCTIONS:
1. Analyze the provided ingredients
2. Suggest 5-7 diverse meal options that can be made with these ingredients
3. For each meal, provide:
   - Meal name and cuisine type
   - Brief description (1-2 sentences)
   - Estimated prep/cook time
   - Difficulty level (Easy/Medium/Hard)
   - Approximate calories per serving
   - Key ingredients used from the available ones
4. Be creative and suggest meals from different cuisines
5. Consider both simple and more complex recipes
6. If some common ingredients are missing, suggest what could be added (optional)

OUTPUT FORMAT:
**MEAL SUGGESTIONS:**

**1. [Meal Name]**
- Cuisine: [Type]
- Description: [Brief description]
- Prep Time: [X minutes]
- Cook Time: [X minutes]
- Difficulty: [Easy/Medium/Hard]
- Calories: ~[X] kcal per serving
- Ingredients Used: [List]
- Optional Additions: [If any]

[Repeat for each meal suggestion]

Analyze the provided ingredients and suggest creative meal options following the format above."""

    logger.info(f"=== MEAL SUGGESTION API CALL START (TEXT) ===")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        response = model.generate_content(system_prompt)
        
        logger.info(f"=== MEAL SUGGESTION API CALL END ===")
        return response
        
    except Exception as e:
        logger.error(f"Meal suggestion API call failed: {str(e)}")
        raise e

def display_meal_suggestions(response, target_language='en'):
    st.markdown("""
        <div class="premium-card" style="margin-top: 2rem;">
            <div class="card-title">🍽️ Meal Suggestions</div>
    """, unsafe_allow_html=True)
    
    try:
        response_text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                response_text += part.text
        
        if target_language != 'en':
            response_text = translate_response(response_text, target_language)
        
        content = response_text
        if "AVAILABLE INGREDIENTS" in content:
            content = content.replace("**AVAILABLE INGREDIENTS DETECTED:**", "### 🥬 Available Ingredients Detected")
        if "MEAL SUGGESTIONS:" in content:
            content = content.replace("**MEAL SUGGESTIONS:**", "### 🍳 Meal Suggestions")
        
        st.markdown(content)
        st.markdown("</div>", unsafe_allow_html=True)
        
        return response_text
        
    except AttributeError as e:
        st.error(f"Error in accessing the response attributes: {e}")
        st.info("Please try again or check your API configuration.")
        st.markdown("</div>", unsafe_allow_html=True)
        return None

def display_response(response, vision_data=None, target_language='en'):
    st.markdown("""
        <div class="premium-card" style="margin-top: 2rem;">
            <div class="card-title">🥗 Professional Nutritional Analysis</div>
    """, unsafe_allow_html=True)
    try:
        response_text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                response_text += part.text
        
        if target_language != 'en':
            response_text = translate_response(response_text, target_language)
        
        content = response_text
        if "FOOD IDENTIFICATION:" in content:
            content = content.replace("**FOOD IDENTIFICATION:**", "### 🍽️ Food Identification")
        if "NUTRITIONAL BREAKDOWN:" in content:
            content = content.replace("**NUTRITIONAL BREAKDOWN:**", "### 📊 Nutritional Breakdown")
        if "HEALTH ASSESSMENT:" in content:
            content = content.replace("**HEALTH ASSESSMENT:**", "### 🏥 Health Assessment")
        if "PROFESSIONAL RECOMMENDATIONS:" in content:
            content = content.replace("**PROFESSIONAL RECOMMENDATIONS:**", "### 💡 Professional Recommendations")
        
        st.markdown(content)
        
        if vision_data and vision_data['objects']:
            with st.expander("🤖 Vision AI Detection Results"):
                st.write("**Detected Food Objects:**")
                for obj in vision_data['objects']:
                    st.write(f"- {obj['name']} (Confidence: {obj['confidence']:.2f})")
        
        nutrition_values = extract_nutrition_values(response_text)
        nutrition_values['text'] = response_text
        
        if st.session_state.get('save_to_bq', False):
            save_success = save_to_bigquery(nutrition_values)
            if save_success:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 185, 129, 0.15) 100%); 
                                border-left: 4px solid #4ade80; border-radius: 10px; 
                                padding: 1rem; margin-top: 1rem;">
                        <p style="margin: 0; color: #86efac; font-weight: 600;">✅ Analysis saved to BigQuery for analytics</p>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        return response_text, nutrition_values
        
    except AttributeError as e:
        st.error(f"Error in accessing the response attributes: {e}")
        st.info("Please try uploading the image again or check your API configuration.")
        return None, None

# Premium Dark Theme CSS for Shelfie
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 3rem;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(102, 126, 234, 0.2);
        text-align: center;
    }
    
    .app-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.75rem;
        letter-spacing: -1.5px;
        line-height: 1.1;
    }
    
    .app-subtitle {
        color: #94a3b8;
        font-size: 1.15rem;
        font-weight: 400;
        margin-top: 0.5rem;
        line-height: 1.6;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Premium Card Styling */
    .premium-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 18px;
        padding: 2rem;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 2rem;
    }
    
    .premium-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 50px rgba(102, 126, 234, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    .card-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        letter-spacing: -0.3px;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(129, 140, 248, 0.4);
        letter-spacing: 0.2px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(129, 140, 248, 0.5);
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* File Uploader Styling */
    .stFileUploader > div {
        border: 2.5px dashed rgba(148, 163, 184, 0.4);
        border-radius: 16px;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stFileUploader > div:hover {
        border-color: #818cf8;
        background: linear-gradient(135deg, #334155 0%, #475569 100%);
        box-shadow: 0 4px 30px rgba(129, 140, 248, 0.25);
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid rgba(148, 163, 184, 0.3);
        padding: 0.85rem 1.25rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        background: #334155;
        color: #f1f5f9;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #818cf8;
        box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.2);
        outline: none;
        background: #475569;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid rgba(148, 163, 184, 0.3);
        padding: 0.85rem 1.25rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        background: #334155;
        color: #f1f5f9;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #818cf8;
        box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.2);
        outline: none;
        background: #475569;
    }
    
    /* Selectbox Styling */
    .stSelectbox > div > div > select {
        border-radius: 12px;
        border: 2px solid rgba(148, 163, 184, 0.3);
        padding: 0.85rem 1.25rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        background: #334155;
        color: #f1f5f9;
    }
    
    .stSelectbox > div > div > select:focus {
        border-color: #818cf8;
        box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.2);
    }
    
    /* Checkbox Styling */
    .stCheckbox {
        margin: 1rem 0;
    }
    
    .stCheckbox > label {
        font-size: 0.95rem;
        color: #cbd5e1;
        font-weight: 500;
        padding-left: 0.5rem;
    }
    
    /* Markdown Headings */
    .stMarkdown h1 {
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1.2;
    }
    
    .stMarkdown h2, .stMarkdown h3 {
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .stMarkdown h3 {
        font-size: 1.35rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .stMarkdown p {
        color: #cbd5e1;
    }
    
    /* Image Styling */
    .stImage > img {
        border-radius: 16px;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
        border: 2px solid rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .stImage > img:hover {
        transform: scale(1.01);
        box-shadow: 0 12px 50px rgba(102, 126, 234, 0.4);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    .sidebar .sidebar-content {
        background: transparent;
    }
    
    /* Sidebar Cards */
    .sidebar-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 1.75rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(102, 126, 234, 0.2);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .sidebar-card:hover {
        box-shadow: 0 6px 40px rgba(102, 126, 234, 0.3);
        transform: translateY(-2px);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    .sidebar-card h2, .sidebar-card h4 {
        color: #f1f5f9;
    }
    
    /* Info Boxes */
    .info-box {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.1) 100%);
        border-left: 4px solid #60a5fa;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 15px rgba(59, 130, 246, 0.2);
    }
    
    .info-box p {
        color: #bfdbfe;
    }
    
    /* Feature List */
    .feature-list {
        list-style: none;
        padding: 0;
        margin: 1rem 0;
    }
    
    .feature-list li {
        padding: 0.6rem 0;
        color: #cbd5e1;
        line-height: 1.7;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .feature-list li:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: #818cf8;
        font-weight: 700;
        font-size: 1.1rem;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem 0;
    }
    
    .status-success {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .status-warning {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    
    /* Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.3), transparent);
        margin: 2.5rem 0;
        border: none;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: #334155;
        border-radius: 10px;
        padding: 1rem;
        font-weight: 600;
        color: #f1f5f9;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .streamlit-expanderContent {
        background: #1e293b;
        color: #cbd5e1;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 185, 129, 0.15) 100%);
        border-left: 4px solid #4ade80;
        border-radius: 10px;
        padding: 1rem;
        color: #86efac;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.15) 100%);
        border-left: 4px solid #f87171;
        border-radius: 10px;
        padding: 1rem;
        color: #fca5a5;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.15) 100%);
        border-left: 4px solid #60a5fa;
        border-radius: 10px;
        padding: 1rem;
        color: #93c5fd;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #475569 0%, #64748b 100%);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #64748b 0%, #818cf8 100%);
    }
    
    /* Spinner Styling */
    .stSpinner > div {
        border-top-color: #818cf8;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 35px rgba(102, 126, 234, 0.3);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    /* Caption styling */
    .stImage > div > div > p {
        color: #94a3b8;
    }
    
    /* Selectbox options */
    option {
        background: #334155;
        color: #f1f5f9;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 12px 12px 0 0;
        padding: 0.75rem 1.5rem;
        color: #94a3b8;
        font-weight: 500;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #334155;
        color: #cbd5e1;
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: #f1f5f9;
        border-color: rgba(102, 126, 234, 0.5);
        border-bottom-color: transparent;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.5rem;
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: #1e293b;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .stRadio > label {
        color: #cbd5e1;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI with Shelfie branding
st.set_page_config(
    page_title="Shelfie - AI-Powered Food Analysis",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Main Header
st.markdown("""
    <div class="main-header">
        <div class="app-title">📱 Shelfie</div>
        <div class="app-subtitle">
            Advanced AI-powered food analysis. Get instant nutritional insights, calorie tracking, and personalized dietary recommendations from your food photos.
        </div>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'meal_suggestions_history' not in st.session_state:
    st.session_state.meal_suggestions_history = []

# Create tabs for different features
tab1, tab2 = st.tabs(["📸 Analyze Meal", "🍽️ Get Meal Suggestions"])

with tab1:
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
            <div class="premium-card">
                <div class="card-title">📸 Upload Your Meal</div>
                <p style='color: #cbd5e1; margin-bottom: 1.5rem; line-height: 1.7; font-size: 0.95rem;'>
                    Take or upload a clear photo of your meal to receive instant nutritional analysis and insights powered by advanced AI.
                </p>
        """, unsafe_allow_html=True)
        
        uploaded_image = st.file_uploader(
            label="Choose an image...",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
            help="For best results, ensure good lighting and all food items are visible"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # AI Enhancement Options
        st.markdown("""
            <div class="premium-card">
                <div class="card-title">⚙️ Analysis Options</div>
                <p style='color: #cbd5e1; margin-bottom: 1.5rem; line-height: 1.7; font-size: 0.95rem;'>
                    Customize your analysis with these advanced AI-powered features
                </p>
        """, unsafe_allow_html=True)
        col_ai1, col_ai2 = st.columns(2)
        
        with col_ai1:
            use_vision_ai = st.checkbox("🔍 Use Vision AI Detection", 
                                       value=False, 
                                       help="Enhanced food detection using Google Vision AI")
            
            target_language = st.selectbox("🌍 Analysis Language", 
                                         ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'zh'],
                                         format_func=lambda x: {
                                             'en': '🇺🇸 English',
                                             'es': '🇪🇸 Spanish', 
                                             'fr': '🇫🇷 French',
                                             'de': '🇩🇪 German',
                                             'it': '🇮🇹 Italian',
                                             'pt': '🇵🇹 Portuguese',
                                             'hi': '🇮🇳 Hindi',
                                             'zh': '🇨🇳 Chinese'
                                         }[x])
        
        with col_ai2:
            enable_tts = st.checkbox("🔊 Text-to-Speech", 
                                   value=False,
                                   help="Convert analysis to audio")
            
            st.session_state.save_to_bq = st.checkbox("📊 Save to BigQuery", 
                                                     value=False,
                                                     help="Store analysis for future analytics")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if uploaded_image is not None:
            st.markdown("""
                <div class="premium-card" style="text-align: center;">
            """, unsafe_allow_html=True)
            st.image(uploaded_image, caption="Your Meal", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("🔍 Analyze with Multi-AI", type="primary"):
                with st.spinner("🧠 Multi-AI system analyzing your meal..."):
                    try:
                        response, vision_data = get_nutritional_info(
                            uploaded_image, 
                            use_vision_ai=use_vision_ai,
                            target_language=target_language
                        )
                        
                        response_text, nutrition_values = display_response(
                            response, 
                            vision_data, 
                            target_language
                        )
                        
                        # Text-to-Speech
                        if enable_tts and response_text:
                            with st.spinner("🔊 Generating audio..."):
                                audio_content = text_to_speech(response_text, 
                                                             f"{target_language}-US" if target_language == 'en' else f"{target_language}")
                                if audio_content:
                                    st.audio(audio_content, format='audio/mp3')
                        
                        # Save to history
                        st.session_state.analysis_history.append({
                            'timestamp': datetime.now(),
                            'nutrition_values': nutrition_values,
                            'language': target_language,
                            'vision_ai_used': use_vision_ai
                        })
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
                        st.info("Please check your API configurations and internet connection.")
    
    with col2:
        # Sidebar content for tab1 will be added here if needed
        pass

with tab2:
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
            <div class="premium-card">
                <div class="card-title">🥬 Input Your Ingredients</div>
                <p style='color: #cbd5e1; margin-bottom: 1.5rem; line-height: 1.7; font-size: 0.95rem;'>
                    Upload a photo of your ingredients or enter them as text to get personalized meal suggestions powered by AI.
                </p>
        """, unsafe_allow_html=True)
        
        # Toggle between image and text input
        input_mode = st.radio(
            "Choose input method:",
            ["📷 Photo Upload", "✍️ Text Input"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if input_mode == "📷 Photo Upload":
            st.markdown("""
                <div class="premium-card">
                    <div class="card-title">📷 Upload Ingredients Photo</div>
                    <p style='color: #cbd5e1; margin-bottom: 1.5rem; line-height: 1.7; font-size: 0.95rem;'>
                        Take or upload a photo showing all your available ingredients.
                    </p>
            """, unsafe_allow_html=True)
            
            ingredients_image = st.file_uploader(
                label="Choose an ingredients image...",
                type=["jpg", "jpeg", "png"],
                key="ingredients_uploader",
                label_visibility="collapsed",
                help="Upload a clear photo of your ingredients"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if ingredients_image is not None:
                st.markdown("""
                    <div class="premium-card" style="text-align: center;">
                """, unsafe_allow_html=True)
                st.image(ingredients_image, caption="Your Ingredients", use_column_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Language selection for meal suggestions
                st.markdown("""
                    <div class="premium-card">
                        <div class="card-title">⚙️ Options</div>
                """, unsafe_allow_html=True)
                
                suggestion_language = st.selectbox(
                    "🌍 Suggestion Language", 
                    ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'zh'],
                    key="suggestion_lang",
                    format_func=lambda x: {
                        'en': '🇺🇸 English',
                        'es': '🇪🇸 Spanish', 
                        'fr': '🇫🇷 French',
                        'de': '🇩🇪 German',
                        'it': '🇮🇹 Italian',
                        'pt': '🇵🇹 Portuguese',
                        'hi': '🇮🇳 Hindi',
                        'zh': '🇨🇳 Chinese'
                    }[x])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("🍽️ Get Meal Suggestions", type="primary", key="suggest_from_image"):
                    with st.spinner("🧠 AI chef analyzing your ingredients and creating meal suggestions..."):
                        try:
                            response = get_meal_suggestions_from_image(
                                ingredients_image,
                                target_language=suggestion_language
                            )
                            
                            suggestions_text = display_meal_suggestions(response, suggestion_language)
                            
                            # Save to history
                            if suggestions_text:
                                st.session_state.meal_suggestions_history.append({
                                    'timestamp': datetime.now(),
                                    'mode': 'image',
                                    'language': suggestion_language,
                                    'suggestions': suggestions_text
                                })
                            
                        except Exception as e:
                            st.error(f"Failed to generate meal suggestions: {str(e)}")
                            st.info("Please check your API configurations and internet connection.")
        
        else:  # Text Input
            st.markdown("""
                <div class="premium-card">
                    <div class="card-title">✍️ Enter Ingredients</div>
                    <p style='color: #cbd5e1; margin-bottom: 1.5rem; line-height: 1.7; font-size: 0.95rem;'>
                        List all the ingredients you have available. You can separate them by commas, lines, or bullets.
                    </p>
            """, unsafe_allow_html=True)
            
            ingredients_text = st.text_area(
                "Ingredients",
                placeholder="Example:\n- Chicken breast\n- Tomatoes\n- Onions\n- Garlic\n- Olive oil\n- Pasta\n- Cheese",
                height=200,
                key="ingredients_text_area",
                help="Enter all your available ingredients"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if ingredients_text.strip():
                st.markdown("""
                    <div class="premium-card">
                        <div class="card-title">⚙️ Options</div>
                """, unsafe_allow_html=True)
                
                suggestion_language_text = st.selectbox(
                    "🌍 Suggestion Language", 
                    ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'zh'],
                    key="suggestion_lang_text",
                    format_func=lambda x: {
                        'en': '🇺🇸 English',
                        'es': '🇪🇸 Spanish', 
                        'fr': '🇫🇷 French',
                        'de': '🇩🇪 German',
                        'it': '🇮🇹 Italian',
                        'pt': '🇵🇹 Portuguese',
                        'hi': '🇮🇳 Hindi',
                        'zh': '🇨🇳 Chinese'
                    }[x])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("🍽️ Get Meal Suggestions", type="primary", key="suggest_from_text"):
                    with st.spinner("🧠 AI chef analyzing your ingredients and creating meal suggestions..."):
                        try:
                            response = get_meal_suggestions_from_text(
                                ingredients_text,
                                target_language=suggestion_language_text
                            )
                            
                            suggestions_text = display_meal_suggestions(response, suggestion_language_text)
                            
                            # Save to history
                            if suggestions_text:
                                st.session_state.meal_suggestions_history.append({
                                    'timestamp': datetime.now(),
                                    'mode': 'text',
                                    'language': suggestion_language_text,
                                    'suggestions': suggestions_text
                                })
                            
                        except Exception as e:
                            st.error(f"Failed to generate meal suggestions: {str(e)}")
                            st.info("Please check your API configurations and internet connection.")
    
    with col2:
        # Sidebar content for tab2 will be added here if needed
        pass

# Shared sidebar (appears on both tabs)
    st.sidebar.markdown("""
    <div class="sidebar-card">
        <h2 style='color: #f1f5f9; margin-top: 0; font-size: 1.35rem; font-weight: 700; margin-bottom: 1rem;'>📊 Analysis Features</h2>
        <ul class="feature-list">
                <li>Comprehensive nutrition analysis</li>
                <li>Calorie and macro tracking</li>
            <li>Meal suggestions from ingredients</li>
                <li>Multi-language support</li>
                <li>Detailed food recognition</li>
            <li>Health rating & recommendations</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
st.sidebar.markdown("""
    <div class="sidebar-card">
        <h4 style='color: #f1f5f9; margin-top: 0; font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;'>📸 Best Practices</h4>
        <ul class="feature-list">
            <li>Use natural, even lighting</li>
            <li>Shoot directly from above</li>
            <li>Keep camera steady and focused</li>
            <li>Include reference for scale</li>
            <li>Minimize background clutter</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
# Info box
st.sidebar.markdown("""
    <div class="info-box">
        <p style='margin: 0; font-size: 0.9rem; color: #1e40af; line-height: 1.6;'>
            <span style='font-weight: 700; display: block; margin-bottom: 0.5rem; font-size: 1rem;'>💡 Nutritional Insights</span>
            Regular meal tracking can help identify dietary patterns and support healthier eating habits.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
# AI Services Status
st.sidebar.markdown("""
    <div class="sidebar-card">
        <h4 style='color: #f1f5f9; margin-top: 0; font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;'>🔬 AI Services Status</h4>
    """, unsafe_allow_html=True)
    
st.sidebar.markdown("""
    <div class="status-badge status-success" style="display: block; width: 100%; text-align: center; margin-bottom: 0.5rem;">
        ✅ Gemini AI (Active)
    </div>
    """, unsafe_allow_html=True)
    
if GOOGLE_CLOUD_ENABLED:
    st.sidebar.markdown("""
        <div class="status-badge status-success" style="display: block; width: 100%; text-align: center; margin-bottom: 0.5rem;">
            ✅ Vision AI (Available)
        </div>
        <div class="status-badge status-success" style="display: block; width: 100%; text-align: center; margin-bottom: 0.5rem;">
            ✅ Translation (Available)
        </div>
        <div class="status-badge status-success" style="display: block; width: 100%; text-align: center; margin-bottom: 0.5rem;">
            ✅ Text-to-Speech (Available)
        </div>
        <div class="status-badge status-success" style="display: block; width: 100%; text-align: center; margin-bottom: 0.5rem;">
            ✅ BigQuery (Available)
        </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
        <div class="status-badge status-warning" style="display: block; width: 100%; text-align: center;">
            ⚠️ Google Cloud Services (Not Configured)
        </div>
    """, unsafe_allow_html=True)
    
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Analysis History
if st.session_state.analysis_history:
    st.sidebar.markdown("""
        <div class="sidebar-card">
            <h4 style='color: #f1f5f9; margin-top: 0; font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;'>📈 Recent Analyses</h4>
        """, unsafe_allow_html=True)
    
    for i, analysis in enumerate(st.session_state.analysis_history[-3:]):
        with st.sidebar.expander(f"📊 Analysis {len(st.session_state.analysis_history)-i}"):
            st.markdown(f"""
                <div style="padding: 0.5rem 0;">
                    <p style="margin: 0.25rem 0; color: #cbd5e1;"><strong>Time:</strong> {analysis['timestamp'].strftime('%H:%M')}</p>
                    <p style="margin: 0.25rem 0; color: #cbd5e1;"><strong>Calories:</strong> {analysis['nutrition_values'].get('calories', 'N/A')} kcal</p>
                    <p style="margin: 0.25rem 0; color: #cbd5e1;"><strong>Language:</strong> {analysis['language'].upper()}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
# Meal Suggestions History
if st.session_state.meal_suggestions_history:
    st.sidebar.markdown("""
        <div class="sidebar-card">
            <h4 style='color: #f1f5f9; margin-top: 0; font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;'>🍽️ Recent Meal Suggestions</h4>
        """, unsafe_allow_html=True)
    
    for i, suggestion in enumerate(st.session_state.meal_suggestions_history[-3:]):
        mode_icon = "📷" if suggestion['mode'] == 'image' else "✍️"
        with st.sidebar.expander(f"{mode_icon} Suggestions {len(st.session_state.meal_suggestions_history)-i}"):
            st.markdown(f"""
                <div style="padding: 0.5rem 0;">
                    <p style="margin: 0.25rem 0; color: #cbd5e1;"><strong>Time:</strong> {suggestion['timestamp'].strftime('%H:%M')}</p>
                    <p style="margin: 0.25rem 0; color: #cbd5e1;"><strong>Mode:</strong> {suggestion['mode'].title()}</p>
                    <p style="margin: 0.25rem 0; color: #cbd5e1;"><strong>Language:</strong> {suggestion['language'].upper()}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Premium Footer
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; padding: 2.5rem 0; color: #64748b; font-size: 0.9rem; line-height: 1.8;'>
        <p style='margin: 0.5rem 0; font-weight: 500; color: #94a3b8;'>Multi-AI Powered Nutrition Analysis</p>
        <p style='margin: 0.5rem 0; color: #64748b;'>Gemini AI • Vision AI • Translation • Text-to-Speech • BigQuery</p>
        <p style='margin: 1rem 0 0 0; font-size: 0.85rem; color: #475569;'>Built with precision for your health journey</p>
    </div>
""", unsafe_allow_html=True)
