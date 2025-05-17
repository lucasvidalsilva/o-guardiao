import os
import re
import json
import logging
import datetime
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from src.utils import setup_logging, load_config

# Carregando variáveis de ambiente e configurando o log
load_dotenv()
setup_logging()

class EngineerAgent:
    def __init__(self):
        self.config = load_config()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("SEARCH_ENGINE_ID")
        self.logger = logging.getLogger(__name__)
        # Se não existir o diretório /data, crie
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

    def pesquisa_dados_golpes(self, query, max_results=10):
        """Pesquisa por dados recentes sobre fraudes financeiras usando a API de Pesquisa Personalizada do Google."""
        try:
            service = build("customsearch", "v1", developerKey=self.api_key)
            result = service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=max_results
            ).execute()
            return result.get("items", [])
        except HttpError as e:
            self.logger.error(f"Erro na API de busca: {e}")
            return []

    def normalize_data(self, data):
        """Normaliza os dados extraídos para garantir consistência."""
        normalized = []
        for item in data:
            try:
                normalized_item = {
                    "Fonte": re.sub(r"\[\d+\]", "", item.get("Fonte", "")).strip(),
                    "Data da notícia": item.get("Data da notícia", ""),
                    "Tipo do golpe": self.normalize_golpe_type(item.get("Tipo do golpe", "")),
                    "Descrição breve do golpe": item.get("Descrição breve do golpe", ""),
                    "Canal utilizado": self.normalize_canal(item.get("Canal utilizado", "")),
                    "Público alvo": self.normalize_publico(item.get("Público alvo", "")),
                    "Estimativa de impacto ou prejuízo": item.get("Estimativa de impacto ou prejuízo", "")
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.error(f"Erro ao normalizar item {item}: {e}")
        return normalized

    def normalize_golpe_type(self, text):
        """Normaliza o tipo de golpe."""
        text = str(text).lower()
        mappings = {
            "pix": "Golpe do Pix",
            "phishing": "Phishing",
            "suporte técnico": "Golpe do Suporte Técnico",
            "investimento": "Falso Investimento",
            "whatsapp": "Clonagem de WhatsApp",
            "empréstimo": "Falso Empréstimo",
            "comprovante": "Falso Comprovante de Pagamento",
            "perfil falso": "Perfil Falso",
            "deepfake": "Deepfake / IA",
            "link": "Site Falso / Link Malicioso",
            "cartão": "Golpe do Cartão",
            "número falso": "Golpe com Número Falso",
            "bolsa família": "Falso Bolsa Família",
            "auxílio": "Golpe do Auxílio",
            "compra falsa": "Compra Falsa"
        }
        for key, value in mappings.items():
            if key in text:
                return value
        return "Outros"

    def normalize_canal(self, text):
        """Normaliza o canal pelo qual o golpe foi aplicado."""
        text = str(text).lower()
        mappings = {
            "whatsapp": "WhatsApp",
            "sms": "SMS / Mensagens",
            "e-mail": "E-mail",
            "telefone": "Telefone",
            "pix": "PIX",
            "cartão": "Cartão de Crédito / Débito",
            "boletos": "Boletos",
            "rede social": "Redes Sociais",
            "e-commerce": "E-commerce / Plataformas Online",
            "máquina de cartão": "Máquina de Cartão",
            "dns": "Manipulação de DNS",
            "inteligência artificial": "IA / Deepfake",
            "diversos": "Diversos"
        }
        for key, value in mappings.items():
            if key in text:
                return value
        return "Outros"

    def normalize_publico(self, text):
        """Normaliza o público-alvo dos golpes."""
        text = str(text).lower()
        mappings = {
            "idoso": "Idosos",
            "jovens": "Jovens",
            "pix": "Usuários do Pix",
            "whatsapp": "Usuários do WhatsApp",
            "internet": "Usuários de Internet",
            "investidor": "Investidores",
            "comerciante": "Comerciantes",
            "clientes de banco": "Clientes Bancários",
            "população": "População em Geral",
            "consumidores": "Consumidores",
            "instituições financeiras": "Instituições Financeiras",
            "empresas": "Empresas",
            "carnaval": "Foliões"
        }
        for key, value in mappings.items():
            if key in text:
                return value
        return "Outros"

    def salva_em_parquet(self, data, filename="engineer_data.parquet"):
        """Salva os dados normalizados em um arquivo .parquet na pasta /data."""
        try:
            df = pd.DataFrame(data)
            output_path = os.path.join(self.data_dir, filename)
            df.to_parquet(output_path, engine="pyarrow", index=False)
            self.logger.info(f"{len(data)} registros salvos em {output_path}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar em Parquet: {e}")

    def run(self, date_str):
        """Executa a pipeline do agente Engenheiro de Dados."""
        query = f"Golpes financeiros Brasil 2025"
        raw_data = self.pesquisa_dados_golpes(query)
        structured_data = [
            {
                "Fonte": item.get("link", ""),
                "Data da notícia": date_str,
                "Tipo do golpe": item.get("title", "").lower(),
                "Descrição breve do golpe": item.get("snippet", ""),
                "Canal utilizado": "Internet",
                "Público alvo": "População em Geral",
                "Estimativa de impacto ou prejuízo": "Não informado"
            } for item in raw_data
        ]
        normalized_data = self.normalize_data(structured_data)
        self.salva_em_parquet(normalized_data, "engineer_data.parquet")
        return normalized_data