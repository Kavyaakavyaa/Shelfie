🥗 Shelfie — AI-Powered Nutrition & Meal Recommendation System

Shelfie is an AI-driven nutrition analysis application that provides detailed calorie and macronutrient breakdowns from food images and suggests balanced meals based on daily goals and nutritional needs. Built with Google Cloud AI services and Streamlit, Shelfie combines accurate food recognition, structured analysis, and an intuitive interface.

⸻

🚀 Core Features

1. AI-Based Calorie & Nutrition Analysis

Shelfie uses Google Vision AI and Gemini to:
	•	Detect ingredients from uploaded food images
	•	Generate structured nutritional breakdowns
	•	Provide calories, macros (protein, carbs, fats), health ratings, and improvement suggestions

2. Intelligent Meal Suggestions

Meal recommendations are generated based on:
	•	User’s daily calorie targets
	•	Nutrient gaps (e.g., protein, fiber)
	•	Previous meals and patterns
	•	Balanced, high-protein, and low-calorie options

⸻

🤖 Integrated Google Cloud Services
	•	Vision AI — Ingredient detection from food photos
	•	Gemini AI — Structured nutrition analysis
	•	Translation API — Multi-language support
	•	Text-to-Speech API — Audio-based feedback
	•	BigQuery ML — Storage, analytics, and trend modeling
	•	Speech-to-Text (Planned) — Future voice-based inputs

⸻

🛠 Tech Stack
	•	Frontend: Streamlit
	•	Cloud & AI: Google Cloud (Vision, Translation, Text-to-Speech, BigQuery, Gemini)
	•	ML Model: Gemini
	•	Deployment: Local and cloud-compatible

⸻

📊 Example Output (AI Analysis)
	•	Calories: 580 kcal
	•	Protein: 22g
	•	Carbs: 60g
	•	Fats: 24g
	•	Health Rating: ⭐⭐⭐⭐⭐
	•	Recommendation: “Add a leafy green to improve micronutrient balance.”

⸻

📁 Run Locally

git clone https://github.com/Kavyaakavyaa/Shelfie.git
pip install -r requirements.txt
streamlit run calorie_detection_max.py


⸻

⚙️ Setup Instructions
	1.	Enable billing on Google Cloud
	2.	Enable the required APIs: Vision, Translation, Text-to-Speech, BigQuery, Gemini
	3.	Create a Service Account → assign the necessary roles
	4.	Download the JSON key file
	5.	Export the credentials:

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

	6.	Create BigQuery dataset and tables
	7.	Use the included test script to validate API access

⸻

🔮 Future Enhancements
	•	Automated meal planner
	•	Daily nutrition trend visualization
	•	Wearable device integration
	•	Export reports (PDF/CSV) for dietitians

⸻

📜 License

MIT License

⸻

💬 Contributions

Contributions, issues, and feature requests are welcome.

