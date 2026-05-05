import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pandas as pd

# SCOPES for Google Search Console and Google Analytics APIs
SCOPES = [
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/analytics.readonly'
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
            if "gcp_oauth_credentials" in st.secrets:
                creds_info = st.secrets["gcp_oauth_credentials"]
                if isinstance(creds_info, str):
                    creds_info = json.loads(creds_info)
                # Forçar conversão de TOML dict para plain dict caso necessário
                self.credentials = Credentials.from_authorized_user_info(dict(creds_info), SCOPES)
        except Exception:
            pass

        if not self.credentials and os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # Validar se a credencial existe, é válida e possui os escopos corretos
        if not self.credentials or not self.credentials.valid or not self.credentials.has_scopes(SCOPES):
            if self.credentials and self.credentials.expired and self.credentials.refresh_token and self.credentials.has_scopes(SCOPES):
                self.credentials.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    # Final fallback: check current working directory
                    if os.path.exists('client_secret.json'):
                        self.client_secrets_file = os.path.abspath('client_secret.json')
                    else:
                        raise FileNotFoundError(f"Credenciais OAuth ({self.client_secrets_file}) não encontradas.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES)
                self.credentials = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)

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
