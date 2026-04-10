from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
from ai_engine import AIEngineGemini

load_dotenv()

app = FastAPI(title="Sociax API Gateway", description="API para integração com n8n e outras ferramentas de automação.")

# Security
API_KEY = os.getenv("SOCIAX_API_KEY", "sociax_secret_2024")

async def verify_token(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Chave de API inválida.")

# Engine initialization
ai = AIEngineGemini()

# Models
class ContentRequest(BaseModel):
    url: str
    keyword: str

class CWVRequest(BaseModel):
    url: str

class CompareRequest(BaseModel):
    keyword: str
    urls: List[str]

@app.get("/")
def home():
    return {"status": "online", "message": "Sociax API Gateway está rodando."}

@app.post("/report/content", dependencies=[Depends(verify_token)])
def analyze_content_api(req: ContentRequest):
    """Gera um relatório de otimização de conteúdo."""
    result = ai.analyze_content(req.url, req.keyword)
    return {"status": "success", "report": result}

@app.post("/report/cwv", dependencies=[Depends(verify_token)])
def analyze_cwv_api(req: CWVRequest):
    """Gera um relatório de performance (CWV)."""
    metrics = ai.get_cwv_metrics(req.url)
    if metrics["status"] == "error":
        raise HTTPException(status_code=500, detail=metrics["message"])
    
    report = ai.analyze_cwv(req.url, metrics)
    return {
        "status": "success", 
        "score": metrics["lh_score"],
        "metrics": metrics["lab_metrics"],
        "report": report
    }

@app.post("/report/compare", dependencies=[Depends(verify_token)])
def compare_urls_api(req: CompareRequest):
    """Compara múltiplas URLs sob a ótica de SEO."""
    if len(req.urls) < 2:
        raise HTTPException(status_code=400, detail="Forneça pelo menos 2 URLs para comparação.")
    
    data_list = []
    for url in req.urls:
        data_list.append(ai.scrape_url_seo(url))
    
    report = ai.compare_urls_logic(req.keyword, data_list)
    return {"status": "success", "report": report}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
