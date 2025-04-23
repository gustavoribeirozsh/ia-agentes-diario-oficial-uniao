"""
Módulo de indexação para o Agente de Busca.

Este módulo implementa a classe Indexador, responsável por
indexar os dados organizados do DOU no Elasticsearch.
"""

import os
import json
import csv
import pandas as pd
from elasticsearch import Elasticsearch, helpers
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('busca.indexador')

class Indexador:
    """
    Classe para indexação de dados do DOU no Elasticsearch.
    
    Esta classe implementa métodos para indexar dados organizados
    do DOU em um índice Elasticsearch para busca eficiente.
    """
    
    def __init__(self, host='localhost', port=9200):
        """
        Inicializa o indexador.
        
        Args:
            host (str): Host do servidor Elasticsearch
            port (int): Porta do servidor Elasticsearch
        """
        self.es_url = f"http://{host}:{port}"
        
        try:
            self.es = Elasticsearch([self.es_url])
            logger.info(f"Conexão estabelecida com Elasticsearch em {self.es_url}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Elasticsearch em {self.es_url}: {str(e)}")
            logger.warning("Operações de indexação não estarão disponíveis")
            self.es = None
    
    def _criar_indice(self, index_name):
        """
        Cria um índice no Elasticsearch com o mapeamento adequado.
        
        Args:
            index_name (str): Nome do índice
            
        Returns:
            bool: True se a criação foi bem-sucedida, False caso contrário
        """
        if not self.es:
            logger.error("Elasticsearch não disponível")
            return False
        
        # Verifica se o índice já existe
        if self.es.indices.exists(index=index_name):
            logger.info(f"Índice '{index_name}' já existe")
            return True
        
        # Define o mapeamento do índice
        mappings = {
            "mappings": {
                "properties": {
                    "data_publicacao": {
                        "type": "date",
                        "format": "yyyy-MM-dd||yyyy/MM/dd"
                    },
                    "secao": {
                        "type": "keyword"
                    },
                    "numero_pagina": {
                        "type": "keyword"
                    },
                    "titulo": {
                        "type": "text",
                        "analyzer": "portuguese"
                    },
                    "resumo": {
                        "type": "text",
                        "analyzer": "portuguese"
                    },
                    "entidades": {
                        "type": "text",
                        "analyzer": "portuguese"
                    },
                    "palavras_chave": {
                        "type": "text",
                        "analyzer": "portuguese",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "tipo_documento": {
                        "type": "keyword"
                    },
                    "datas_mencionadas": {
                        "type": "text"
                    },
                    "valores_monetarios": {
                        "type": "text"
                    },
                    "numeros_processos": {
                        "type": "text"
                    },
                    "cnpj": {
                        "type": "text"
                    },
                    "cpf": {
                        "type": "text"
                    },
                    "texto_completo": {
                        "type": "text",
                        "analyzer": "portuguese"
                    }
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "portuguese": {
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "portuguese_stop",
                                "portuguese_stemmer"
                            ]
                        }
                    },
                    "filter": {
                        "portuguese_stop": {
                            "type": "stop",
                            "stopwords": "_portuguese_"
                        },
                        "portuguese_stemmer": {
                            "type": "stemmer",
                            "language": "portuguese"
                        }
                    }
                }
            }
        }
        
        try:
            # Cria o índice com o mapeamento
            self.es.indices.create(index=index_name, body=mappings)
            logger.info(f"Índice '{index_name}' criado com sucesso")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao criar índice '{index_name}': {str(e)}")
            return False
    
    def indexar_arquivo(self, arquivo, index_name):
        """
        Indexa um arquivo CSV ou JSON no Elasticsearch.
        
        Args:
            arquivo (str): Caminho para o arquivo
            index_name (str): Nome do índice
            
        Returns:
            dict: Resultado da indexação
        """
        if not self.es:
            return {'success': False, 'error': 'Elasticsearch não disponível', 'total': 0}
        
        # Cria o índice se não existir
        if not self._criar_indice(index_name):
            return {'success': False, 'error': 'Falha ao criar índice', 'total': 0}
        
        # Determina o tipo de arquivo
        ext = os.path.splitext(arquivo)[1].lower()
        
        try:
            # Carrega os dados do arquivo
            if ext == '.csv':
                dados = self._carregar_csv(arquivo)
            elif ext == '.json':
                dados = self._carregar_json(arquivo)
            elif ext == '.xlsx' or ext == '.xls':
                dados = self._carregar_excel(arquivo)
            else:
                return {'success': False, 'error': f'Formato de arquivo não suportado: {ext}', 'total': 0}
            
            # Indexa os dados
            return self._indexar_dados(dados, index_name)
        
        except Exception as e:
            logger.error(f"Erro ao indexar arquivo {arquivo}: {str(e)}")
            return {'success': False, 'error': str(e), 'total': 0}
    
    def indexar_diretorio(self, diretorio, index_name):
        """
        Indexa todos os arquivos CSV e JSON em um diretório.
        
        Args:
            diretorio (str): Caminho para o diretório
            index_name (str): Nome do índice
            
        Returns:
            dict: Resultado da indexação
        """
        if not self.es:
            return {'success': False, 'error': 'Elasticsearch não disponível', 'total': 0}
        
        # Cria o índice se não existir
        if not self._criar_indice(index_name):
            return {'success': False, 'error': 'Falha ao criar índice', 'total': 0}
        
        # Resultado acumulado
        resultado = {'success': True, 'total': 0, 'arquivos': []}
        
        # Percorre os arquivos do diretório
        for arquivo in os.listdir(diretorio):
            caminho = os.path.join(diretorio, arquivo)
            
            # Ignora diretórios
            if os.path.isdir(caminho):
                continue
            
            # Verifica a extensão
            ext = os.path.splitext(arquivo)[1].lower()
            if ext not in ['.csv', '.json', '.xlsx', '.xls']:
                continue
            
            # Indexa o arquivo
            logger.info(f"Indexando arquivo: {caminho}")
            resultado_arquivo = self.indexar_arquivo(caminho, index_name)
            
            # Acumula o resultado
            resultado['total'] += resultado_arquivo.get('total', 0)
            resultado['arquivos'].append({
                'arquivo': caminho,
                'success': resultado_arquivo.get('success', False),
                'total': resultado_arquivo.get('total', 0),
                'error': resultado_arquivo.get('error', None)
            })
            
            # Se algum arquivo falhar, marca o resultado como falha
            if not resultado_arquivo.get('success', False):
                resultado['success'] = False
        
        return resultado
    
    def _carregar_csv(self, arquivo):
        """
        Carrega dados de um arquivo CSV.
        
        Args:
            arquivo (str): Caminho para o arquivo CSV
            
        Returns:
            list: Lista de dicionários com os dados
        """
        try:
            # Tenta usar pandas para carregar o CSV
            df = pd.read_csv(arquivo, encoding='utf-8')
            return df.to_dict('records')
        except:
            # Fallback para o módulo csv
            dados = []
            with open(arquivo, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dados.append(row)
            return dados
    
    def _carregar_json(self, arquivo):
        """
        Carrega dados de um arquivo JSON.
        
        Args:
            arquivo (str): Caminho para o arquivo JSON
            
        Returns:
            list: Lista de dicionários com os dados
        """
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Verifica se os dados estão em formato de lista ou dentro de uma chave
        if isinstance(dados, list):
            return dados
        elif isinstance(dados, dict) and 'registros' in dados:
            return dados['registros']
        elif isinstance(dados, dict):
            # Tenta extrair registros de outras estruturas comuns
            for chave in ['dados', 'items', 'results', 'documents']:
                if chave in dados and isinstance(dados[chave], list):
                    return dados[chave]
            
            # Se não encontrar uma lista, retorna o próprio dicionário como um item
            return [dados]
        else:
            return []
    
    def _carregar_excel(self, arquivo):
        """
        Carrega dados de um arquivo Excel.
        
        Args:
            arquivo (str): Caminho para o arquivo Excel
            
        Returns:
            list: Lista de dicionários com os dados
        """
        try:
            df = pd.read_excel(arquivo)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo Excel {arquivo}: {str(e)}")
            return []
    
    def _indexar_dados(self, dados, index_name):
        """
        Indexa uma lista de documentos no Elasticsearch.
        
        Args:
            dados (list): Lista de dicionários com os dados
            index_name (str): Nome do índice
            
        Returns:
            dict: Resultado da indexação
        """
        if not dados:
            return {'success': True, 'total': 0, 'message': 'Nenhum dado para indexar'}
        
        # Prepara os documentos para indexação em massa
        actions = []
        for i, doc in enumerate(dados):
            # Gera um ID único para o documento
            doc_id = doc.get('id', f"{index_name}_{i}")
            
            # Cria o texto completo para melhorar a busca
            texto_completo = " ".join([
                str(doc.get('titulo', '')),
                str(doc.get('resumo', '')),
                str(doc.get('entidades', '')),
                str(doc.get('palavras_chave', ''))
            ])
            
            # Adiciona o texto completo ao documento
            doc['texto_completo'] = texto_completo
            
            # Adiciona a ação de indexação
            actions.append({
                '_index': index_name,
                '_id': doc_id,
                '_source': doc
            })
        
        try:
            # Executa a indexação em massa
            resultado = helpers.bulk(self.es, actions)
            logger.info(f"Indexação concluída: {resultado[0]} documentos indexados")
            
            # Força um refresh do índice para tornar os documentos pesquisáveis imediatamente
            self.es.indices.refresh(index=index_name)
            
            return {'success': True, 'total': resultado[0]}
        
        except Exception as e:
            logger.error(f"Erro durante a indexação em massa: {str(e)}")
            return {'success': False, 'error': str(e), 'total': 0}
    
    def limpar_indice(self, index_name):
        """
        Remove todos os documentos de um índice.
        
        Args:
            index_name (str): Nome do índice
            
        Returns:
            bool: True se a limpeza foi bem-sucedida, False caso contrário
        """
        if not self.es:
            logger.error("Elasticsearch não disponível")
            return False
        
        try:
            # Verifica se o índice existe
            if not self.es.indices.exists(index=index_name):
                logger.warning(f"Índice '{index_name}' não existe")
                return True
            
            # Remove todos os documentos do índice
            self.es.delete_by_query(
                index=index_name,
                body={"query": {"match_all": {}}}
            )
            
            logger.info(f"Índice '{index_name}' limpo com sucesso")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao limpar índice '{index_name}': {str(e)}")
            return False
    
    def remover_indice(self, index_name):
        """
        Remove um índice do Elasticsearch.
        
        Args:
            index_name (str): Nome do índice
            
        Returns:
            bool: True se a remoção foi bem-sucedida, False caso contrário
        """
        if not self.es:
            logger.error("Elasticsearch não disponível")
            return False
        
        try:
            # Verifica se o índice existe
            if not self.es.indices.exists(index=index_name):
                logger.warning(f"Índice '{index_name}' não existe")
                return True
            
            # Remove o índice
            self.es.indices.delete(index=index_name)
            
            logger.info(f"Índice '{index_name}' removido com sucesso")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao remover índice '{index_name}': {str(e)}")
            return False
