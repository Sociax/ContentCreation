import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pandas as pd

# SCOPES for Google Search Console and Google Analytics APIs
SCOPES = [
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

class AuthEngineGSC:
    def __init__(self, client_secrets_file='client_secret.json', token_file='sociax_token_v2.pickle'):
        # Use absolute paths relative to this file's directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.client_secrets_file = os.path.join(base_path, client_secrets_file)
        self.token_file = os.path.join(base_path, token_file)
        self.credentials = None
        self.service = None

    def connect(self):
        """Authenticates and builds the Search Console service."""
        try:
            import streamlit as st
            from google.oauth2.credentials import Credentials
            import json
            
            # Debug: avisar se o arquivo secrets.toml existe no ambiente da nuvem
            if hasattr(st, "secrets"):
                if "gcp_oauth_credentials" in st.secrets:
                    creds_info = st.secrets["gcp_oauth_credentials"]
                    if isinstance(creds_info, str):
                        creds_info = json.loads(creds_info)
                    # Forçar conversão de TOML dict para plain dict caso necessário
                    temp_creds = Credentials.from_authorized_user_info(dict(creds_info))
                    
                    # Verificar se o token atual possui todos os scopes necessários
                    has_all_scopes = all(s in (temp_creds.scopes or []) for s in SCOPES)
                    if has_all_scopes:
                        self.credentials = temp_creds
                    else:
                        st.info("🔄 Novos recursos detectados. É necessário re-autenticar para liberar o Google Docs.")
                else:
                    st.warning("⚠️ Chave 'gcp_oauth_credentials' não foi encontrada dentro do st.secrets. Verifique se você salvou corretamente no painel do Streamlit Cloud.")
        except Exception as e:
            pass # Silencioso para permitir fallback local

        # Melhor detecção de ambiente Nuvem vs Local
        is_cloud = os.getenv("STREAMLIT_SHARING_MODE") is not None or os.getenv("HOME") == "/home/appuser"
        
        if not self.credentials and os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            except: pass
        
        # Validar e renovar credenciais
        if self.credentials:
            # Se expirado mas tem refresh_token, renovar diretamente
            if self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                except:
                    self.credentials = None # Forçar re-login se falhar refresh

        if not self.credentials or not self.credentials.valid:
            if is_cloud:
                st.error("🔒 **Sessão não iniciada**: O token de acesso do Google não foi encontrado nos Secrets.")
                st.markdown("""
                ### Como configurar na Nuvem:
                1. Rode o app localmente e faça login.
                2. Gere o JSON do token atualizado.
                3. Cole no painel de **Secrets** do Streamlit Cloud.
                """)
                st.stop()
            else:
                # Fluxo local: Buscar client_secret.json
                if not os.path.exists(self.client_secrets_file):
                    if os.path.exists('client_secret.json'):
                        self.client_secrets_file = os.path.abspath('client_secret.json')
                    else:
                        st.error(f"❌ Arquivo `{self.client_secrets_file}` não encontrado.")
                        st.info("Para rodar localmente, você precisa do arquivo `client_secret.json` na raiz do projeto.")
                        st.stop()
                
                with st.spinner("Aguardando autorização no navegador..."):
                    flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                    
                    # Salvar token atualizado localmente
                    try:
                        with open(self.token_file, 'wb') as token:
                            pickle.dump(self.credentials, token)
                        st.success("✅ Token salvo localmente!")
                    except: pass

        self.service = build('webmasters', 'v3', credentials=self.credentials)
        return self.service

    def get_properties(self):
        if not self.service: self.connect()
        site_list = self.service.sites().list().execute()
        return [site['siteUrl'] for site in site_list.get('siteEntry', [])]

    def fetch_analytics(self, site_uri, start, end, dims=['query'], limit=2000):
        if not self.service: self.connect()
        request = {
            'startDate': start,
            'endDate': end,
            'dimensions': dims,
            'rowLimit': limit
        }
        response = self.service.searchanalytics().query(siteUrl=site_uri, body=request).execute()
        
        if 'rows' not in response:
            return pd.DataFrame()

        data = []
        for row in response['rows']:
            entry = {dims[i]: row['keys'][i] for i in range(len(dims))}
            entry.update({
                'clicks': row['clicks'],
                'impressions': row['impressions'],
                'ctr': row['ctr'],
                'position': row['position']
            })
            data.append(entry)
        return pd.DataFrame(data)

    def create_google_doc(self, title, content):
        """Creates a new Google Doc and populates it with content."""
        if not self.credentials:
            self.connect()
        
        try:
            docs_service = build('docs', 'v1', credentials=self.credentials)
            doc = docs_service.documents().create(body={'title': title}).execute()
            doc_id = doc.get('documentId')
            
            # Simple insertion of the content
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': 1,
                        },
                        'text': content
                    }
                }
            ]
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            return f"https://docs.google.com/document/d/{doc_id}/edit"
        except Exception as e:
            raise Exception(f"Erro ao criar documento no Google Docs: {str(e)}")
