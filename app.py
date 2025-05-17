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
st.set_page_config(page_title="O GUARDIÃO", layout="wide")

# Navegação na barra lateral
st.sidebar.title("🔍 Navegação")
page = st.sidebar.radio("Escolha uma aba:", ["Dashboard", "Informativo", "Chatbot"])

# Cache para carregar dados
@st.cache_data
def load_analysis():
    data_dir = "data"
    analysis_file = os.path.join(data_dir, "analyst_data.parquet")
    if not os.path.exists(analysis_file):
        logger.warning(f"Arquivo de análise {analysis_file} não encontrado, executando pipeline")
        _, analysis = orchestrator.run_pipeline()
    else:
        df = pd.read_parquet(analysis_file, engine="pyarrow")
        # Reconstruir dicionário de análise a partir do Parquet
        analysis = {}
        for _, row in df.iterrows():
            category = row["Category"]
            subcategory = row["Subcategory"]
            value = row["Value"]
            if subcategory:
                if category not in analysis:
                    analysis[category] = {}
                analysis[category][subcategory] = value
            else:
                analysis[category] = value
    return analysis

# Página Dashboard
def show_dashboard():
    st.title("📊 Dashboard de Golpes Financeiros")
    analysis = load_analysis()

    if not analysis:
        st.warning("Nenhum dado disponível. Execute o pipeline primeiro.")
        return

    # Total de golpes registrados
    st.metric("Total de Golpes Registrados", analysis.get("total_golpes", 0))

    # Gráfico dos tipos de golpes
    st.subheader("Tipos de Golpes")
    df_types = pd.DataFrame(list(analysis.get("golpes_por_tipo", {}).items()), columns=["Tipo", "Contagem"])
    fig_types = px.bar(df_types, x="Tipo", y="Contagem", title="Distribuição por Tipo de Golpe")
    st.plotly_chart(fig_types)

    # Gráfico dos canais utilizados
    st.subheader("Canais Utilizados")
    df_channels = pd.DataFrame(list(analysis.get("golpes_por_canal", {}).items()), columns=["Canal", "Contagem"])
    fig_channels = px.bar(df_channels, x="Canal", y="Contagem", title="Distribuição por Canal")
    st.plotly_chart(fig_channels)

    # Gráfico do público alvo
    st.subheader("Público Alvo")
    df_public = pd.DataFrame(list(analysis.get("golpes_por_publico", {}).items()), columns=["Público", "Contagem"])
    fig_public = px.bar(df_public, x="Público", y="Contagem", title="Distribuição por Público Alvo")
    st.plotly_chart(fig_public)

# Página Informativo
def show_informative():
    st.title("📚 Informativo sobre Golpes")
    analysis = load_analysis()

    st.write("### Principais Golpes Identificados")
    for fraud_type, count in sorted(analysis.get("golpes_por_tipo", {}).items(), key=lambda x: x[1], reverse=True)[:5]:
        st.subheader(f"🔍 {fraud_type}")
        st.write(f"- **Ocorrências**: {count}")
        response = orchestrator.get_educational_response(f"Como se prevenir de {fraud_type}?", analysis)
        st.markdown(response)

# Página Chatbot
def show_chatbot():
    st.title("🤖 Chatbot Antifraude")
    st.write("Pergunte sobre golpes financeiros e receba dicas de prevenção:")

    # Inicializa o estado da sessão para o histórico do chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    question = st.text_input("Digite sua pergunta:", key="chat_input")
    if question:
        analysis = load_analysis()
        response = orchestrator.get_educational_response(question, analysis)
        st.session_state.chat_history.append({"user": question, "bot": response})

    # Exibe o histórico do chat
    for chat in st.session_state.chat_history:
        st.markdown(f"**Você**: {chat['user']}")
        st.markdown(f"**Chatbot**: {chat['bot']}")

# Renderiza a página selecionada
if page == "Dashboard":
    show_dashboard()
elif page == "Informativo":
    show_informative()
elif page == "Chatbot":
    show_chatbot()