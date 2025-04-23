"""
Módulo de configuração para os agentes do DOU.

Este módulo implementa a classe Config para gerenciar as configurações
globais do sistema de agentes.
"""

import os
import json
from pathlib import Path

from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('utils.config')

class Config:
    """
    Classe para gerenciar configurações do sistema de agentes.
    
    Esta classe carrega configurações de um arquivo JSON e fornece
    métodos para acessar essas configurações.
    """
    
    # Configurações padrão
    DEFAULT_CONFIG = {
        # Diretórios
        'dados_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dados'),
        'cache_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dados', 'cache'),
        
        # Configurações do Agente Coletor
        'usar_cache': True,
        'timeout': 30,
        'max_retries': 3,
        'delay_entre_requisicoes': (1, 3),
        'usar_selenium': False,
        'verificar_secoes_extras': True,
        
        # Configurações do Agente Processador
        'modelo_spacy': 'pt_core_news_lg',
        'tamanho_maximo_resumo': 200,
        'limiar_similaridade': 0.7,
        
        # Configurações do Agente Organizador
        'formato_saida': 'csv',
        'separador_csv': ',',
        'encoding_csv': 'utf-8',
        
        # Configurações do Agente de Busca
        'elasticsearch_host': 'localhost',
        'elasticsearch_port': 9200,
        'tamanho_indice': 10000,
        
        # Configurações do Agente Coordenador
        'intervalo_monitoramento': 60,
        'usar_mensageria': False,
        'rabbitmq_host': 'localhost',
        'rabbitmq_port': 5672,
        
        # Configurações de logging
        'nivel_log': 'INFO',
        'arquivo_log': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'agentes_dou.log'),
    }
    
    def __init__(self, config_file=None):
        """
        Inicializa o objeto de configuração.
        
        Args:
            config_file (str): Caminho para o arquivo de configuração JSON
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file:
            self.carregar_arquivo(config_file)
        
        # Garante que os diretórios necessários existam
        self._criar_diretorios()
    
    def carregar_arquivo(self, config_file):
        """
        Carrega configurações de um arquivo JSON.
        
        Args:
            config_file (str): Caminho para o arquivo de configuração
            
        Returns:
            bool: True se o carregamento foi bem-sucedido, False caso contrário
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_usuario = json.load(f)
            
            # Atualiza as configurações padrão com as do usuário
            self.config.update(config_usuario)
            logger.info(f"Configurações carregadas de {config_file}")
            return True
        
        except Exception as e:
            logger.warning(f"Erro ao carregar configurações de {config_file}: {str(e)}")
            logger.info("Usando configurações padrão")
            return False
    
    def get(self, chave, padrao=None):
        """
        Retorna o valor de uma configuração.
        
        Args:
            chave (str): Nome da configuração
            padrao: Valor padrão caso a configuração não exista
            
        Returns:
            Valor da configuração ou o valor padrão
        """
        return self.config.get(chave, padrao)
    
    def set(self, chave, valor):
        """
        Define o valor de uma configuração.
        
        Args:
            chave (str): Nome da configuração
            valor: Novo valor para a configuração
        """
        self.config[chave] = valor
    
    def salvar(self, arquivo):
        """
        Salva as configurações em um arquivo JSON.
        
        Args:
            arquivo (str): Caminho para o arquivo de saída
            
        Returns:
            bool: True se o salvamento foi bem-sucedido, False caso contrário
        """
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configurações salvas em {arquivo}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao salvar configurações em {arquivo}: {str(e)}")
            return False
    
    def _criar_diretorios(self):
        """Cria os diretórios necessários para o funcionamento do sistema."""
        diretorios = [
            self.get('dados_dir'),
            self.get('cache_dir'),
            os.path.join(self.get('dados_dir'), 'brutos'),
            os.path.join(self.get('dados_dir'), 'processados'),
            os.path.join(self.get('dados_dir'), 'csv'),
            os.path.dirname(self.get('arquivo_log'))
        ]
        
        for diretorio in diretorios:
            try:
                Path(diretorio).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Diretório criado/verificado: {diretorio}")
            except Exception as e:
                logger.warning(f"Erro ao criar diretório {diretorio}: {str(e)}")
