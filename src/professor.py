import logging
import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from src.utils import setup_logging, load_config

load_dotenv()
setup_logging()

class ProfessorAgent:
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

    def read_parquets(self):
        """Lê os arquivos engineer_data.parquet e analyst_data.parquet."""
        try:
            # Ler engineer_data.parquet
            engineer_path = os.path.join(self.data_dir, "engineer_data.parquet")
            if not os.path.exists(engineer_path):
                self.logger.warning(f"Arquivo {engineer_path} não encontrado")
                engineer_df = pd.DataFrame()
            else:
                engineer_df = pd.read_parquet(engineer_path, engine="pyarrow")
                self.logger.info(f"Lido {len(engineer_df)} registros de {engineer_path}")

            # Ler analyst_data.parquet
            analyst_path = os.path.join(self.data_dir, "analyst_data.parquet")
            if not os.path.exists(analyst_path):
                self.logger.warning(f"Arquivo {analyst_path} não encontrado")
                analyst_df = pd.DataFrame()
            else:
                analyst_df = pd.read_parquet(analyst_path, engine="pyarrow")
                self.logger.info(f"Lido {len(analyst_df)} registros de {analyst_path}")

            # Extrair métricas de analyst_data
            analysis = {}
            if not analyst_df.empty:
                for _, row in analyst_df.iterrows():
                    category = row["Categoria"]
                    subcategory = row["Subcategoria"]
                    value = row["Valor"]
                    if subcategory:
                        if category not in analysis:
                            analysis[category] = {}
                        analysis[category][subcategory] = value
                    else:
                        analysis[category] = value

            return engineer_df, analysis
        except Exception as e:
            self.logger.error(f"Erro ao ler arquivos Parquet: {e}")
            return pd.DataFrame(), {}

    def create_prompt(self, question, engineer_df, analysis):
        """Cria um prompt para o Gemini com base na pergunta e nos dados dos Parquet."""
        # Extrair informações relevantes dos Parquet
        context = []
        if not engineer_df.empty:
            context.append("### Dados detalhados de golpes financeiros (engineer_data.parquet):")
            for _, row in engineer_df.head(5).iterrows():  # Limitar a 5 registros para evitar prompt longo
                context.append(
                    f"- Fonte: {row['Fonte']}\n"
                    f"  Data: {row['Data da notícia']}\n"
                    f"  Tipo do golpe: {row['Tipo do golpe']}\n"
                    f"  Descrição: {row['Descrição breve do golpe']}\n"
                    f"  Canal: {row['Canal utilizado']}\n"
                    f"  Público alvo: {row['Público alvo']}\n"
                    f"  Impacto: {row['Estimativa de impacto ou prejuízo']}"
                )
        else:
            context.append("Nenhum dado detalhado de golpes disponível em engineer_data.parquet.")

        if analysis.get("golpes_por_tipo"):
            context.append("\n### Métricas agregadas (analyst_data.parquet):")
            context.append(f"Total de golpes: {analysis.get('total_golpes', 0)}")
            context.append("Tipos de golpes mais comuns:")
            for fraud_type, count in sorted(analysis.get("golpes_por_tipo", {}).items(), key=lambda x: x[1], reverse=True)[:3]:
                context.append(f"- {fraud_type}: {count} casos")
        else:
            context.append("Nenhuma métrica agregada disponível em analyst_data.parquet.")

        # Criar o prompt
        prompt = f"""
Você é um especialista em prevenção de golpes financeiros no Brasil. Sua tarefa é responder à pergunta do usuário de forma educativa, clara e formatada em Markdown, com base nos dados fornecidos e no seu conhecimento sobre golpes financeiros em 2025.

**Pergunta do usuário**: {question}

**Contexto (dados coletados em 2025):**
{'\n'.join(context)}

**Instruções:**
- Responda em Markdown, com seções claras (e.g., `### Sobre o [golpe]`, `#### Como se prevenir`).
- Se a pergunta mencionar um tipo de golpe específico, forneça detalhes sobre ele, incluindo sua frequência (se disponível no contexto) e dicas de prevenção específicas.
- Use os dados do contexto para embasar a resposta (e.g., cite tipos de golpes, canais, públicos alvos ou descrições).
- Se a pergunta for genérica, forneça uma visão geral dos golpes mais comuns no contexto, com dicas de prevenção.
- Inclua um exemplo prático de como identificar ou evitar o golpe (baseado no contexto ou no tipo de golpe).
- Não invente dados; se o contexto for insuficiente, use seu conhecimento geral, mas indique que os dados são limitados.
- A resposta deve ser concisa, com no máximo 500 palavras.

**Saída esperada (exemplo):**
```markdown
### Sobre o Phishing
O **Phishing** é um golpe comum, com X casos registrados. Ele envolve e-mails falsos que imitam bancos para roubar dados.

#### Como se prevenir
1. Não clique em links de e-mails suspeitos.
2. Verifique o remetente antes de responder.
3. Use autenticação de dois fatores.

#### Exemplo prático
Você recebe um e-mail pedindo para atualizar seus dados bancários. **O que fazer?** Não clique no link e contate seu banco diretamente.
```
"""
        return prompt

    def query_gemini(self, question, engineer_df, analysis):
        """Faz uma pergunta ao modelo Gemini e retorna a resposta."""
        try:
            prompt = self.create_prompt(question, engineer_df, analysis)
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            self.logger.debug(f"Resposta do Gemini: {response_text}")
            return response_text
        except Exception as e:
            self.logger.error(f"Erro ao consultar Gemini: {e}")
            return f"### Erro\nNão foi possível gerar uma resposta devido a um problema com o modelo. Tente novamente mais tarde."

    def generate_response(self, question, analysis_data):
        """Gera uma resposta educativa para uma pergunta do usuário."""
        # Ler os dados dos Parquet
        engineer_df, analysis = self.read_parquets()

        # Fazer a consulta ao Gemini
        response = self.query_gemini(question, engineer_df, analysis)

        # Se o Gemini falhar, fornecer uma resposta básica
        if "Erro" in response:
            response = f"### Resposta Temporária\nDesculpe, não consegui processar sua pergunta no momento. Tente novamente ou pergunte sobre um golpe específico, como {list(analysis.get('golpes_por_tipo', {}).keys())[0] if analysis.get('golpes_por_tipo') else 'Phishing'}."

        return response

    def run(self, question, analysis_data):
        """Executa a pipeline do professor."""
        return self.generate_response(question, analysis_data)