import streamlit as st
import pandas as pd
import plotly.express as px
from src.orchestrator import Orchestrator
from src.utils import setup_logging
import logging
import os

setup_logging()
logger = logging.getLogger(__name__)

# Inicializa o orquestrador
orchestrator = Orchestrator()

# Configuração da página
st.set_page_config(page_title="O GUARDIÃO", layout="wide", initial_sidebar_state="collapsed")

# CSS personalizado para estilização
st.markdown("""
<style>
    /* Tema geral */
    .stApp {
        background-color: #252525;
        color: #e9e9e9;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Banner */
    .banner {
        background: linear-gradient(90deg, #e48f4f, #cc7030);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }
    .banner h1 {
        color: #e9e9e9;
        font-size: 3em;
        margin: 0;
        text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.6);
    }
    .banner p {
        color: #fff;
        font-size: 1.2em;
        margin-top: 10px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 25px;
        justify-content: center;
        background-color: #1e1e1e;
        padding: 12px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #bbb;
        font-size: 1.1em;
        padding: 10px 20px;
        border-radius: 10px;
        transition: all 0.3s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e48f4f;
        color: #252525;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e48f4f;
        color: #252525 !important;
        font-weight: bold;
        box-shadow: 0 0 10px #e48f4f66;
    }

    /* Botões */
    .stButton>button {
        background-color: #e48f4f;
        color: #252525;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-size: 1em;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #252525;
        color: #e48f4f;
        border: 1px solid #e48f4f;
    }

    /* Inputs */
    .stTextInput>div>input {
        background-color: #1e1e1e;
        color: #e9e9e9;
        border: 1px solid #e48f4f;
        border-radius: 10px;
        padding: 10px;
    }

    /* Gráficos */
    .plotly-graph {
        background-color: #1e1e1e;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }

    /* Chat */
    .chat-container {
        background-color: #1e1e1e;
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
        max-height: 450px;
        overflow-y: auto;
        box-shadow: inset 0 0 8px rgba(255, 255, 255, 0.05);
    }
    .chat-message {
        margin: 12px 0;
        padding: 12px 16px;
        border-radius: 10px;
        max-width: 75%;
    }
    .user-message {
        background-color: #e48f4f;
        color: #252525;
        margin-left: auto;
        text-align: right;
        font-weight: bold;
    }
    .bot-message {
        background-color: #383838;
        color: #e9e9e9;
        margin-right: auto;
    }

    /* Expander */
    .st-expander {
        background-color: #2e2e2e;
        border: 1px solid #e48f4f;
        border-radius: 10px;
        padding: 5px;
        margin-bottom: 10px;
    }

    /* Responsividade */
    @media (max-width: 768px) {
        .banner h1 {
            font-size: 2em;
        }
        .banner p {
            font-size: 1em;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 1em;
            padding: 8px 15px;
        }
    }
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
""", unsafe_allow_html=True)

# Cache para carregar dados
@st.cache_data
def load_analysis():
    data_dir = "data"
    analysis_file = os.path.join(data_dir, "analyst_data.parquet")
    
    if not os.path.exists(analysis_file):
        logger.warning(f"Arquivo de análise {analysis_file} não encontrado, executando pipeline")
        _, analysis = orchestrator.run_pipeline()
        return analysis

    try:
        df = pd.read_parquet(analysis_file, engine="pyarrow")
        required_columns = ["Categoria", "Subcategoria", "Valor"]
        if df.empty or not all(col in df.columns for col in required_columns):
            logger.warning(f"Arquivo {analysis_file} está vazio ou não contém colunas esperadas: {required_columns}")
            _, analysis = orchestrator.run_pipeline()
            return analysis

        analysis = {}
        for _, row in df.iterrows():
            category = row["Categoria"]
            subcategory = row["Subcategoria"]
            value = row["Valor"]
            if subcategory:
                if category not in analysis:
                    analysis[category] = {}
                analysis[category][subcategory] = value
            else:
                analysis[category] = value
        return analysis
    except Exception as e:
        logger.error(f"Erro ao ler {analysis_file}: {e}")
        _, analysis = orchestrator.run_pipeline()
        return analysis

# Banner
with st.container():
    st.markdown("""
    <div class="banner">
        <h1><i class="fas fa-shield-alt"></i> O GUARDIÃO</h1>
        <p>Protegendo você contra golpes financeiros</p>
    </div>
    """, unsafe_allow_html=True)

# Tabs para navegação
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📚 Informativo", "🤖 Chatbot"])

