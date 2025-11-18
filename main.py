"""
Main application entry point for Shelfie - AI-Powered Food Analysis App.
This is the refactored modular version of the original calorie_detection_max.py
"""
import streamlit as st
from datetime import datetime

# Import modules
from config import GOOGLE_CLOUD_ENABLED
from services import (
    get_nutritional_info,
    get_meal_suggestions_from_image,
    get_meal_suggestions_from_text,
    text_to_speech
)
from ui import (
    load_css,
    render_header,
    render_footer,
    render_sidebar,
    display_response,
    display_meal_suggestions
)

# Page configuration
st.set_page_config(
    page_title="Shelfie - AI-Powered Food Analysis",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS styling
load_css()

# Render header
render_header()

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'meal_suggestions_history' not in st.session_state:
    st.session_state.meal_suggestions_history = []

# Create tabs for different features
tab1, tab2 = st.tabs(["📸 Analyze Meal", "🍽️ Get Meal Suggestions"])

# Tab 1: Analyze Meal
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

# Tab 2: Get Meal Suggestions
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
                st.image(ingredients_image, caption="Your Ingredients", use_container_width=True)
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

# Render shared sidebar
render_sidebar()

# Render footer
render_footer()

