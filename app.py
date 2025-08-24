from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize API key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("API key is missing. Set GOOGLE_API_KEY as an environment variable.")

# Initialize Gemini client
try:
    client = genai.Client(api_key=API_KEY)
    logger.info("Gemini client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini client: {e}")
    raise

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route("/get-country", methods=["POST"])
def get_country():
    """
    Extract country code from natural language description.
    
    Expected JSON payload:
    {
        "message": "Description of a country"
    }
    
    Returns:
    {
        "country_code": "USA",
        "success": true
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON", "success": False}), 400
        
        data = request.json
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"error": "Message field is required", "success": False}), 400
        
        logger.info(f"Processing request: {user_input}")
        
        # Create enhanced prompt
        prompt = f"""
        Extract the ISO 3166-1 alpha-3 country code from the description below.
        - Return ONLY the three-letter country code (e.g., USA, GBR, FRA)
        - If multiple countries match, return the most relevant one
        - If no country can be identified, return 'NONE'
        - Do not include any explanation or additional text
        Description: {user_input}
        """
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        country_code = response.text.strip().upper()
        
        # Validate response
        if len(country_code) != 3 or country_code == 'NONE':
            logger.warning(f"No valid country code found for: {user_input}")
            return jsonify({
                "country_code": None, 
                "success": False,
                "message": "No country identified"
            })
        
        logger.info(f"Successfully identified country: {country_code}")
        return jsonify({
            "country_code": country_code,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({
            "error": "Internal server error",
            "success": False
        }), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "LLM Map API"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(debug=True, host="0.0.0.0", port=port)