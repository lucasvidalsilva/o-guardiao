import logging
import yaml
import os

def setup_logging():
    """Configure o registro de logs para a aplicação."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

def load_config():
    """Carregar configuração a partir do arquivo config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)