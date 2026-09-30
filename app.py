import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for the React frontend
CORS(app)

# Configure Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

@app.route('/api/generate-itinerary', methods=['POST'])
def generate_itinerary():
    if not API_KEY:
        return jsonify({"error": "Gemini API key is not configured on the server."}), 500

    data = request.json
    destination = data.get('destination')
    days = data.get('days')
    interests = data.get('interests')

    if not destination or not days:
        return jsonify({"error": "Destination and days are required."}), 400

    try:
        # Prompt definition
        prompt = f"""
        Create a detailed, day-by-day travel itinerary for {days} days to {destination}.
        The traveler is interested in: {interests if interests else 'General sightseeing, popular attractions, and local food'}.

        Return the itinerary EXACTLY as a JSON array of objects, where each object represents a day.
        Each day object must have the following structure:
        {{
            "day": 1,
            "title": "A short, catchy title for the day",
            "activities": [
                {{
                    "time": "Morning",
                    "location": "Name of the place",
                    "description": "A brief description of what to do there."
                }},
                {{
                    "time": "Afternoon",
                    "location": "Name of the place",
                    "description": "A brief description of what to do there."
                }},
                {{
                    "time": "Evening",
                    "location": "Name of the place",
                    "description": "A brief description of what to do there."
                }}
            ],
            "tip": "A helpful tip for the day"
        }}
        
        Do not include any markdown formatting like ```json or anything else outside the array. Return just the JSON array.
        """

        model = genai.GenerativeModel('gemini-3.5-flash-lite')
        response = model.generate_content(prompt)
        
        import re
        text = response.text.strip()
        # Find the first '[' and last ']' to extract just the array
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)
        else:
            raise ValueError("No JSON array found in response")

        # Parse JSON to ensure it's valid before sending it back
        itinerary_data = json.loads(text)
        
        return jsonify({"itinerary": itinerary_data})

    except json.JSONDecodeError as e:
        print(f"Failed to parse Gemini response as JSON: {e}")
        print(f"Raw response: {response.text}")
        return jsonify({"error": "Failed to parse itinerary from AI response."}), 500
    except Exception as e:
        print(f"Error generating itinerary: {e}")
        return jsonify({"error": str(e)}), 500

def _get_mock_itinerary(destination, days):
    try:
        days_int = int(days)
    except:
        days_int = 3
        
    itinerary = []
    for day in range(1, days_int + 1):
        itinerary.append({
            "day": day,
            "title": f"Exploring {destination} - Day {day}",
            "activities": [
                {
                    "time": "Morning",
                    "location": "City Center",
                    "description": "Start your day with a walking tour of the main attractions."
                },
                {
                    "time": "Afternoon",
                    "location": "Local Museum",
                    "description": "Dive into the history and culture of the area."
                },
                {
                    "time": "Evening",
                    "location": "Popular Restaurant",
                    "description": "Enjoy traditional local cuisine and relax."
                }
            ],
            "tip": "Wear comfortable shoes for walking!"
        })
    return itinerary

if __name__ == '__main__':
    app.run(debug=True, port=5000)
