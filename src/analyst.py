import logging
import pandas as pd
from collections import Counter
from dotenv import load_dotenv
from src.utils import setup_logging, load_config
import os

load_dotenv()
setup_logging()

class AnalystAgent:
    def __init__(self):
        self.config = load_config()
        self.logger = logging.getLogger(__name__)
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

    def read_from_parquet(self, filename="engineer_data.parquet"):
        """Lê dados de um arquivo Parquet local."""
        try:
            input_path = os.path.join(self.data_dir, filename)
            if not os.path.exists(input_path):
                self.logger.warning(f"Arquivo Parquet {input_path} não encontrado")
                return pd.DataFrame()
            df = pd.read_parquet(input_path, engine="pyarrow")
            self.logger.info(f"Lido {len(df)} registros de {input_path}")
            return df
        except Exception as e:
            self.logger.error(f"Erro ao ler arquivo Parquet: {e}")
            return pd.DataFrame()

    def analyze_data(self, df):
        """Analisa os dados de fraude e gera métricas."""
        if df.empty:
            self.logger.warning("Nenhum dado para analisar")
            return {}

        total_golpes = len(df)
        tipos = Counter(df["Tipo do golpe"])
        canais = Counter(df["Canal utilizado"])
        publicos = Counter(df["Público alvo"])
        fontes = Counter(df["Fonte"])

        # Análise de tendência (se datas estiverem disponíveis)
        df["Data da notícia"] = pd.to_datetime(df["Data da notícia"], errors="coerce")
        tendencias_mensais = df.groupby(df["Data da notícia"].dt.to_period("M")).size().to_dict()

        return {
            "total_golpes": total_golpes,
            "golpes_por_tipo": dict(tipos),
            "golpes_por_canal": dict(canais),
            "golpes_por_publico": dict(publicos),
            "golpes_por_fonte": dict(fontes),
            "tendencias_mensais": {str(k): v for k, v in tendencias_mensais.items()}
        }

    def save_analysis(self, analysis, filename="analyst_data.parquet"):
        """Salva os resultados da análise em um arquivo Parquet local."""
        try:
            # Converte a análise para um DataFrame plano
            linhas = []
            for chave, valor in analysis.items():
                if isinstance(valor, dict):
                    for subchave, subvalor in valor.items():
                        linhas.append({"Categoria": chave, "Subcategoria": subchave, "Valor": subvalor})
                else:
                    linhas.append({"Categoria": chave, "Subcategoria": "", "Valor": valor})
            df = pd.DataFrame(linhas)
            output_path = os.path.join(self.data_dir, filename)
            df.to_parquet(output_path, engine="pyarrow", index=False)
            self.logger.info(f"Análise salva em {output_path}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar análise em Parquet: {e}")

    def run(self):
        """Executa a pipeline do analista."""
        df = self.read_from_parquet("engineer_data.parquet")
        analysis = self.analyze_data(df)
        self.save_analysis(analysis, "analyst_data.parquet")
        return analysis