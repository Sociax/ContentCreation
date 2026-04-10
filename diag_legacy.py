import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def diagnostic_generativeai():
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Try different ways to access 1.5-flash
    attempts = [
        "gemini-1.5-flash",
        "models/gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "models/gemini-1.5-flash-latest",
        "gemini-pro", # Baseline
    ]
    
    print("Testing google-generativeai models...")
    for m in attempts:
        print(f"Testing {m}...", end=" ", flush=True)
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content("Hi")
            print(f"✅ SUCCESS: {response.text[:20]}...")
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")

if __name__ == "__main__":
    diagnostic_generativeai()
