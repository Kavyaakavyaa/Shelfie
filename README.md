## Author

Souvik Das
[Link to Profile](https://www.linkedin.com/in/souvik2710/)

---

This advanced nutrition app leverages multiple Google AI services to provide comprehensive meal analysis through image recognition. Users upload food photos and receive detailed nutritional breakdowns including calories, macronutrients, health ratings, and personalized dietary recommendations.

---

# 🍱 AI-Powered Multi-Service Nutritional Analysis Application

This advanced nutrition analysis app leverages multiple Google Cloud AI services to provide intelligent, restaurant-grade meal breakdowns. Users can upload food photos and instantly receive detailed insights including calorie count, macronutrient composition, personalized dietary recommendations, and audio feedback. Designed with accessibility and scalability in mind, the application integrates cutting-edge technologies like Vision AI, Gemini, and BigQuery to deliver a powerful and intuitive experience.

Built with **Streamlit** for seamless user interaction, it empowers health-conscious individuals, fitness enthusiasts, dietitians, and healthcare professionals to make informed decisions about their meals.

---

## 🚀 Key Features

* **Gemini AI**: Delivers professional nutritionist-level analysis with structured outputs.
* **Vision AI**: Advanced object detection for accurate food and ingredient recognition.
* **Multi-language Support**: Translates outputs into 8 languages via Google Translation API.
* **Text-to-Speech**: Converts results into natural-sounding audio for accessibility.
* **BigQuery ML**: Tracks user data trends and enables predictive analytics.
* **Token Logging**: Monitors AI service usage for cost optimization.
* **Voice Input (Framework Ready)**: Future support for hands-free interaction using Speech-to-Text.

---

## 🤖 Integrated Google AI Services

### 1. **Vision AI**

* **Purpose**: Enhanced food detection & ingredient recognition.
* **Implementation**: Uses bounding boxes and confidence scores.
* **Benefit**: Increases accuracy in meal breakdowns.

### 2. **Translation API**

* **Purpose**: Global language accessibility (8+ languages).
* **Implementation**: Translates results based on user preference.
* **Benefit**: Broader user inclusivity and reach.

### 3. **Text-to-Speech**

* **Purpose**: Accessibility through audio output.
* **Implementation**: Converts analysis results to spoken language.
* **Benefit**: Ideal for visually impaired users or audio learners.

### 4. **BigQuery ML**

* **Purpose**: Data storage, tracking, and analytics.
* **Implementation**: Stores historical nutrition data.
* **Benefit**: Enables trend analysis and personalized recommendations.

### 5. **Speech-to-Text (Framework Ready)**

* **Purpose**: Future voice command support.
* **Implementation**: Prepared for seamless voice interaction.
* **Benefit**: Enhances UX with hands-free control.

---

## 🧑‍💼 Target Users

* Dietitians and nutritionists
* Fitness enthusiasts and athletes
* Healthcare professionals
* Health-conscious individuals
* Visually impaired users seeking nutritional guidance

---

## 🛠 Tech Stack

* **Frontend**: Streamlit (Python)
* **Cloud Services**: Google Cloud Platform (Vision AI, Translation API, BigQuery, Text-to-Speech)
* **ML Models**: Gemini AI for structured analysis
* **Deployment**: Ready for local and cloud deployment

---

## 📊 Example Output

* **Calories**: 580 kcal
* **Proteins**: 22g
* **Carbohydrates**: 60g
* **Fats**: 24g
* **Fiber**: 8g
* **Health Rating**: ⭐⭐⭐⭐☆
* **Recommendation**: "Reduce sugar content; add a leafy green for balance."

---

## 🔍 Future Scope

* Voice-based meal input using Speech-to-Text
* Meal planning & daily nutrition tracking
* Integration with fitness trackers and wearable devices
* Export to PDF/CSV for dietician consultation

---

## 📁 How to Run Locally

```bash
git clone https://github.com/your-username/calorie_detection_public.git
pip install -r requirements.txt
streamlit run calorie_detection_max.py
```

---


## ⚡ Quick Start Sequence

Follow these steps carefully to get your AI-powered nutritional analysis app up and running:

1. **Enable Billing on GCP**

   > ℹ️ *Nothing will work until billing is enabled.*

2. **Enable Required APIs**
   Enable the following Google Cloud APIs **before** creating your service account:

   * Vision API
   * Translation API
   * Text-to-Speech API
   * BigQuery API
   * Gemini API (via Vertex AI or PaLM API access)

3. **Create a Service Account**

   * Assign the following roles:

     * `BigQuery Admin`
     * `Vertex AI User` or equivalent for Gemini access
     * `Cloud Translation API User`
     * `Cloud Text-to-Speech API User`
     * `Cloud Vision API User`
   * **Download the JSON key file** for the service account.

4. **Set the Environment Variable**

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"
   ```

5. **Create BigQuery Dataset & Table**

   * Create a dataset in BigQuery (e.g., `nutrition_data`)
   * Define a schema for the table to store meal analysis results.

6. **Run the Test Script**

   * Use the included `test_services.py` or similar test script.
   * Verify each service works as expected (Vision, Translation, TTS, BigQuery, Gemini).

---

## 💡 Pro Tips

* ✅ **Start with Vision API only** – test image recognition before integrating other services.
* 🧪 **Use the test script** to debug and validate each service independently.
* 📌 **Keep your Project ID handy** – you’ll use it multiple times across setup and scripts.
* 💰 **Set billing alerts** – avoid surprise charges by configuring budgets and alerts in the **Billing > Budgets & alerts** section.

---

## 📜 License

[MIT License](LICENSE)

---

## 💬 Feedback & Contributions

We welcome feature suggestions, issue reports, and contributions via pull requests!

---
