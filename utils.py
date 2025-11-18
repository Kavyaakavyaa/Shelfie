"""
Utility functions for image processing and data extraction.
"""
import base64
import io
import re
from PIL import Image


def encode_image(image):
    """Encode PIL image to base64 string for API transmission."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def extract_nutrition_values(text):
    """Extract numerical values from nutrition text for BigQuery storage."""
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

