"""
Módulo de construção de CSV para o Agente Organizador.

Este módulo implementa a classe CSVBuilder, responsável por
gerar arquivos CSV, Excel ou JSON a partir dos dados processados.
"""

import csv
import json
import os
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('organizador.csv_builder')

class CSVBuilder:
    """
    Classe para construção de arquivos CSV a partir dos dados processados.
    
    Esta classe implementa métodos para gerar arquivos CSV, Excel ou JSON
    com os dados estruturados das publicações do DOU.
    """
    
    def __init__(self, separador=',', encoding='utf-8'):
        """
        Inicializa o construtor de CSV.
        
        Args:
            separador (str): Caractere separador para o CSV
            encoding (str): Encoding para o arquivo CSV
        """
        self.separador = separador
        self.encoding = encoding
    
    def gerar_csv(self, registros, arquivo_saida):
        """
        Gera um arquivo CSV com os registros fornecidos.
        
        Args:
            registros (list): Lista de dicionários com os dados
            arquivo_saida (str): Caminho para o arquivo de saída
            
        Returns:
            bool: True se a geração foi bem-sucedida, False caso contrário
        """
        try:
            # Garante que o diretório de saída existe
            os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
            
            # Se não há registros, cria um arquivo vazio com cabeçalho
            if not registros:
                logger.warning("Nenhum registro para gerar CSV")
                with open(arquivo_saida, 'w', encoding=self.encoding, newline='') as f:
                    writer = csv.writer(f, delimiter=self.separador)
                    writer.writerow(['data_publicacao', 'secao', 'numero_pagina', 'titulo', 'resumo'])
                return True
            
            # Obtém os campos a partir do primeiro registro
            campos = list(registros[0].keys())
            
            # Escreve o arquivo CSV
            with open(arquivo_saida, 'w', encoding=self.encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=campos, delimiter=self.separador)
                writer.writeheader()
                writer.writerows(registros)
            
            logger.info(f"Arquivo CSV gerado com sucesso: {arquivo_saida}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao gerar arquivo CSV: {str(e)}")
            return False
    
    def gerar_excel(self, registros, arquivo_saida):
        """
        Gera um arquivo Excel com os registros fornecidos.
        
        Args:
            registros (list): Lista de dicionários com os dados
            arquivo_saida (str): Caminho para o arquivo de saída
            
        Returns:
            bool: True se a geração foi bem-sucedida, False caso contrário
        """
        try:
            # Tenta importar pandas
            import pandas as pd
            
            # Garante que o diretório de saída existe
            os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
            
            # Converte os registros para um DataFrame
            df = pd.DataFrame(registros)
            
            # Salva como Excel
            df.to_excel(arquivo_saida, index=False, engine='openpyxl')
            
            logger.info(f"Arquivo Excel gerado com sucesso: {arquivo_saida}")
            return True
        
        except ImportError:
            logger.error("Biblioteca pandas não encontrada. Gerando CSV como alternativa.")
            # Fallback para CSV
            return self.gerar_csv(registros, arquivo_saida.replace('.xlsx', '.csv'))
        
        except Exception as e:
            logger.error(f"Erro ao gerar arquivo Excel: {str(e)}")
            return False
    
    def gerar_json(self, registros, arquivo_saida):
        """
        Gera um arquivo JSON com os registros fornecidos.
        
        Args:
            registros (list): Lista de dicionários com os dados
            arquivo_saida (str): Caminho para o arquivo de saída
            
        Returns:
            bool: True se a geração foi bem-sucedida, False caso contrário
        """
        try:
            # Garante que o diretório de saída existe
            os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
            
            # Estrutura o JSON
            dados_json = {
                'registros': registros,
                'total': len(registros)
            }
            
            # Escreve o arquivo JSON
            with open(arquivo_saida, 'w', encoding=self.encoding) as f:
                json.dump(dados_json, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Arquivo JSON gerado com sucesso: {arquivo_saida}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao gerar arquivo JSON: {str(e)}")
            return False
    
    def converter_csv_para_excel(self, arquivo_csv, arquivo_excel=None):
        """
        Converte um arquivo CSV existente para Excel.
        
        Args:
            arquivo_csv (str): Caminho para o arquivo CSV
            arquivo_excel (str): Caminho para o arquivo Excel de saída
            
        Returns:
            bool: True se a conversão foi bem-sucedida, False caso contrário
        """
        try:
            # Tenta importar pandas
            import pandas as pd
            
            # Define o arquivo de saída se não for especificado
            if not arquivo_excel:
                arquivo_excel = os.path.splitext(arquivo_csv)[0] + '.xlsx'
            
            # Garante que o diretório de saída existe
            os.makedirs(os.path.dirname(arquivo_excel), exist_ok=True)
            
            # Lê o CSV
            df = pd.read_csv(arquivo_csv, sep=self.separador, encoding=self.encoding)
            
            # Salva como Excel
            df.to_excel(arquivo_excel, index=False, engine='openpyxl')
            
            logger.info(f"Arquivo CSV convertido para Excel com sucesso: {arquivo_excel}")
            return True
        
        except ImportError:
            logger.error("Biblioteca pandas não encontrada. Não é possível converter para Excel.")
            return False
        
        except Exception as e:
            logger.error(f"Erro ao converter CSV para Excel: {str(e)}")
            return False
    
    def converter_excel_para_csv(self, arquivo_excel, arquivo_csv=None):
        """
        Converte um arquivo Excel existente para CSV.
        
        Args:
            arquivo_excel (str): Caminho para o arquivo Excel
            arquivo_csv (str): Caminho para o arquivo CSV de saída
            
        Returns:
            bool: True se a conversão foi bem-sucedida, False caso contrário
        """
        try:
            # Tenta importar pandas
            import pandas as pd
            
            # Define o arquivo de saída se não for especificado
            if not arquivo_csv:
                arquivo_csv = os.path.splitext(arquivo_excel)[0] + '.csv'
            
            # Garante que o diretório de saída existe
            os.makedirs(os.path.dirname(arquivo_csv), exist_ok=True)
            
            # Lê o Excel
            df = pd.read_excel(arquivo_excel, engine='openpyxl')
            
            # Salva como CSV
            df.to_csv(arquivo_csv, sep=self.separador, encoding=self.encoding, index=False)
            
            logger.info(f"Arquivo Excel convertido para CSV com sucesso: {arquivo_csv}")
            return True
        
        except ImportError:
            logger.error("Biblioteca pandas não encontrada. Não é possível converter de Excel.")
            return False
        
        except Exception as e:
            logger.error(f"Erro ao converter Excel para CSV: {str(e)}")
            return False
