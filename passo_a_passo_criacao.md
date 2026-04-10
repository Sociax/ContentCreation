# 🚀 Sociax Analytics v2: Passo a Passo da Criação

Este documento foi criado para registrar a jornada de desenvolvimento do **Sociax Analytics v2**, documentando desde a idealização até a implementação final da arquitetura. Ele serve como material de apresentação e guia arquitetural para a equipe.

---

## 1. O Desafio e a Visão do Produto
A necessidade era construir uma ferramenta própria, de uso direto e intuitivo, mas que aparentasse ter a complexidade de um software SaaS (Software as a Service) Premium de mercado. 
**O objetivo:** Unir dados robustos de SEO à capacidade analítica de Inteligência Artificial sem que o analista precise sair da plataforma.

**A Stack Tecnológica Selecionada:**
- **Linguagem Base:** Python 3.x
- **Interface e Roteamento:** Streamlit (desenvolvimento web ágil e focado em dados)
- **Engenharia de Dados:** Pandas
- **APIs de Fonte da Verdade:** Google API Client (Google Search Console)
- **Motor de Inteligência:** Google Gemini (1.5 Flash via `google-generativeai`)

---

## 2. Passo a Passo do Desenvolvimento

### Passo 1: O Motor de Autenticação (`auth_engine.py`)
A primeira grande barreira era o acesso seguro aos dados dos clientes.
- Implementei o fluxo **OAuth 2.0**. Ao invés de lidar com senhas, o sistema exige uma conta Google com permissões na propriedade desejada.
- Criei a classe `AuthEngineGSC` que lê um arquivo seguro (`client_secret.json`) e salva as sessões localmente (`sociax_token_v2.pickle`).
- Desenvolvi a lógica que puxa a lista completa de sites vinculados àquela conta e filtra métricas-chave: *Cliques, Impressões, CTR e Posição*.

### Passo 2: O Cérebro da Inteligência Artificial (`ai_engine.py`)
Não queria apenas gráficos, queria "Insights como Serviço".
- Criei a classe `AIEngineGemini` integrando a IA generativa do Google.
- **Auditoria de Estratégia:** Programei "System Prompts" altamente personalizados focados em termos de negócios, eficiência de capital e SEO Arbitrage. Quando os dados chegam do GSC, envio ao modelo para que ele encontre oportunidades não óbvias.
- **Otimizador de Conteúdo:** Integrei raspadores web (`trafilatura` e `beautifulsoup4`). A plataforma consegue visitar uma URL do meu cliente e pontuar se o conteúdo da página responde adequadamente à Palavra-Chave buscada, agindo como um consultor editorial.

### Passo 3: Construção da Interface Principal (`dashboard.py`)
A amarração técnica. O arquivo visual onde instancio e chamo as regras dos Passos 1 e 2.
- Adotei um layout de dupla-visão ("GSC Analytics" para performance ampla e "Content Optimizer" para microscopia de URL).
- Usei a **Barra Lateral do Streamlit** (Sidebar) como controle principal. É nela que o usuário decide a data de análise, qual projeto (Site) estudar e escolhe a visão da tela.
- Incluí um ChatBot de Consultoria contínua para que o analista possa fazer perguntas ativas sobre os dados que estão brotando na tela no exato momento.

### Passo 4: UX/UI e a Estilização "Premium" (`premium_style.css`)
Sistemas Streamlit puros parecem acadêmicos ou relatórios de protótipos. O Sociax necessitava de uma identidade forte.
- Injetei Vanilla CSS dentro do ecossistema do Python.
- Alterei a paleta global para o "Dark Mode Tático", utilizando fundos de chumbo/preto (`#0A0A0A`) com pontos de destaque em "Verde Sociax" (`#00B74F`).
- Adicionei tipografias futuristas (`Michroma`, `Inter`) e Efeitos Glow em elementos textuais, criando cartões transparentes (`glassmorphism`) no lugar das caixas cinzas comuns.

### Passo 5: O Engenheiro de Performance (`CWV ENGINEER`)
Integrei uma camada de Auditoria Técnica de Performance para garantir que o "Capital de Busca" não seja desperdiçado por sites lentos.
- **API PageSpeed Insights:** Implementei a conexão para buscar dados de Core Web Vitals (LCP, CLS e INP).
- **Tratamento de Dados:** Filtrei métricas CrUX (usuários reais) e Lighthouse (laboratório) para exibição visual imediata no dashboard com cores de alerta.
- **Roadbook Técnico:** Programei o Gemini para analisar os gargalos técnicos e entregar um roteiro de correções de alta prioridade.

### Passo 6: O Toque Final (`UI Overhaul Premium`)
Por fim, realizei um refinamento estético completo para elevar a experiência para o patamar de software de elite.
- **Glassmorphism Avançado:** Refinei os cards de métricas com efeitos de desfoque e profundidade, adicionando micro-interações ao passar o mouse (*hovers*).
- **Navigation UX:** Transformei os botões de rádio tradicionais em um menu de navegação lateral moderno e integrado, com estados ativos e transições fluidas.
- **Inputs & Selectors:** Estilizei todos os campos de entrada e seletores para seguirem a paleta dark mode com bordas iluminadas e foco suavizado.
- **Hierarquia de Dados:** Melhorei visualmente a exibição dos Core Web Vitals, criando badges coloridos para status (Verde/Amarelo/Vermelho) que facilitam o diagnóstico imediato.

---

## 3. Desafios Superados (Histórico de Refinamento)
Durante minha construção, algumas pivotações provaram ser excelentes apostas a longo prazo:
1. **Remoção de Inputs Manuais:** Originalmente as IDs precisavam ser digitadas; refatorei para que as APIs retornassem listas em menus suspensos (Dropdowns).
2. **Estabilidade de LLM:** Sofri problemas com a nova biblioteca Alpha do Google. O *Rollback* técnico para o conector legado (`google-generativeai`) garantiu escala e proteção contra encerramentos de Cota e instabilidade de Endpoints.
3. **Agrupadores Múltiplos:** Criei suporte a leitura e manipulações de banco de dados offline (como parseamento de extratos do *ScreamingFrog* - `.dbseospider`), transformando a Sociax num Hub central de Diagnósticos.
4. **Análise de Performance Integrada:** Reconheci que SEO não é apenas conteúdo, mas também velocidade. A inclusão da aba CWV resolve a necessidade de usar ferramentas externas para auditoria técnica básica.

---

## 4. Como Executar o Sistema Localmente
Para os novos devs e curiosos, o setup diário exige apenas o básico:
1. Validar as variáveis de ambiente e ter o token local `client_secret.json`.
2. Executar em terminal na raiz do projeto:
   ```bash
   pip install -r requirements.txt
   streamlit run dashboard.py
   ```

**🌟 Sociax Analytics:** Do protótipo aos grandes insights unindo Dados de Performance, UX imersivo e IA Estrutural.
