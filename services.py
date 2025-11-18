"""
API services module for Shelfie app.
Handles all external API calls: Gemini, Vision AI, Translation, TTS, BigQuery.
"""
import os
import io
import tempfile
from datetime import datetime
from PIL import Image
from google.cloud import vision, texttospeech

from config import (
    model, GOOGLE_CLOUD_ENABLED, vision_client, translate_client,
    tts_client, bq_client, logger, TTS_AVAILABLE
)
from utils import encode_image


def vision_ai_analysis(image):
    """Enhanced image analysis using Vision AI for object detection"""
    if not GOOGLE_CLOUD_ENABLED:
        return None
    
    try:
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Create Vision API image object
        vision_image = vision.Image(content=img_byte_arr)
        
        # Perform object detection
        objects = vision_client.object_localization(image=vision_image).localized_object_annotations
        
        # Perform label detection for food items
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
    """Translate nutrition response to different languages"""
    if not GOOGLE_CLOUD_ENABLED:
        return text
    
    try:
        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text


def text_to_speech(text, language_code='en-US'):
    """Convert nutrition analysis to speech"""
    try:
        # If pyttsx3 is available, use it as fallback
        if not GOOGLE_CLOUD_ENABLED and TTS_AVAILABLE:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                return
            except Exception as e:
                logger.warning(f"pyttsx3 TTS failed: {e}")
                print(f"[TTS Error]: {e}")
        
        # Use Google Cloud Text-to-Speech if available
        if GOOGLE_CLOUD_ENABLED:
            try:
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                # Configure the voice settings
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                )
                
                # Select the type of audio file you want returned
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                # Perform the text-to-speech request
                response = tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                # Play the audio using afplay (macOS)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    fp.write(response.audio_content)
                    temp_file = fp.name
                    
                # Play the audio file
                os.system(f'afplay {temp_file}')
                
                # Clean up
                os.unlink(temp_file)
                return
                
            except Exception as e:
                logger.error(f"Google TTS failed: {e}")
        
        # Fallback to simple print if TTS fails or is not available
        print(f"[TTS not available]: {text}")
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        print(f"[TTS Error]: {text}")


def save_to_bigquery(analysis_data):
    """Save nutrition analysis to BigQuery for analytics"""
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
    """Get nutritional information from meal image using Gemini AI"""
    image = Image.open(image_path)
    img_str = encode_image(image)
    
    # Enhanced analysis with Vision AI
    vision_data = None
    if use_vision_ai:
        vision_data = vision_ai_analysis(image)
    
    # Enhanced system prompt
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

    # Log input token count estimation
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
        
        # Log token usage information
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


def get_meal_suggestions_from_image(image_path, target_language='en'):
    """Generate meal suggestions from ingredient image"""
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
    """Generate meal suggestions from text list of ingredients"""
    
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

