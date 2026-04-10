import os
from ai_engine import AIEngineGemini
from dotenv import load_dotenv

def test_gemini_connection():
    print("Iniciando teste de conexão com Gemini API...")
    load_dotenv()
    
    try:
        ai = AIEngineGemini()
        print(f"Modelo configurado: {ai.model_id}")
        
        prompt = "Olá Gemini, este é um teste de conexão do sistema Sociax Analytics. Por favor, responda com uma saudação curta em Português do Brasil."
        print(f"Enviando prompt: {prompt}")
        
        response = ai._safe_generate(prompt)
        
        print("\n--- Resposta do Gemini ---")
        print(response)
        print("--------------------------\n")
        
        if "Erro" in response or "⚠️" in response:
            print("❌ O teste falhou ou retornou um erro.")
        else:
            print("✅ Conexão estabelecida com sucesso!")
            
    except Exception as e:
        print(f"❌ Ocorreu um erro durante o teste: {e}")

if __name__ == "__main__":
    test_gemini_connection()
