"""
UI components and styling module for Shelfie app.
Handles all UI rendering, CSS styling, and display functions.
"""
import streamlit as st
from services import translate_response, save_to_bigquery
from utils import extract_nutrition_values
from config import GOOGLE_CLOUD_ENABLED


def load_css():
    """Load and apply premium dark theme CSS"""
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


def render_header():
    """Render the main app header"""
    st.markdown("""
        <div class="main-header">
            <div class="app-title">📱 Shelfie</div>
            <div class="app-subtitle">
                Advanced AI-powered food analysis. Get instant nutritional insights, calorie tracking, and personalized dietary recommendations from your food photos.
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the app footer"""
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; padding: 2.5rem 0; color: #64748b; font-size: 0.9rem; line-height: 1.8;'>
            <p style='margin: 0.5rem 0; font-weight: 500; color: #94a3b8;'>Multi-AI Powered Nutrition Analysis</p>
            <p style='margin: 0.5rem 0; color: #64748b;'>Gemini AI • Vision AI • Translation • Text-to-Speech • BigQuery</p>
            <p style='margin: 1rem 0 0 0; font-size: 0.85rem; color: #475569;'>Built with precision for your health journey</p>
        </div>
    """, unsafe_allow_html=True)


def display_response(response, vision_data=None, target_language='en'):
    """Display nutritional analysis response"""
    st.markdown("""
        <div class="premium-card" style="margin-top: 2rem;">
            <div class="card-title">🥗 Professional Nutritional Analysis</div>
    """, unsafe_allow_html=True)
    try:
        response_text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                response_text += part.text
        
        # Translate if needed
        if target_language != 'en':
            response_text = translate_response(response_text, target_language)
        
        # Enhanced display with better formatting
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
        
        # Display Vision AI results if available
        if vision_data and vision_data['objects']:
            with st.expander("🤖 Vision AI Detection Results"):
                st.write("**Detected Food Objects:**")
                for obj in vision_data['objects']:
                    st.write(f"- {obj['name']} (Confidence: {obj['confidence']:.2f})")
        
        # Extract nutritional values for BigQuery
        nutrition_values = extract_nutrition_values(response_text)
        nutrition_values['text'] = response_text
        
        # Save to BigQuery
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
        st.markdown("</div>", unsafe_allow_html=True)
        return None, None


def display_meal_suggestions(response, target_language='en'):
    """Display meal suggestions in a formatted way"""
    st.markdown("""
        <div class="premium-card" style="margin-top: 2rem;">
            <div class="card-title">🍽️ Meal Suggestions</div>
    """, unsafe_allow_html=True)
    
    try:
        response_text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                response_text += part.text
        
        # Translate if needed
        if target_language != 'en':
            response_text = translate_response(response_text, target_language)
        
        # Enhanced display with better formatting
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


def render_sidebar():
    """Render the sidebar with features, tips, and history"""
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

