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
Você é um engenheiro de dados especializado em golpes financeiros. Sua tarefa é buscar informações reais e recentes (de 2025) sobre golpes financeiros ocorridos no Brasil, usando fontes confiáveis como G1, UOL, TecMundo, Polícia Federal, Febraban, Reclame Aqui.

Retorne SOMENTE uma lista JSON válida com os seguintes campos, sem qualquer texto adicional fora dos colchetes:

[
  {
    "Fonte": "https://...",
    "Data da notícia": "2025-MM-DD",
    "Tipo do golpe": "<escolha uma das opções abaixo>",
    "Descrição breve do golpe": "<descrição curta do golpe>",
    "Canal utilizado": "<escolha uma das opções abaixo>",
    "Público alvo": "<escolha uma das opções abaixo>",
    "Estimativa de impacto ou prejuízo": "<estimativa ou 'Não informado'>"
  },
  ...
]

**Instruções para padronização:**
- Para "Tipo do golpe", escolha EXATAMENTE uma das seguintes opções com base na descrição do golpe:
  - Golpe do Pix
  - Phishing
  - Golpe do Suporte Técnico
  - Falso Investimento
  - Clonagem de WhatsApp
  - Falso Empréstimo
  - Falso Comprovante de Pagamento
  - Perfil Falso
  - Deepfake / IA
  - Site Falso / Link Malicioso
  - Golpe do Cartão
  - Golpe com Número Falso
  - Falso Bolsa Família
  - Golpe do Auxílio
  - Compra Falsa

- Para "Canal utilizado", escolha EXATAMENTE uma das seguintes opções com base no método do golpe:
  - WhatsApp
  - SMS / Mensagens
  - E-mail
  - Telefone
  - PIX
  - Cartão de Crédito / Débito
  - Boletos
  - Redes Sociais
  - E-commerce / Plataformas Online
  - Máquina de Cartão
  - Manipulação de DNS
  - IA / Deepfake
  - Internet

- Para "Público alvo", escolha EXATAMENTE uma das seguintes opções com base nas vítimas:
  - Idosos
  - Jovens
  - Usuários do Pix
  - Usuários do WhatsApp
  - Usuários de Internet
  - Investidores
  - Comerciantes
  - Clientes Bancários
  - População em Geral
  - Consumidores
  - Instituições Financeiras
  - Empresas
  - Foliões

- "Estimativa de impacto ou prejuízo" deve ser um valor estimado (ex.: "Mais de 100 mil reais") ou "Não informado" se desconhecido.
- Certifique-se de que a "Data da notícia" esteja no formato "YYYY-MM-DD" e corresponda a 2025.
- Se não encontrar dados reais, retorne uma lista vazia [].
- A saída deve ser JSON válido, contendo apenas os campos especificados, sem explicações ou mensagens adicionais.
"""

    def search_fraud_data(self, query="Golpes financeiros Brasil 2025", max_results=10):
        try:
            prompt = self.criar_prompt_agente()
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Log da resposta bruta para depuração
            self.logger.debug(f"Resposta do Gemini: {response_text}")

            # Extrair JSON da resposta
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                json_text = match.group(0)
                try:
                    results = json.loads(json_text)
                    if not isinstance(results, list):
                        self.logger.warning("Resposta não é uma lista JSON")
                        return []
                    self.logger.info(f"{len(results)} resultados reais extraídos com Gemini")
                    return results[:max_results]
                except json.JSONDecodeError as e:
                    self.logger.error(f"Erro ao parsear JSON: {e}")
                    return []
            else:
                self.logger.warning("Nenhum JSON válido encontrado na resposta do Gemini")
                return []
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados com Gemini: {e}")
            return []

    def normalize_data(self, data):
        """Aplica limpeza básica, já que os dados vêm padronizados do Gemini."""
        normalized = []
        for item in data:
            try:
                normalized_item = {
                    "Fonte": re.sub(r"\[\d+\]", "", item.get("Fonte", "")).strip(),
                    "Data da notícia": item.get("Data da notícia", datetime.datetime.now().strftime("%Y-%m-%d")),
                    "Tipo do golpe": item.get("Tipo do golpe", "Outros"),
                    "Descrição breve do golpe": item.get("Descrição breve do golpe", ""),
                    "Canal utilizado": item.get("Canal utilizado", "Outros"),
                    "Público alvo": item.get("Público alvo", "População em Geral"),
                    "Estimativa de impacto ou prejuízo": item.get("Estimativa de impacto ou prejuízo", "Não informado")
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.error(f"Erro na normalização do item {item}: {e}")
        return normalized

    def save_to_parquet(self, data, filename="engineer_data.parquet"):
        try:
            df_new = pd.DataFrame(data)
            output_path = os.path.join(self.data_dir, filename)

            # Se o arquivo já existe, carrega e concatena
            if os.path.exists(output_path):
                df_existing = pd.read_parquet(output_path)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                # Remover duplicatas baseadas em 'Fonte' e 'Data da notícia'
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