import logging
from datetime import datetime
from src.engineer import EngineerAgent
from src.analyst import AnalystAgent
from src.professor import ProfessorAgent
from src.utils import setup_logging

setup_logging()

class Orchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engineer = EngineerAgent()
        self.analyst = AnalystAgent()
        self.professor = ProfessorAgent()

    def run_pipeline(self):
        """Executa toda a pipeline de coleta e análise de dados."""
        self.logger.info("Iniciando a pipeline")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # executa o agente engineer
        self.logger.info("Executando o agente engineer")
        fraud_data = self.engineer.run(date_str)
        
        # executa o agente analyst
        self.logger.info("Executando o agente analyst")
        analysis = self.analyst.run()
        
        self.logger.info("Pipeline concluída")
        return fraud_data, analysis

    def get_educational_response(self, question, analysis_data):
        """Obtém uma resposta educativa para uma pergunta do usuário."""
        self.logger.info(f"Processando a pergunta: {question}")
        return self.professor.run(question, analysis_data)

if __name__ == "__main__":
    orchestrator = Orchestrator()
    fraud_data, analysis = orchestrator.run_pipeline()
    print("Análise:", analysis)