# Página Dashboard
with tab1:
    st.markdown("<h2><i class='fas fa-chart-bar'></i> Dashboard de Golpes Financeiros</h2>", unsafe_allow_html=True)
    analysis = load_analysis()

    if not analysis:
        st.warning("Nenhum dado disponível. Tente executar o pipeline novamente.")
        if st.button("Executar Pipeline"):
            with st.spinner("Executando pipeline..."):
                _, analysis = orchestrator.run_pipeline()
                st.experimental_rerun()
    else:
        # Total de golpes registrados
        st.metric(label="Total de Golpes Registrados", value=analysis.get("total_golpes", 0), delta_color="off")

        # Gráficos em colunas
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h3>Tipos de Golpes</h3>", unsafe_allow_html=True)
            tipos = analysis.get("golpes_por_tipo", {})
            if tipos:
                df_types = pd.DataFrame(list(tipos.items()), columns=["Tipo", "Contagem"])
                fig_types = px.bar(df_types, x="Tipo", y="Contagem", title="Distribuição por Tipo de Golpe",
                                   color_discrete_sequence=["#e48f4f"])
                fig_types.update_layout(paper_bgcolor="#252525", plot_bgcolor="#252525", font_color="#e9e9e9")
                st.plotly_chart(fig_types, use_container_width=True)
            else:
                st.info("Nenhum dado disponível para tipos de golpes.")

        with col2:
            st.markdown("<h3>Canais Utilizados</h3>", unsafe_allow_html=True)
            canais = analysis.get("golpes_por_canal", {})
            if canais:
                df_channels = pd.DataFrame(list(canais.items()), columns=["Canal", "Contagem"])
                fig_channels = px.bar(df_channels, x="Canal", y="Contagem", title="Distribuição por Canal",
                                      color_discrete_sequence=["#e48f4f"])
                fig_channels.update_layout(paper_bgcolor="#252525", plot_bgcolor="#252525", font_color="#e9e9e9")
                st.plotly_chart(fig_channels, use_container_width=True)
            else:
                st.info("Nenhum dado disponível para canais utilizados.")

        st.markdown("<h3>Público Alvo</h3>", unsafe_allow_html=True)
        publicos = analysis.get("golpes_por_publico", {})
        if publicos:
            df_public = pd.DataFrame(list(publicos.items()), columns=["Público", "Contagem"])
            fig_public = px.pie(df_public, names="Público", values="Contagem", title="Distribuição por Público Alvo",
                                color_discrete_sequence=["#e48f4f", "#f5b041", "#e67e22"])
            fig_public.update_layout(paper_bgcolor="#252525", plot_bgcolor="#252525", font_color="#e9e9e9")
            st.plotly_chart(fig_public, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para público alvo.")

# Página Informativo
with tab2:
    st.markdown("<h2><i class='fas fa-book'></i> Informativo sobre Golpes</h2>", unsafe_allow_html=True)
    analysis = load_analysis()

    if not analysis:
        st.warning("Nenhum dado disponível. Execute o pipeline primeiro.")
    else:
        st.markdown("### Principais Golpes Identificados")
        tipos = analysis.get("golpes_por_tipo", {})
        if tipos:
            for fraud_type, count in sorted(tipos.items(), key=lambda x: x[1], reverse=True)[:5]:
                with st.expander(f"🔍 {fraud_type} ({count} casos)"):
                    st.markdown(f"- **Ocorrências**: {count}")
                    response = orchestrator.get_educational_response(f"Como se prevenir de {fraud_type}?", analysis)
                    st.markdown(response)
        else:
            st.info("Nenhum dado disponível para golpes identificados.")

# Página Chatbot
with tab3:
    st.markdown("<h2><i class='fas fa-robot'></i> Chatbot Antifraude</h2>", unsafe_allow_html=True)
    st.markdown("Pergunte sobre golpes financeiros e receba dicas de prevenção:")

    # Inicializa o estado da sessão para o histórico do chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Container para o chat
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for chat in st.session_state.chat_history:
            st.markdown(f'<div class="chat-message user-message">Você: {chat["user"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-message bot-message">Guardião: {chat["bot"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input para nova pergunta
    question = st.text_input("Digite sua pergunta:", key="chat_input", placeholder="Ex.: Como prevenir vazamentos de dados?")
    if question:
        analysis = load_analysis()
        response = orchestrator.get_educational_response(question, analysis)
        st.session_state.chat_history.append({"user": question, "bot": response})
        st.experimental_rerun()