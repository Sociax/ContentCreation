import os
import json
from typing import List
from mcp.server.fastmcp import FastMCP
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

# Importar o sistema de autenticação já existente na Sociax (via OAuth)
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from auth_engine import AuthEngineGSC

mcp = FastMCP("Sociax GA4 MCP")

def get_ga4_client() -> BetaAnalyticsDataClient:
    """Inicializa e retorna o cliente do Google Analytics Data usando OAuth."""
    # O cliente buscará as credenciais do token.pickle logado no navegador
    auth = AuthEngineGSC()
    auth.connect()
    return BetaAnalyticsDataClient(credentials=auth.credentials)

@mcp.tool()
def get_ga4_report(
    metrics: List[str],
    dimensions: List[str] = [],
    start_date: str = "30daysAgo",
    end_date: str = "today",
    property_id: str = None
) -> str:
    """
    Busca um relatório no Google Analytics 4.
    
    Args:
        metrics: Lista de métricas do GA4 (ex: "activeUsers", "sessions", "screenPageViews").
        dimensions: Lista de dimensões do GA4 (ex: "city", "date", "pagePath"). Padrão é vazio.
        start_date: Data de início ("YYYY-MM-DD" ou palavras-chave como "30daysAgo", "yesterday", "today"). Padrão: "30daysAgo".
        end_date: Data de término ("YYYY-MM-DD" ou palavras-chave como "today", "yesterday"). Padrão: "today".
        property_id: O ID da Propriedade GA4 (apenas os números). Se não for passado, usará a env var GA4_PROPERTY_ID.
    """
    prop_id = property_id or os.getenv("GA4_PROPERTY_ID")
    if not prop_id:
        return "Erro: O 'property_id' não foi fornecido e a variável GA4_PROPERTY_ID não está configurada no ambiente."

    try:
        client = get_ga4_client()
        
        request = RunReportRequest(
            property=f"properties/{prop_id}",
            dimensions=[Dimension(name=d) for d in dimensions] if dimensions else [],
            metrics=[Metric(name=m) for m in metrics] if metrics else [],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )
        
        response = client.run_report(request)
        
        # Formatar a resposta em dicionários
        results = []
        for row in response.rows:
            row_dict = {}
            for i, dimension_value in enumerate(row.dimension_values):
                row_dict[response.dimension_headers[i].name] = dimension_value.value
            for i, metric_value in enumerate(row.metric_values):
                row_dict[response.metric_headers[i].name] = metric_value.value
            results.append(row_dict)
            
        return json.dumps({
            "status": "success",
            "property_id": prop_id,
            "row_count": response.row_count,
            "data": results
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Carrega as variáveis de ambiente locais caso .env exista (bom para testes locais)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    mcp.run()
