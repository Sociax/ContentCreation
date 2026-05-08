import streamlit as st
import pandas as pd
from auth_engine import AuthEngineGSC
from ai_engine import AIEngineGemini
from datetime import date, timedelta
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Load Premium CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), 'assets', 'premium_style.css')
    if os.path.exists(css_path):
        with open(css_path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# --- Header Section ---
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0;'>🛡️ SOCIAX ANALYTICS</h1>
        <p style='color: #00B74F; font-family: "Michroma"; letter-spacing: 0.2em; font-size: 0.9rem;'>
            A COMPANHIA DE PERFORMANCE CRIATIVA
        </p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Identity
with st.sidebar:
    col_sid1, col_sid2 = st.columns([4, 1])
    with col_sid1:
        st.markdown("<h2 class='sociax-glow-text'>PAINEL CENTRAL</h2>", unsafe_allow_html=True)
    with col_sid2:
        st.markdown('<div class="auth-reset-container">', unsafe_allow_html=True)
        if st.button("🔄", key="reset_auth_icon", help="Resetar Sessão de Autenticação"):
            if os.path.exists('sociax_token_v2.pickle'):
                os.remove('sociax_token_v2.pickle')
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def init_engines_v2():
    try:
        gsc = AuthEngineGSC(client_secrets_file='client_secret.json')
        ai = AIEngineGemini()
        return gsc, ai
    except Exception as e:
        st.error(f"Erro de inicialização: {e}")
        return None, None

gsc, ai = init_engines_v2()

if gsc:
    try:
        # --- Sidebar Navigation State Management ---
        if 'current_view' not in st.session_state:
            st.session_state.current_view = "📊 GSC ANALYTICS"

        def set_view(group_key):
            if st.session_state[group_key] is not None:
                st.session_state.current_view = st.session_state[group_key]

        # --- Sidebar Navigation ---
        data_opts = ["📊 GSC ANALYTICS", "📈 GA4 ANALYTICS"]
        content_opts = ["✍️ CRIADOR DE CONTEÚDOS", "📝 OTIMIZADOR DE CONTEÚDO"]
        tech_opts = ["⚡ CWV", "⚔️ COMPARADOR DE URLS", "🔗 LINKS INTERNOS", "📊 SCHEMA", "📑 HEADERS", "🌐 HREFLANG", "🖼️ ALT IMAGE"]

        with st.sidebar:
            st.markdown("<div class='sociax-subheader-bar'>DATA & ANALYTICS</div>", unsafe_allow_html=True)
            st.radio(
                "Data", data_opts, 
                index=data_opts.index(st.session_state.current_view) if st.session_state.current_view in data_opts else None, 
                key="nav_data", on_change=set_view, args=("nav_data",), label_visibility="collapsed"
            )
            
            st.markdown("<div class='sociax-subheader-bar'>CONTENT CATEGORY</div>", unsafe_allow_html=True)
            st.radio(
                "Content", content_opts, 
                index=content_opts.index(st.session_state.current_view) if st.session_state.current_view in content_opts else None, 
                key="nav_content", on_change=set_view, args=("nav_content",), label_visibility="collapsed"
            )

            st.markdown("<div class='sociax-subheader-bar'>TECH SEO CATEGORY</div>", unsafe_allow_html=True)
            st.radio(
                "Tech", tech_opts, 
                index=tech_opts.index(st.session_state.current_view) if st.session_state.current_view in tech_opts else None, 
                key="nav_tech", on_change=set_view, args=("nav_tech",), label_visibility="collapsed"
            )

        view = st.session_state.current_view

        # --- Sidebar Controls ---
        with st.sidebar:
            if view in ["📊 GSC ANALYTICS", "📝 OTIMIZADOR DE CONTEÚDO", "⚡ CWV"]:
                st.markdown("<div class='sociax-subheader-bar'>SINAIS DE DADOS</div>", unsafe_allow_html=True)
                
                if 'sites_list' not in st.session_state:
                    st.session_state['sites_list'] = gsc.get_properties()
                
                sites = st.session_state['sites_list']
                
                if 'selected_site' not in st.session_state:
                    st.session_state['selected_site'] = sites[0] if sites else None

                selected = st.selectbox(
                    "Selecionar Propriedade", 
                    sites, 
                    index=sites.index(st.session_state['selected_site']) if st.session_state['selected_site'] in sites else 0,
                    key="property_selector",
                    help="Escolha o ativo digital (site) para carregar os sinais de busca."
                )
                st.session_state['selected_site'] = selected

                start = st.date_input("Início da Análise", date.today() - timedelta(days=30), help="Data inicial para auditoria dos dados de busca.")
                end = st.date_input("Fim da Análise", date.today(), help="Data final para auditoria dos dados de busca.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 CARREGAR DADOS DE MERCADO", use_container_width=True, help="Conectar ao motor GSC e processar sinais."):
                    with st.spinner("Decodificando sinais do GSC..."):
                        df = gsc.fetch_analytics(selected, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                        st.session_state['v2_data'] = df
                        st.session_state['last_site'] = selected

        # --- Main Dashboard Rendering ---
        if view == "📊 GSC ANALYTICS":
            if 'v2_data' in st.session_state:
                df = st.session_state['v2_data']
                st.markdown(f"<div class='sociax-subheader-bar'>PERFORMANCE DO ATIVO: {st.session_state.get('last_site')}</div>", unsafe_allow_html=True)
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("CLIQUES TOTAIS", f"{df['clicks'].sum():,}")
                m2.metric("IMPRESSÕES", f"{df['impressions'].sum():,}")
                m3.metric("CTR MÉDIO", f"{df['ctr'].mean():.2%}")
                m4.metric("ÍNDICE DE POSIÇÃO", f"{df['position'].mean():.1f}")
        
                with st.container():
                    st.dataframe(df, use_container_width=True)
                
                st.divider()
                st.markdown("<h2 class='sociax-glow-text'>// CAMADA DE INTELIGÊNCIA</h2>", unsafe_allow_html=True)
                
                st.markdown("<div class='command-center-container'>", unsafe_allow_html=True)
                col_ai1, col_ai2 = st.columns([1, 2])
                
                with col_ai1:
                    st.markdown("<div style='padding-top: 1rem;'>", unsafe_allow_html=True)
                    st.write("Nosso motor baseado em Gemini audita os dados de mercado sob a ótica de eficiência de capital e disciplina financeira.")
                    if st.button("⚡ EXECUTAR AUDITORIA DE ESTRATÉGIA IA", use_container_width=True):
                        with st.spinner("Gemini processando arbitragem de SEO..."):
                            report = ai.run_seo_analysis(df, st.session_state.get('last_site', ''))
                            st.session_state['last_report'] = report
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col_ai2:
                    if 'last_report' in st.session_state:
                        st.markdown("<div class='terminal-viewport'><div class='terminal-header'><span class='terminal-status'>SISTEMA OPERACIONAL // DIAGNÓSTICO COMPLETO</span><small style='color: rgba(0,183,79,0.5); font-family: monospace;'>v2.5.0-ESTÁVEL</small></div>", unsafe_allow_html=True)
                        st.markdown(st.session_state['last_report'])
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='terminal-viewport' style='display: flex; align-items: center; justify-content: center; min-height: 200px;'><div style='text-align: center; opacity: 0.3;'><p style='font-family: Michroma; font-size: 0.8rem;'>AGUARDANDO COMANDO DE EXECUÇÃO...</p><code style='color: var(--sociax-green);'>intelligence_layer.init()</code></div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                        
                st.divider()
                st.markdown("<h3 class='sociax-glow-text'>CHAT DO CONSULTOR</h3>", unsafe_allow_html=True)
                q = st.text_input("Pergunte sobre sinais específicos de mercado ou oportunidades de SEO:")
                if q:
                    with st.spinner("Sintetizando resposta..."):
                        ans = ai.chat(q, df)
                        st.chat_message("assistant").write(ans)
            else:
                st.markdown("<div class='premium-card' style='text-align: center; background: rgba(255,255,255,0.02);'><h3 style='opacity: 0.5;'>SISTEMA PRONTO</h3><p style='opacity: 0.5;'>Por favor, configure os sinais do ativo na barra lateral para iniciar a análise.</p></div>", unsafe_allow_html=True)
        
        elif view == "📈 GA4 ANALYTICS":
            st.markdown("<h2 class='sociax-glow-text'>// GA4 ANALYTICS</h2>", unsafe_allow_html=True)
            st.write("Conectado ao motor MCP para extração de relatórios e insights do Google Analytics 4.")
            
            # Form setup
            col_ga1, col_ga2 = st.columns(2)
            with col_ga1:
                # Carregamento Dinâmico das Propriedades (Admin API)
                if 'ga4_properties_dict' not in st.session_state:
                    try:
                        from google.analytics.admin import AnalyticsAdminServiceClient
                        if not gsc.credentials:
                            gsc.connect() # Garante que as credenciais OAuth sejam geradas/carregadas
                        admin_client = AnalyticsAdminServiceClient(credentials=gsc.credentials)
                        response = admin_client.list_account_summaries()
                        prop_dict = {}
                        for account in response:
                            for prop in account.property_summaries:
                                clean_id = prop.property.replace('properties/', '')
                                prop_dict[f"{prop.display_name} ({clean_id})"] = clean_id
                        st.session_state['ga4_properties_dict'] = prop_dict
                    except Exception as e:
                        st.session_state['ga4_properties_dict'] = {}
                        st.error(f"Erro ao listar propriedades do GA4: {e}")

                prop_dict = st.session_state.get('ga4_properties_dict', {})
                if prop_dict:
                    selected_prop_name = st.selectbox("Propriedade GA4", list(prop_dict.keys()), help="Lista automática de todas as propriedades da sua conta.")
                    prop_id = prop_dict[selected_prop_name]
                else:
                    prop_id = st.text_input("Property ID Manual", value=os.getenv("GA4_PROPERTY_ID", ""))
                
                # NOVA INTERFACE AGENTE GA4
                st.markdown("<p style='color: #888;'>O Agente GA4 tem acesso dinâmico a todas as métricas e dimensões da sua conta.</p>", unsafe_allow_html=True)
                
            st.divider()
            
            # Inicializa histórico de chat se não existir
            if "ga4_chat_history" not in st.session_state:
                st.session_state.ga4_chat_history = []
                
            # Renderiza histórico
            for msg in st.session_state.ga4_chat_history:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        if "dataframe" in msg:
                            st.dataframe(msg["dataframe"], use_container_width=True)
                        st.write(msg["content"])

            user_ga4_prompt = st.chat_input("O que você deseja saber sobre o tráfego desta propriedade? (Ex: Receita e sessões por cidade nos últimos 15 dias)")
            
            if user_ga4_prompt:
                st.session_state.ga4_chat_history.append({"role": "user", "content": user_ga4_prompt})
                st.chat_message("user").write(user_ga4_prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("🤖 O Agente está traduzindo a sua requisição..."):
                        params = ai.extract_ga4_parameters(user_ga4_prompt)
                        st.write(f"*(📡 Conectando ao MCP GA4 com os parâmetros: Métricas: {params.get('metrics')}, Dimensões: {params.get('dimensions')}, Período: {params.get('start_date')} até {params.get('end_date')})*")
                        
                        metrics = params.get("metrics", [])
                        dimensions = params.get("dimensions", [])
                        start_date = params.get("start_date", "30daysAgo")
                        end_date = params.get("end_date", "today")
                        
                    with st.spinner("Extraindo dados oficiais..."):
                        from mcp_ga_server import get_ga4_report
                        res_json = get_ga4_report(
                            metrics=metrics,
                            dimensions=dimensions,
                            start_date=start_date,
                            end_date=end_date,
                            property_id=prop_id
                        )
                        res = json.loads(res_json)
                        
                        if res.get("status") == "success":
                            df_ga = pd.DataFrame(res.get("data", []))
                            if not df_ga.empty:
                                st.dataframe(df_ga, use_container_width=True)
                                
                                with st.spinner("Analisando os resultados..."):
                                    ans_ga = ai.chat(f"O usuário perguntou: '{user_ga4_prompt}'. Aja como um Analista de Dados Sênior e explique os insights extraídos desta tabela do GA4.", df_ga)
                                    st.write(ans_ga)
                                    
                                    # Salvar no histórico
                                    st.session_state.ga4_chat_history.append({
                                        "role": "assistant", 
                                        "content": ans_ga,
                                        "dataframe": df_ga
                                    })
                            else:
                                msg_vazia = "A API retornou sucesso, mas não há dados (tabela vazia) para esta combinação de métricas, dimensões e datas ou a data é muito recente e o Google aplicou Thresholding."
                                st.warning(msg_vazia)
                                st.session_state.ga4_chat_history.append({"role": "assistant", "content": msg_vazia})
                        else:
                            error_msg = f"**Erro retornado pela API do GA4:** {res.get('message', 'Erro desconhecido. Verifique se a dimensão é compatível com a métrica pedida.')}"
                            st.error(error_msg)
                            st.session_state.ga4_chat_history.append({"role": "assistant", "content": error_msg})

        elif view == "📝 OTIMIZADOR DE CONTEÚDO":
            st.markdown("<h2 class='sociax-glow-text'>// OTIMIZADOR DE CONTEÚDO</h2>", unsafe_allow_html=True)
            col_opt1, col_opt2 = st.columns([1, 1])
            with col_opt1:
                target_url = st.text_input("URL Alvo", placeholder="https://exemplo.com.br/pagina")
                target_kw = st.text_input("Palavra-Chave Principal", placeholder="ex: estrategia seo")
                if st.button("🚀 ANALISAR E PONTUAR CONTEÚDO", use_container_width=True):
                    if target_url and target_kw:
                        with st.spinner("Analisando conteúdo..."):
                            st.session_state['opt_report'] = ai.analyze_content(target_url, target_kw)
            with col_opt2:
                if 'opt_report' in st.session_state:
                    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                    st.markdown(st.session_state['opt_report'])
                    st.markdown("</div>", unsafe_allow_html=True)

        elif view == "⚡ CWV":
            st.markdown("<h2 class='sociax-glow-text'>// CWV</h2>", unsafe_allow_html=True)
            cwv_url = st.text_input("URL Alvo para Auditoria", placeholder="https://exemplo.com.br")
            if st.button("🚀 EXECUTAR AUDITORIA CWV", use_container_width=True):
                if cwv_url:
                    with st.spinner("Buscando sinais..."):
                        cwv_data = ai.get_cwv_metrics(cwv_url)
                        if cwv_data["status"] == "success":
                            st.session_state['cwv_results'] = cwv_data
                            st.session_state['cwv_url'] = cwv_url
            if 'cwv_results' in st.session_state:
                res = st.session_state['cwv_results']
                field_metrics = res.get("metrics", {})
                lab_metrics = res.get("lab_metrics", {})
                lh_score = res.get("lh_score", 0)
                
                st.divider()
                
                # --- Visual Score Indicator ---
                col_score, col_status = st.columns([1, 2])
                with col_score:
                    score_color = "#00B74F" if lh_score > 89 else "#FFA900" if lh_score > 49 else "#FF4B4B"
                    st.markdown(f"""
                        <div style='text-align: center; background: rgba(255,255,255,0.03); padding: 20px; border-radius: 15px; border: 1px solid {score_color}44;'>
                            <h4 style='margin: 0; color: var(--text-dim); font-size: 0.8rem;'>SCORE PERFORMANCE</h4>
                            <h1 style='color: {score_color}; margin: 10px 0; font-size: 3.5rem;'>{lh_score:.0f}</h1>
                            <p style='margin: 0; opacity: 0.6;'>Lighthouse Lab</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_status:
                    if not field_metrics:
                        st.info("💡 **ANÁLISE DE LABORATÓRIO**: Esta URL ainda não possui dados suficientes no CrUX ( Chrome User Experience Report) para exibir métricas de 'Campo' (usuários reais). Abaixo estão os dados simulados pelo motor Lighthouse.")
                    else:
                        st.success("✅ **ANÁLISE DE CAMPO ATIVA**: Dados de usuários reais detectados nos últimos 28 dias.")

                # --- Metrics Grid ---
                st.markdown("<br>", unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                
                def render_metric(col, label, field_val, lab_val):
                    with col:
                        st.markdown(f"""
                            <div style='background: rgba(255,255,255,0.02); padding: 15px; border-radius: 12px; border: 1px solid var(--glass-border);'>
                                <p style='color: var(--text-dim); font-size: 0.75rem; margin-bottom: 5px; text-transform: uppercase;'>{label}</p>
                                <h3 style='margin: 0; font-size: 1.2rem;'>{field_val if field_val else lab_val}</h3>
                                <small style='opacity: 0.4;'>{'CrUX' if field_val else 'Lab'}</small>
                            </div>
                        """, unsafe_allow_html=True)

                # Map CrUX labels to readable names
                lcp_field = field_metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile")
                if lcp_field: lcp_field = f"{lcp_field/1000:.2f}s"
                
                cls_field = field_metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile")
                if cls_field: cls_field = f"{float(cls_field)/100:.3f}"

                fcp_field = field_metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("percentile")
                if fcp_field: fcp_field = f"{fcp_field/1000:.2f}s"

                inp_field = field_metrics.get("INTERACTIVE_TO_NEXT_PAINT", {}).get("percentile")
                if inp_field: inp_field = f"{inp_field}ms"

                render_metric(m1, "LCP (Carregamento)", lcp_field, lab_metrics.get('lcp'))
                render_metric(m2, "CLS (Estabilidade)", cls_field, lab_metrics.get('cls'))
                render_metric(m3, "FCP (Primeira Pintura)", fcp_field, lab_metrics.get('fcp'))
                render_metric(m4, "TBT / INP (Interação)", inp_field, lab_metrics.get('tbt'))

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⚡ GERAR ESTRATÉGIA IA", use_container_width=True):
                    with st.spinner("Sintetizando roteiro técnico..."):
                        st.session_state['cwv_report'] = ai.analyze_cwv(st.session_state['cwv_url'], res)
                
                if 'cwv_report' in st.session_state:
                    st.markdown("<div class='terminal-viewport' style='padding: 20px;'>", unsafe_allow_html=True)
                    st.markdown(st.session_state['cwv_report'])
                    st.markdown("</div>", unsafe_allow_html=True)

        elif view == "⚔️ COMPARADOR DE URLS":
            st.markdown("<h2 class='sociax-glow-text'>// COMPARADOR DE URLS</h2>", unsafe_allow_html=True)
            st.write("Compare ativos via URL ou Código Fonte bruto (útil para páginas atrás de login).")
            
            with st.container(border=True):
                kw = st.text_input("Palavra-Chave Foco", placeholder="ex: melhor agencia de marketing")
                
                col_u1, col_u2 = st.columns(2)
                
                with col_u1:
                    st.markdown("### ATIVO 1")
                    tipo1 = st.toggle("Usar Código Fonte", key="t1")
                    if tipo1:
                        content1 = st.text_area("Cole o HTML (Ativo 1)", height=200, key="c1")
                    else:
                        u1 = st.text_input("URL (Ativo 1)", placeholder="https://seu-site.com.br", key="u1")

                with col_u2:
                    st.markdown("### ATIVO 2")
                    tipo2 = st.toggle("Usar Código Fonte", key="t2")
                    if tipo2:
                        content2 = st.text_area("Cole o HTML (Ativo 2)", height=200, key="c2")
                    else:
                        u2 = st.text_input("URL (Ativo 2)", placeholder="https://concorrente.com.br", key="u2")
                
                if st.button("🚀 EXECUTAR COMPARAÇÃO", use_container_width=True):
                    if kw:
                        with st.spinner("Motor Sociax processando dados..."):
                            # Coleta Ativo 1
                            if tipo1:
                                d1 = ai.parse_html_seo(content1, "Código Manual 1") if content1 else None
                            else:
                                d1 = ai.scrape_url_seo(u1) if u1 else None
                            
                            # Coleta Ativo 2
                            if tipo2:
                                d2 = ai.parse_html_seo(content2, "Código Manual 2") if content2 else None
                            else:
                                d2 = ai.scrape_url_seo(u2) if u2 else None

                            if d1 and d2:
                                report = ai.compare_urls_logic(kw, [d1, d2])
                                st.session_state['comp_report'] = report
                            else:
                                st.error("Certifique-se de preencher ambos os ativos para comparação.")
                    else:
                        st.warning("Preencha a Palavra-Chave para análise.")
            if 'comp_report' in st.session_state:
                st.markdown(st.session_state['comp_report'])

        elif view == "🔗 LINKS INTERNOS":
            st.markdown("<h2 class='sociax-glow-text'>// LINKS INTERNOS</h2>", unsafe_allow_html=True)
            urls_area = st.text_area("URLs do Silo (uma por linha)")
            if st.button("🚀 AUDITAR LINKS"):
                target_urls = [u.strip() for u in urls_area.split('\n') if u.strip()]
                if len(target_urls) >= 2:
                    with st.spinner("Mapeando..."):
                        all_data = [ai.scrape_url_seo(u) for u in target_urls]
                        st.session_state['il_report'] = ai.analyze_internal_linking_logic(all_data, target_urls)
            if 'il_report' in st.session_state:
                st.markdown(st.session_state['il_report'])

        elif view == "📊 SCHEMA":
            st.markdown("<h2 class='sociax-glow-text'>// SCHEMA</h2>", unsafe_allow_html=True)
            s_url = st.text_input("URL para Auditoria")
            if st.button("🚀 AUDITAR SCHEMA"):
                if s_url:
                    with st.spinner("Analisando..."):
                        data = ai.scrape_url_seo(s_url)
                        st.session_state['schema_report'] = ai.analyze_schema_logic(data)
            if 'schema_report' in st.session_state:
                st.markdown(st.session_state['schema_report'])

        elif view == "📑 HEADERS":
            st.markdown("<h2 class='sociax-glow-text'>// HEADERS</h2>", unsafe_allow_html=True)
            h_url = st.text_input("URL para Auditoria Headers")
            h_kw = st.text_input("Palavra-Chave Alvo Headers")
            if st.button("🚀 AUDITAR HEADERS"):
                if h_url and h_kw:
                    with st.spinner("Mapeando..."):
                        data = ai.scrape_url_seo(h_url)
                        st.session_state['headers_report'] = ai.analyze_headers_logic(h_kw, data['headers'])
            if 'headers_report' in st.session_state:
                st.markdown(st.session_state['headers_report'])

        elif view == "🌐 HREFLANG":
            st.markdown("<h2 class='sociax-glow-text'>// HREFLANG</h2>", unsafe_allow_html=True)
            href_url = st.text_input("URL Internacional")
            if st.button("🚀 AUDITAR HREFLANG"):
                if href_url:
                    with st.spinner("Buscando tags..."):
                        st.json(ai.extract_hreflangs(href_url))

        elif view == "🖼️ ALT IMAGE":
            st.markdown("<h2 class='sociax-glow-text'>// ALT IMAGE</h2>", unsafe_allow_html=True)
            img_url = st.text_input("URL Auditoria Imagem")
            img_kw = st.text_input("Palavra-Chave Imagem")
            if st.button("🚀 AUDITAR IMAGENS"):
                if img_url and img_kw:
                    with st.spinner("Analisando visão..."):
                        images = ai.get_page_images(img_url)
                        for img in images[:3]:
                            st.image(img['src'], width=300)
                            st.write(ai.analyze_image_alt_logic(img['src'], img['alt'], img_kw, "Ativo SEO"))

        elif view == "✍️ CRIADOR DE CONTEÚDOS":
            st.markdown("<h2 class='sociax-glow-text'>// CRIADOR DE CONTEÚDOS</h2>", unsafe_allow_html=True)
            st.write("Gere artigos otimizados com Storytelling Orientado a Dados para posicionar clientes como autoridade.")
            
            clients_db = {
                "Sociax": {"name": "Sociax", "url": "https://sociax.com.br/", "desc": "Agência de marketing de performance"},
                "Terê": {"name": "Terê", "url": "https://usetere.com.br/", "desc": "E-commerce de produtos de beleza"},
                "Unidombosco": {"name": "Unidombosco", "url": "https://unidombosco.edu.br/", "desc": "Faculdade com diversos cursos de graduação e pós-graduação"},
                "EPD": {"name": "EPD", "url": "https://epd.edu.br/", "desc": "Faculdade de direito especializada em mestrado e pós-graduação"},
                "Agibank": {"name": "Agibank", "url": "https://agibank.com.br/", "desc": "Banco digital, soluções financeiras e crédito"},
                "Blog Agibank": {"name": "Blog Agibank", "url": "https://blog.agibank.com.br/", "desc": "Blog oficial de educação financeira e dicas sobre crédito"}
            }

            with st.container(border=True):
                col_cg1, col_cg2 = st.columns(2)
                with col_cg1:
                    selected_client_key = st.selectbox("Selecione o Cliente", list(clients_db.keys()))
                    target_kw = st.text_input("Palavra-Chave Principal", placeholder="ex: Mestrado em Direito Administrativo")
                    kw_type = st.selectbox("Tipo de Palavra-Chave", ["Short tail", "Mid tail", "Long tail"])
                    content_format = st.selectbox("Formato do Conteúdo", ["Blog post content", "Category content", "Product description"])
                    keyword_average = st.number_input("Média de Palavras-Chave Desejada", min_value=1, value=5, help="Quantas vezes a palavra-chave deve aparecer em média no texto")
                with col_cg2:
                    content_intent = st.selectbox(
                        "Intenção de Busca",
                        ["Informativo", "Navegacional", "Comercial", "Transacional"]
                    )
                    content_style = st.radio(
                        "Estilo de Escrita",
                        options=["Educativo (Tutorial)", "Provocativo (Opinião)", "Data-Driven (Relatório)"]
                    )
                
                additional_notes = st.text_area("Observações Adicionais", placeholder="Ex: Mencione que estamos com inscrições abertas para o segundo semestre.")
                
                if st.button("🚀 GERAR CONTEÚDO OTIMIZADO", use_container_width=True):
                    if target_kw:
                        with st.spinner("🔍 Coletando tendências em tempo real do Google Trends e gerando conteúdo..."):
                            client_data = clients_db[selected_client_key]
                            # Chama a nova função de AI
                            generated_content = ai.generate_blog_content(client_data, target_kw, content_style, keyword_average, additional_notes, content_intent, kw_type, content_format)
                            st.session_state['cg_report'] = generated_content
                    else:
                        st.warning("Preencha a Palavra-Chave Principal para continuar.")
            
            if 'cg_report' in st.session_state:
                st.markdown("<div class='premium-card' style='margin-top: 2rem;'>", unsafe_allow_html=True)
                st.markdown(st.session_state['cg_report'])
                st.markdown("</div>", unsafe_allow_html=True)
                
                col_exp1, col_exp2, col_exp3 = st.columns([1, 2, 1])
                with col_exp2:
                    if st.button("📄 EXPORTAR PARA GOOGLE DOCS", use_container_width=True):
                        with st.spinner("Criando documento no Google Docs..."):
                            try:
                                from datetime import datetime
                                content = st.session_state['cg_report']
                                
                                # New naming convention: YYYY-MM-DD - Site - Keyword
                                current_date = datetime.now().strftime("%Y-%m-%d")
                                site_name = selected_client_key
                                doc_title = f"{current_date} - {site_name} - {target_kw}"
                                
                                doc_url = gsc.create_google_doc(doc_title, content)
                                st.success(f"✅ Documento criado com sucesso!")
                                st.link_button("🔗 ABRIR GOOGLE DOC", doc_url, use_container_width=True)
                            except Exception as e:
                                st.error(f"Erro ao exportar: {e}")
                                if "insufficient permissions" in str(e).lower() or "scope" in str(e).lower():
                                    st.info("💡 Parece que você precisa autorizar a nova permissão de escrita de documentos. Clique no ícone 🔄 na barra lateral para resetar a sessão e fazer o login novamente.")

    except Exception as e:
        st.error(f"Erro na renderização: {e}")
else:
    st.warning("Motores não configurados corretamente.")
