import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini_15_connection():
    print("Iniciando teste de conexão com Gemini 1.5 Flash...")
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = "Teste de conexão Sociax. Responda 'OK'."
        print(f"Enviando prompt: {prompt}")
        
        response = model.generate_content(prompt)
        print("\n--- Resposta ---")
        print(response.text)
        print("----------------\n")
        print("✅ Conexão com Gemini 1.5 Flash estabelecida!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_gemini_15_connection()
