# Shelfie App - Modular Structure

This document describes the refactored modular structure of the Shelfie app.

## File Structure

```
calorie_detection_public-main/
├── main.py                 # Main application entry point
├── config.py              # Configuration and service initialization
├── utils.py               # Utility functions (image encoding, data extraction)
├── services.py            # API services (Gemini, Vision AI, Translation, TTS, BigQuery)
├── ui.py                  # UI components, styling, and display functions
├── calorie_detection_max.py  # Original file (kept for reference)
└── requirements.txt       # Dependencies
```

## Module Descriptions

### `config.py`
- Handles environment variable loading
- Configures logging
- Initializes Google Cloud services (Vision AI, Translation, TTS, BigQuery)
- Initializes Gemini AI model
- Exports configuration constants and clients

### `utils.py`
- `encode_image()` - Converts PIL images to base64 for API transmission
- `extract_nutrition_values()` - Extracts nutritional data from text using regex

### `services.py`
- `vision_ai_analysis()` - Google Vision AI for food detection
- `translate_response()` - Google Translation API
- `text_to_speech()` - Google TTS or pyttsx3 fallback
- `save_to_bigquery()` - Saves analysis data to BigQuery
- `get_nutritional_info()` - Main Gemini AI nutrition analysis
- `get_meal_suggestions_from_image()` - Meal suggestions from ingredient images
- `get_meal_suggestions_from_text()` - Meal suggestions from text ingredients

### `ui.py`
- `load_css()` - Loads premium dark theme CSS
- `render_header()` - Renders app header
- `render_footer()` - Renders app footer
- `render_sidebar()` - Renders sidebar with features and history
- `display_response()` - Displays nutritional analysis results
- `display_meal_suggestions()` - Displays meal suggestions

### `main.py`
- Main Streamlit application entry point
- Imports and orchestrates all modules
- Handles tab navigation
- Manages session state
- Coordinates UI and service calls

## Running the App

To run the refactored app:

```bash
streamlit run main.py
```

The original file `calorie_detection_max.py` is preserved for reference but is no longer the main entry point.

## Benefits of Modular Structure

1. **Separation of Concerns**: Each module has a single, clear responsibility
2. **Maintainability**: Easier to find and modify specific functionality
3. **Testability**: Individual modules can be tested independently
4. **Reusability**: Functions can be imported and reused in other projects
5. **Readability**: Cleaner, more organized codebase
6. **Scalability**: Easy to add new features or services

## Migration Notes

- All functionality from `calorie_detection_max.py` is preserved
- UI and user experience remain identical
- No breaking changes to existing features
- The original file is kept for reference but not used

