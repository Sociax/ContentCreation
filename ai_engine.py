import os
import google.generativeai as genai
from dotenv import load_dotenv
import trafilatura
from bs4 import BeautifulSoup
import requests
import json
import base64
from io import BytesIO
from PIL import Image
from urllib.parse import urljoin, urlparse
from google.api_core import retry, exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pytrends.request import TrendReq
import time

load_dotenv()

class AIEngineGemini:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY não configurada no ambiente.")
        
        # type: ignore is needed because google.generativeai doesn't export these explicitly in its stubs
        genai.configure(api_key=self.api_key) # type: ignore
        # Usando gemini-flash-latest (1.5 Flash) para maior estabilidade e compatibilidade de alias
        self.model_id = "gemini-flash-latest"
        self.model = genai.GenerativeModel(self.model_id) # type: ignore

    def _safe_generate(self, prompt, image=None):
        """Helper centralizado para geração de conteúdo com tratamento robusto de erro 429 e retentativas."""
        max_retries = 5
        base_delay = 5  # segundos
        
        for attempt in range(max_retries):
            try:
                if image:
                    response = self.model.generate_content([prompt, image])
                else:
                    response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                err_msg = str(e)
                is_quota_error = "429" in err_msg or "ResourceExhausted" in err_msg or "quota" in err_msg.lower()
                
                if is_quota_error and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    # Adiciona log no terminal para transparência
                    print(f"⚠️ Quota Gemini atingida. Tentativa {attempt + 1}/{max_retries}. Aguardando {delay}s...")
                    time.sleep(delay)
                    continue
                
                if is_quota_error:
                    return "⚠️ Erro 429: Limite de cota do Google Gemini atingido após várias tentativas automáticas. Por favor, aguarde cerca de 1 minuto e tente novamente."
                return f"Erro na camada de IA Sociax: {err_msg}"

    def run_seo_analysis(self, df, site_context=""):
        if df.empty: return "Sem dados para análise."
        summary = df.head(100).to_markdown()
        prompt = f"""
        Analise estes dados do GSC para o site {site_context}:
        {summary}
        
        Identifique:
        1. Principais tendências de performance.
        2. Oportunidades imediatas de SEO (CTR baixo, impressões altas).
        3. Recomendações estratégicas.
        
        IMPORTANTE: Responda inteiramente em Português do Brasil (PT-BR).
        """
        return self._safe_generate(prompt)

    def chat(self, query, df):
        summary = df.head(150).to_markdown()
        prompt = f"Contexto GSC:\n{summary}\n\nPergunta do Usuário: {query}\n\nResponda em Português do Brasil (PT-BR) de forma profissional e direta."
        return self._safe_generate(prompt)

    def analyze_content(self, url, keyword):
        """Analisa uma URL para dar nota ao conteúdo e sugerir otimizações baseadas em uma palavra-chave."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return "Erro: Não foi possível carregar o conteúdo da URL fornecida."
            
            text_content = trafilatura.extract(downloaded)
            
            if not text_content:
                return "Erro: Não foi possível extrair o texto."

            soup = BeautifulSoup(downloaded, 'html.parser')
            
            # Extract basic SEO elements
            title = soup.title.string if soup.title else "N/D"
            h1s = [h1.get_text() for h1 in soup.find_all('h1')]
            
            prompt = f"""
            Sistema: Analista de Conteúdo SEO (Foco em Eficiência de Capital)
            Palavra-Chave Alvo: {keyword}
            URL: {url}
            
            Tag Title: {title}
            Tags H1: {h1s}
            
            Resumo do Conteúdo (Texto Extraído):
            {text_content[:4000]}

            Tarefa:
            1. Forneça uma 'Pontuação de Conteúdo' de 0-100 (Perspectiva de Disciplina Financeira: quão bem converte o 'Capital de Busca').
            2. Analise a Presença da Palavra-Chave (Relevância Semântica).
            3. Otimizações Detalhadas (Title, Headers, Body, Links Internos).
            4. Formatação: Use markdown profissional e estruturado.
            
            IMPORTANTE: Responda inteiramente em Português do Brasil (PT-BR).
            """
            return self._safe_generate(prompt)
        except Exception as e:
            return f"Erro na análise: {str(e)}"

    def get_cwv_metrics(self, url):
        """Fetches Core Web Vitals data from PageSpeed Insights API (CrUX and Lighthouse)."""
        base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        api_key = os.getenv("PAGESPEED_API_KEY") or self.api_key
        params = {
            "url": url,
            "key": api_key,
            "category": ["PERFORMANCE", "SEO"],
            "strategy": "mobile" # Standard for CWV
        }
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if "error" in data:
                return {"status": "error", "message": data["error"].get("message", "Erro desconhecido na API")}

            # Extract CrUX metrics (Field Data) if available
            loading_experience = data.get("loadingExperience", {})
            metrics = loading_experience.get("metrics", {})
            
            # Extract LH (Lab Data)
            lh_res = data.get("lighthouseResult", {})
            lh_score = lh_res.get("categories", {}).get("performance", {}).get("score", 0) * 100
            
            # Extract Lab Metrics specifically for fallback
            audits = lh_res.get("audits", {})
            lab_metrics = {
                "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/D"),
                "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/D"),
                "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/D"),
                "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/D"),
            }
            
            return {
                "status": "success",
                "metrics": metrics,
                "lh_score": lh_score,
                "lab_metrics": lab_metrics,
                "full_data": data
            }
        except Exception as e:
            return {"status": "error", "message": f"Erro de conexão API: {str(e)}"}

    def analyze_cwv(self, url, cwv_data):
        """Uses AI to interpret CWV metrics and suggest technical fixes."""
        metrics = cwv_data.get("metrics", {})
        score = cwv_data.get("lh_score", 0)
        
        # Simplified metrics for the prompt
        m_str = "\n".join([f"- {k}: {v.get('percentile', 'N/D')} ({v.get('category', 'N/D')})" for k, v in metrics.items()])
        
        prompt = f"""
        Sistema: Engenheiro Sênior de Performance Web (Foco em Disciplina Financeira)
        URL Alvo: {url}
        Pontuação de Performance (Lab): {score}/100
        Métricas de Usuários Reais (CrUX):
        {m_str}

        Tarefa:
        1. Interprete estas métricas através da lente de 'Eficiência de Capital'. Como a velocidade afeta o resultado financeiro do projeto?
        2. Identifique os maiores gargalos (LCP, CLS ou INP).
        3. Forneça um 'Roteiro Técnico Tático' com 3 a 5 correções de alto impacto.
        4. Saída em Markdown profissional e estruturado.
        
        IMPORTANTE: Responda inteiramente em Português do Brasil (PT-BR).
        """
        return self._safe_generate(prompt)

    def scrape_url_seo(self, url):
        """Scrapa uma URL usando Selenium com fallback de User-Agent em 3 estágios."""
        def get_driver(ua):
            from shutil import which
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f'user-agent={ua}')
            
            # Verificação para Streamlit Cloud
            binary_loc = which("chromium") or which("chromium-browser") or which("google-chrome")
            if binary_loc:
                options.binary_location = binary_loc
                
            driver_loc = which("chromedriver") or which("chromium-driver")
            if driver_loc:
                service = ChromeService(executable_path=driver_loc)
            else:
                service = ChromeService(ChromeDriverManager().install())
                
            return webdriver.Chrome(service=service, options=options)

        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36', # Standard
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', # Googlebot
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36' # Chrome Desktop Fresh
        ]

        driver = None
        last_error = ""
        
        try:
            if not url.startswith('http'):
                url = 'https://' + url
            
            for i, ua in enumerate(user_agents):
                if driver: driver.quit()
                driver = get_driver(ua)
                try:
                    driver.get(url)
                    time.sleep(3) # Wait for JS
                    
                    page_source = driver.page_source
                    title = driver.title.lower()
                    
                    # Detect block
                    is_blocked = any(term in page_source or term in title for term in ["forbidden", "access denied", "cloudflare", "captcha", "security check"])
                    
                    if not is_blocked:
                        break # Success!
                    else:
                        last_error = f"Bloqueio detectado com UA {i+1}"
                except Exception as e:
                    last_error = str(e)
                    continue

            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Meta Tags
            title_text = soup.find('title').text if soup.find('title') else driver.title
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc['content'] if meta_desc else "N/D"
            
            # Headers
            headers_structure = {
                "h1": [h.text.strip() for h in soup.find_all('h1')],
                "h2": [h.text.strip() for h in soup.find_all('h2')[:10]],
                "h3": [h.text.strip() for h in soup.find_all('h3')[:10]],
            }
            
            # Schema extraction
            schemas = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    schemas.append(json.loads(script.string))
                except: pass

            return {
                "url": url,
                "title": title_text,
                "description": description,
                "headers": headers_structure,
                "schemas": schemas,
                "status": "success",
                "attempt": i + 1
            }
        except Exception as e:
            return {"url": url, "status": "error", "message": f"Erro final após tentativas: {last_error or str(e)}"}
        finally:
            if driver:
                driver.quit()

    def parse_html_seo(self, html_content, source_label="Código Manual"):
        """Extrai elementos de SEO de um código HTML fornecido manualmente."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Meta Tags
            title_text = soup.find('title').text if soup.find('title') else "N/D"
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc['content'] if meta_desc else "N/D"
            
            # Headers
            headers_structure = {
                "h1": [h.text.strip() for h in soup.find_all('h1')],
                "h2": [h.text.strip() for h in soup.find_all('h2')[:10]],
                "h3": [h.text.strip() for h in soup.find_all('h3')[:10]],
            }
            
            # Schema extraction
            schemas = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    schemas.append(json.loads(script.string))
                except: pass

            return {
                "url": source_label,
                "title": title_text,
                "description": description,
                "headers": headers_structure,
                "schemas": schemas,
                "status": "success",
                "attempt": "manual"
            }
        except Exception as e:
            return {"url": source_label, "status": "error", "message": f"Erro no Parse: {str(e)}"}

    def compare_urls_logic(self, kw, data_list):
        """Usa Gemini para comparar múltiplas URLs sob a ótica de SEO."""
        prompt = f"""
        Você é um Consultor de SEO Sênior da Sociax.
        Realize uma análise comparativa profunda para a palavra-chave: "{kw}".
        
        DADOS DAS PÁGINAS:
        {json.dumps(data_list, indent=2)}
        
        TAREFA:
        1. Crie uma TABELA DE COMPARAÇÃO inicial com as principais diferenças técnicas (Title, Descrição, H1, Presença de Schema, JS-Rendering).
        2. Compare o alinhamento de títulos e metas.
        3. Avalie a hierarquia de headers e fluxo semântico.
        4. Analise o uso de Schema e oportunidades de Rich Results.
        5. Explique por que a página melhor posicionada está vencendo.
        6. Forneça um veredito estratégico e recomendações de 'Eficiência de Capital'.
        
        Responda em PT-BR com markdown profissional.
        """
        return self._safe_generate(prompt)

    def analyze_internal_linking_logic(self, all_data, target_urls):
        """Analisa a estratégia de links internos entre um grupo de páginas."""
        prompt = f"""
        Analise a estratégia de interlinkagem para este conjunto de URLs: {target_urls}
        
        DADOS:
        {json.dumps(all_data, indent=2)}
        
        TAREFA:
        1. Avalie a força do silo/cluster.
        2. Analise a qualidade das âncoras.
        3. Identifique páginas isoladas e oportunidades de interconexão.
        4. Forneça recomendações práticas para maximizar o 'Capital de Linkagem'.
        
        Responda em PT-BR em formato markdown.
        """
        return self._safe_generate(prompt)

    def get_page_images(self, url):
        """Scrapa imagens de uma URL filtrando logos e ícones."""
        try:
            # Use Trafilatura for more reliable content fetching
            downloaded = trafilatura.fetch_url(url)
            if not downloaded: return []
            soup = BeautifulSoup(downloaded, 'html.parser')
            exclude = ['logo', 'icon', 'svg', 'avatar', 'social', 'button', 'arrow']
            img_data = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt = img.get('alt', '')
                if any(kw in src.lower() for kw in exclude) or not src: continue
                img_data.append({"src": urljoin(url, src), "alt": alt})
            return img_data
        except: return []

    def analyze_image_alt_logic(self, img_src, current_alt, keyword, intent):
        """Usa IA para otimizar o Alt text de uma imagem."""
        try:
            img_res = requests.get(img_src, timeout=10)
            img = Image.open(BytesIO(img_res.content))
            
            prompt = f"""
            Analise esta imagem para SEO:
            - Palavra-Chave Alvo: {keyword}
            - Intenção da Página: {intent}
            - Alt Atual: "{current_alt}"
            
            Proponha um Alt text otimizado (PT-BR) em formato JSON:
            {{ "is_best": bool, "reasoning": "string", "proposed_alt": "string" }}
            """
            text = self._safe_generate(prompt, img)
            if "Erro" in text: return {"error": text}
            
            # Clean up potential markdown formatting from AI
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text: text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            return {"error": str(e)}

    def extract_hreflangs(self, url):
        """Extrai tags hreflang de uma página."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded: return []
            soup = BeautifulSoup(downloaded, 'html.parser')
            tags = []
            for link in soup.find_all('link', rel='alternate'):
                if link.get('hreflang') and link.get('href'):
                    tags.append({'hreflang': link.get('hreflang'), 'href': urljoin(url, link.get('href'))})
            return tags
        except: return []

    def analyze_schema_logic(self, data):
        """Audita dados de Schema."""
        prompt = f"Você é um especialista em SEO técnico da Sociax. Audite os seguintes dados de SCHEMA e sugira melhorias para Rich Snippets: {json.dumps(data)} em PT-BR"
        return self._safe_generate(prompt)

    def analyze_headers_logic(self, kw, data):
        """Analise headers semanticamente."""
        prompt = f"Você é um estrategista de conteúdo da Sociax. Analise a hierarquia e relevância dos seguintes headers para a palavra-chave '{kw}': {json.dumps(data)} em PT-BR"
        return self._safe_generate(prompt)

    def _fetch_google_trends(self, keyword):
        """Busca dados em tempo real do Google Trends para a palavra-chave alvo."""
        try:
            pytrends = TrendReq(hl='pt-BR', tz=-180, timeout=(10, 25))
            pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo='BR')
            
            related = pytrends.related_queries()
            kw_data = related.get(keyword, {})
            
            top_queries = []
            rising_queries = []
            
            if kw_data.get('top') is not None and not kw_data['top'].empty:
                top_queries = kw_data['top']['query'].head(10).tolist()
            if kw_data.get('rising') is not None and not kw_data['rising'].empty:
                rising_queries = kw_data['rising']['query'].head(10).tolist()

            return {
                "top_queries": top_queries,
                "rising_queries": rising_queries
            }
        except Exception as e:
            print(f"⚠️ Google Trends indisponível para '{keyword}': {e}")
            return None

    def generate_blog_content(self, client_data, keyword, style, keyword_average, additional_notes="", intent="Informativo", kw_type="Short tail", content_format="Blog post content"):
        """
        Gera um conteúdo otimizado para SEO com dados reais do Google Trends.
        """
        notes_section = f"\n        OBSERVAÇÕES ADICIONAIS DO USUÁRIO:\n        - {additional_notes}\n" if additional_notes.strip() else ""
        
        # Fetch live Google Trends data
        trends_data = self._fetch_google_trends(keyword)
        if trends_data:
            trends_section = f"""
        DADOS EM TEMPO REAL DO GOOGLE TRENDS (Brasil, Últimos 3 meses):
        - Buscas Relacionadas mais Populares (Top): {', '.join(trends_data['top_queries']) or 'N/D'}
        - Buscas em Ascensão / Breakout Topics: {', '.join(trends_data['rising_queries']) or 'N/D'}
        INSTRUCAO: Baseie a "Visão de Busca" e os subtemas do artigo nestes dados reais acima. Não invente ou simule tendências.
        """
        else:
            trends_section = "\n        AVISO: Google Trends indisponível no momento. Use seu melhor julgamento sobre as tendências atuais para esta palavra-chave.\n"
        
        prompt = f"""
        Você é um Especialista Sênior em Conteúdo e SEO. Seu objetivo é criar um material de altíssima qualidade 
        no formato "{content_format}" que posicione o cliente como autoridade no setor. A palavra-chave foco é: "{keyword}".

        DADOS DO CLIENTE E DO CONTEÚDO:
        - Nome: {client_data['name']}
        - Descrição: {client_data['desc']}
        - Website: {client_data['url']}
        - Intenção de Busca do Conteúdo: {intent}
        - Tipo de Palavra-Chave: {kw_type}
        - Formato Exigido: {content_format}
        {trends_section}
        {notes_section}
        DIRETRIZES TÉCNICAS E REGRAS INEGOCIÁVEIS:
        1. Visão de Busca: Dedique a primeira seção para explicar a intenção de busca e como os dados do Google Trends acima confirmam essa tendência.
        2. Estrutura Obrigatória: Crie um Outline claro (H1 título principal, H2 subtítulos, H3 detalhamentos).
        3. Storytelling Orientado a Dados: O conteúdo DEVE incorporar os temas em ascensão do Google Trends com dados concretos (cite fontes factíveis de 2025/2026). PROIBIDO conteúdo genérico.
        4. Mobile-first: ABSOLUTAMENTE NENHUM parágrafo pode ter mais do que 3 frases.
        5. Analogias Simples: Se houver termos técnicos complexos, explique-os usando analogias do dia a dia.
        6. Proibição de Clichês: NUNCA use expressões como "No mundo dinâmico de hoje", "Na era digital", "Em um cenário em constante evolução".
        7. Conclusão e CTA: Finalize com uma forte Chamada para Ação (CTA) embutindo o link do cliente de forma natural.
        8. Sumário Técnico: No final, adicione um sumário simulando:
           - Lacunas de concorrentes batidas.
           - Densidade da Palavra-Chave (seo_check_score).
        9. Média de Palavra-Chave: A palavra-chave principal DEVE aparecer em média cerca de {keyword_average} vezes ao longo do texto.

        DIRETRIZ DE ESTILO DE ESCRITA ESPERADO:
        O tom do texto deve seguir exatamente este estilo: **{style}**
        - Se Educativo: Foco em tutorial passo-a-passo e guias práticos "Como Fazer".
        - Se Provocativo: Quebre paradigmas, questione o status quo do mercado em tom de opinião contundente.
        - Se Data-Driven: Seja extremamente analítico, focado em métricas de performance, com tom corporativo.

        REQUISITO DE SAÍDA:
        Responda integralmente em Markdown (PT-BR). Comece direto com a resposta, sem saudações.
        Obrigatório: No início da resposta, inclua uma seção de Metadados de SEO formatada assim:
        **Meta Title:** (título otimizado, até 60 chars)
        **Meta Description:** (descrição chamativa com CTA, até 160 chars)
        **Slug:** (slug-curto-e-otimizado)
        
        Logo após essa seção, inicie o conteúdo estruturado.
        """
        return self._safe_generate(prompt)
