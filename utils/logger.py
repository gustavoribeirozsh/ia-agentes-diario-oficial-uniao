"""
Módulo de logging para os agentes do DOU.

Este módulo implementa funções para configurar e utilizar
o sistema de logging em todos os agentes.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(nome, nivel=None, arquivo_log=None, max_bytes=10485760, backup_count=5):
    """
    Configura e retorna um logger.
    
    Args:
        nome (str): Nome do logger
        nivel (str): Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        arquivo_log (str): Caminho para o arquivo de log
        max_bytes (int): Tamanho máximo do arquivo de log antes de rotacionar
        backup_count (int): Número de arquivos de backup a manter
        
    Returns:
        logging.Logger: Logger configurado
    """
    # Obtém ou cria o logger
    logger = logging.getLogger(nome)
    
    # Evita configurar o mesmo logger múltiplas vezes
    if logger.handlers:
        return logger
    
    # Define o nível de logging
    nivel_log = nivel or os.environ.get('LOG_LEVEL', 'INFO')
    nivel_numerico = getattr(logging, nivel_log.upper(), logging.INFO)
    logger.setLevel(nivel_numerico)
    
    # Cria o formatador
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Adiciona handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Adiciona handler para arquivo, se especificado
    if arquivo_log:
        try:
            # Cria o diretório do arquivo de log, se necessário
            os.makedirs(os.path.dirname(arquivo_log), exist_ok=True)
            
            # Configura o handler de arquivo com rotação
            file_handler = RotatingFileHandler(
                arquivo_log,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Não foi possível configurar o log em arquivo: {str(e)}")
    
    return logger
