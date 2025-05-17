import os
import re
import json
import logging
import datetime
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from src.utils import setup_logging, load_config

load_dotenv()
setup_logging()

class EngineerAgent:
    def __init__(self):
        self.config = load_config()
        self.logger = logging.getLogger(__name__)
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self.logger.error("GEMINI_API_KEY não encontrada no .env")
            raise ValueError("GEMINI_API_KEY não configurada")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    def criar_prompt_agente(self):
        return """
Você é um engenheiro de dados especializado em golpes financeiros. Sua tarefa é buscar e retornar informações reais e recentes (de 2025) sobre golpes financeiros ocorridos no Brasil, usando fontes confiáveis como G1, UOL, TecMundo, Polícia Federal, Febraban, Reclame Aqui.

Retorne SOMENTE uma lista JSON com os seguintes campos:

[
  {
    "Fonte": "https://...",
    "Data da notícia": "2025-MM-DD",
    "Tipo do golpe": "Phishing",
    "Descrição breve do golpe": "Usuários recebem e-mails falsos se passando por bancos.",
    "Canal utilizado": "E-mail",
    "Público alvo": "Clientes Bancários",
    "Estimativa de impacto ou prejuízo": "Mais de 100 mil reais em prejuízo"
  },
  ...
]

Apenas o JSON estruturado. Sem explicações ou texto adicional. Certifique-se de que a lista JSON seja válida e contenha dados reais de 2025.
"""

    def search_fraud_data(self, query="Golpes financeiros Brasil 2025", max_results=10):
        try:
            prompt = self.criar_prompt_agente()
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Extrair JSON da resposta
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                json_text = match.group(0)
                results = json.loads(json_text)
                self.logger.info(f"{len(results)} resultados reais extraídos com Gemini")
                return results[:max_results]
            else:
                self.logger.warning("Nenhum JSON válido encontrado na resposta do Gemini")
                return []

        except Exception as e:
            self.logger.error(f"Erro ao buscar dados com Gemini: {e}")
            return []

    def normalize_data(self, data):
        normalized = []
        for item in data:
            try:
                normalized_item = {
                    "Fonte": re.sub(r"\[\d+\]", "", item.get("Fonte", "")).strip(),
                    "Data da notícia": item.get("Data da notícia", datetime.datetime.now().strftime("%Y-%m-%d")),
                    "Tipo do golpe": self.normalize_golpe_type(item.get("Tipo do golpe", "").lower()),
                    "Descrição breve do golpe": item.get("Descrição breve do golpe", ""),
                    "Canal utilizado": self.normalize_canal(item.get("Canal utilizado", "Internet").lower()),
                    "Público alvo": self.normalize_publico(item.get("Público alvo", "População em Geral").lower()),
                    "Estimativa de impacto ou prejuízo": item.get("Estimativa de impacto ou prejuízo", "Não informado")
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.error(f"Erro na normalização do item {item}: {e}")
        return normalized

    def normalize_golpe_type(self, text):
        text = str(text).lower()
        mappings = {
            "pix": "Golpe do Pix",
            "phishing": "Phishing",
            "suporte": "Golpe do Suporte Técnico",
            "investimento": "Falso Investimento",
            "whatsapp": "Clonagem de WhatsApp",
            "empréstimo": "Falso Empréstimo",
            "comprovante": "Falso Comprovante de Pagamento",
            "perfil": "Perfil Falso",
            "deepfake": "Deepfake / IA",
            "link": "Site Falso / Link Malicioso",
            "cartão": "Golpe do Cartão",
            "número": "Golpe com Número Falso",
            "bolsa": "Falso Bolsa Família",
            "auxílio": "Golpe do Auxílio",
            "compra": "Compra Falsa"
        }
        for key, value in mappings.items():
            if key in text:
                return value
        return "Outros"

    def normalize_canal(self, text):
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
            "máquina": "Máquina de Cartão",
            "dns": "Manipulação de DNS",
            "ia": "IA / Deepfake",
            "internet": "Internet"
        }
        for key, value in mappings.items():
            if key in text:
                return value
        return "Outros"

    def normalize_publico(self, text):
        text = str(text).lower()
        mappings = {
            "idoso": "Idosos",
            "jovens": "Jovens",
            "pix": "Usuários do Pix",
            "whatsapp": "Usuários do WhatsApp",
            "internet": "Usuários de Internet",
            "investidor": "Investidores",
            "comerciante": "Comerciantes",
            "clientes": "Clientes Bancários",
            "população": "População em Geral",
            "consumidores": "Consumidores",
            "instituições": "Instituições Financeiras",
            "empresas": "Empresas",
            "carnaval": "Foliões"
        }
        for key, value in mappings.items():
            if key in text:
                return value
        return "Outros"

    def save_to_parquet(self, data, filename="engineer_data.parquet"):
        try:
            df_new = pd.DataFrame(data)
            output_path = os.path.join(self.data_dir, filename)

            # Se o arquivo já existe, carrega e concatena
            if os.path.exists(output_path):
                df_existing = pd.read_parquet(output_path)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                # Opcional: remover duplicatas baseadas em 'Fonte' e 'Data da notícia'
                df_combined = df_combined.drop_duplicates(subset=["Fonte", "Data da notícia"], keep="last")
            else:
                df_combined = df_new

            # Salvar o DataFrame combinado
            df_combined.to_parquet(output_path, engine="pyarrow", index=False)
            self.logger.info(f"{len(df_combined)} registros salvos em {output_path} ({len(df_new)} novos)")
        except Exception as e:
            self.logger.error(f"Erro ao salvar em Parquet: {e}")

    def run(self, date_str):
        raw_data = self.search_fraud_data()
        normalized_data = self.normalize_data(raw_data)
        self.save_to_parquet(normalized_data, "engineer_data.parquet")
        return normalized_data