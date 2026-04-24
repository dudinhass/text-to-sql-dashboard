import streamlit as st
import pandas as pd

import requests

# 1. Configuração da Página
st.set_page_config(
    page_title="Global Crisis Data Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Injeção de CSS customizado
st.markdown("""
    <style>
    /* Fundo da aplicação */
    .stApp {
        background-color: #F4F7F6;
    }
    
    /* Estilização dos Cards de Métrica */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        border: 1px solid #F3F4F6;
    }
    
    /* Ajuste de tipografia dos Cards */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #1F2937 !important;
    }
    
    /* Botões Principais (Verde HR) */
    div.stButton > button[kind="primary"] {
        background-color: #10B981;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #059669;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }
    
    /* Textos Gerais */
    h1, h2, h3, h4, h5, h6, p, span {
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        color: #1F2937;
    }
    
    /* Caixas de Texto (Inputs) */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* Ajuste de padding do topo */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Barra Lateral (Sidebar)
with st.sidebar:
    st.markdown("### 🌍 Global Crisis Assistant")
    st.markdown("---")
    
    menu = st.radio("Navegação", ["📊 Dashboard", "📄 Relatórios"])
    st.markdown("---")
    modelo_ia = st.selectbox("🧠 Modelo de IA", ["Groq Llama 3.3 (70B)"])
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.caption("Fase 4 - API + Frontend")

# 4. Corpo Principal
if menu == "📊 Dashboard":
    st.title("Global Crisis Data Assistant")
    st.markdown("Traduza linguagem natural em insights precisos do PostgreSQL utilizando IA.")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("🛢️ Petróleo Brent", "$85.50", "1.2%")
    with col2: st.metric("📰 Sentimento Global", "45/100", "-5%")
    with col3: st.metric("📈 Índice S&P 500", "5.100", "0.8%")

    st.markdown("---")
    st.subheader("🤖 Consulta Assistida")
    
    pergunta = st.text_input(
        "O que você gostaria de descobrir?",
        placeholder="Ex: Como o volume de manchetes de conflito afetou o custo do contêiner global?"
    )
    
    btn_gerar = st.button("Gerar Análise", type="primary", use_container_width=True)
    
    if btn_gerar and pergunta:
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.spinner("🧠 A IA está escrevendo o SQL, consultando o banco e formulando a resposta..."):
            try:
                # Fazendo a requisição para a nossa API FastAPI
                resposta = requests.post(
                    "http://127.0.0.1:8000/ask", 
                    json={"question": pergunta}
                )
                
                if resposta.status_code == 200:
                    dados = resposta.json()
                    texto_ia = dados.get("answer", "")
                    sql_gerado = dados.get("sql_query", "")
                    
                    st.success("Análise concluída com sucesso!")
                    
                    # Resposta Intuitiva (Foco em clareza para todos os públicos)
                    st.markdown("### 💡 Insight Direto da IA")
                    st.info(texto_ia)
                    
                    # Botão expansivo para quem quiser ver a parte técnica
                    with st.expander("🛠️ Ver bastidores técnicos (Código SQL Gerado)"):
                        st.markdown("A IA gerou e executou de forma autônoma a seguinte query no nosso banco PostgreSQL:")
                        st.code(sql_gerado, language="sql")
                        
                else:
                    st.error(f"Erro na API: {resposta.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Não foi possível conectar ao Backend. Verifique se a sua API (uvicorn) está rodando na porta 8000.")

elif menu == "📄 Relatórios":
    st.title("📄 Relatórios Salvos")
    st.info("A funcionalidade de relatórios será implementada na Fase 5.")
