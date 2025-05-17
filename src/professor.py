import logging
import os
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from src.utils import setup_logging, load_config

load_dotenv()
setup_logging()

class ProfessorAgent:
    def __init__(self):
        self.config = load_config()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("SEARCH_ENGINE_ID")
        self.logger = logging.getLogger(__name__)

    def search_prevention_tips(self, fraud_type):
        """Busca dicas de prevenção para um tipo específico de golpe."""
        query = f"Como se prevenir de {fraud_type} Brasil 2025"
        try:
            service = build("customsearch", "v1", developerKey=self.api_key)
            result = service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=5
            ).execute()
            return [item.get("snippet", "") for item in result.get("items", [])]
        except HttpError as e:
            self.logger.error(f"Erro na API de busca: {e}")
            return []

    def generate_response(self, question, analysis_data):
        """Gera uma resposta educativa para uma pergunta do usuário."""
        question = question.lower()
        response = []

        # Extrai os tipos de golpes relevantes da análise
        fraud_types = analysis_data.get("golpes_por_tipo", {})
        top_frauds = sorted(fraud_types.items(), key=lambda x: x[1], reverse=True)[:3]

        # Tenta casar a pergunta com algum tipo de golpe
        matched_fraud = None
        for fraud_type in fraud_types:
            if fraud_type.lower() in question:
                matched_fraud = fraud_type
                break

        if matched_fraud:
            response.append(f"### Sobre o {matched_fraud}\n")
            response.append(f"O **{matched_fraud}** é um dos golpes mais comuns no Brasil, com **{fraud_types[matched_fraud]} casos** registrados em nossa base.\n")

            # Busca dicas de prevenção
            tips = self.search_prevention_tips(matched_fraud)
            if tips:
                response.append("#### Como se prevenir:\n")
                for i, tip in enumerate(tips[:3], 1):
                    response.append(f"{i}. {tip}\n")
            else:
                response.append("#### Dicas gerais de prevenção:\n")
                response.append("1. Verifique sempre a fonte antes de clicar em links ou compartilhar informações.\n")
                response.append("2. Desconfie de promessas de ganhos rápidos ou mensagens urgentes.\n")
                response.append("3. Use autenticação de dois fatores em suas contas.\n")

            # Exemplo prático
            response.append("#### Exemplo prático:\n")
            if "pix" in matched_fraud.lower():
                response.append("Você recebe um SMS dizendo que ganhou um sorteio e precisa fazer um PIX para liberar o prêmio. **O que fazer?** Ignore a mensagem e nunca faça transferências sem verificar diretamente com a instituição oficial.\n")
            else:
                response.append("Você recebe um e-mail pedindo para atualizar seus dados bancários. **O que fazer?** Não clique no link e entre em contato com seu banco pelos canais oficiais.\n")
        else:
            response.append("### Informações Gerais sobre Golpes Financeiros\n")
            response.append("Os golpes financeiros estão cada vez mais sofisticados. Aqui estão os três tipos mais comuns atualmente:\n")
            for fraud, count in top_frauds:
                response.append(f"- **{fraud}**: {count} casos registrados.\n")
            response.append("\n#### Dicas gerais de prevenção:\n")
            response.append("1. Nunca compartilhe senhas ou códigos de verificação.\n")
            response.append("2. Desconfie de mensagens ou ligações inesperadas.\n")
            response.append("3. Consulte fontes oficiais antes de tomar qualquer ação.\n")

        return "\n".join(response)

    def run(self, question, analysis_data):
        """Executa a pipeline do professor."""
        return self.generate_response(question, analysis_data)