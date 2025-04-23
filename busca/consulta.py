"""
Módulo de consulta para o Agente de Busca.

Este módulo implementa a classe ProcessadorConsulta, responsável por
executar consultas no Elasticsearch e processar os resultados.
"""

import json
from elasticsearch import Elasticsearch
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('busca.consulta')

class ProcessadorConsulta:
    """
    Classe para processamento de consultas no Elasticsearch.
    
    Esta classe implementa métodos para executar consultas no Elasticsearch
    e processar os resultados da busca.
    """
    
    def __init__(self, host='localhost', port=9200):
        """
        Inicializa o processador de consulta.
        
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
            logger.warning("Operações de consulta não estarão disponíveis")
            self.es = None
    
    def buscar(self, index_name, query=None, filtros=None, max_resultados=100):
        """
        Executa uma consulta no Elasticsearch.
        
        Args:
            index_name (str): Nome do índice
            query (str): Consulta de busca
            filtros (dict): Filtros adicionais
            max_resultados (int): Número máximo de resultados
            
        Returns:
            dict: Resultados da busca
        """
        if not self.es:
            return {
                'success': False,
                'error': 'Elasticsearch não disponível',
                'total': 0,
                'took': 0,
                'hits': []
            }
        
        # Verifica se o índice existe
        if not self.es.indices.exists(index=index_name):
            logger.warning(f"Índice '{index_name}' não existe")
            return {
                'success': False,
                'error': f"Índice '{index_name}' não existe",
                'total': 0,
                'took': 0,
                'hits': []
            }
        
        # Constrói a consulta
        body = self._construir_consulta(query, filtros)
        
        try:
            # Executa a consulta
            response = self.es.search(
                index=index_name,
                body=body,
                size=max_resultados
            )
            
            # Processa os resultados
            resultados = {
                'success': True,
                'total': response['hits']['total']['value'],
                'took': response['took'],
                'hits': response['hits']['hits']
            }
            
            logger.info(f"Consulta executada com sucesso: {resultados['total']} resultados encontrados")
            return resultados
        
        except Exception as e:
            logger.error(f"Erro ao executar consulta: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'took': 0,
                'hits': []
            }
    
    def _construir_consulta(self, query=None, filtros=None):
        """
        Constrói o corpo da consulta Elasticsearch.
        
        Args:
            query (str): Consulta de busca
            filtros (dict): Filtros adicionais
            
        Returns:
            dict: Corpo da consulta Elasticsearch
        """
        # Inicializa o corpo da consulta
        body = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "highlight": {
                "fields": {
                    "titulo": {},
                    "resumo": {},
                    "texto_completo": {}
                }
            }
        }
        
        # Adiciona a consulta de texto, se fornecida
        if query:
            body["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["titulo^3", "resumo^2", "texto_completo", "entidades", "palavras_chave^2"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Adiciona filtros, se fornecidos
        if filtros:
            # Filtro de data
            if 'data_inicio' in filtros or 'data_fim' in filtros:
                range_filter = {"range": {"data_publicacao": {}}}
                
                if 'data_inicio' in filtros:
                    range_filter["range"]["data_publicacao"]["gte"] = filtros['data_inicio']
                
                if 'data_fim' in filtros:
                    range_filter["range"]["data_publicacao"]["lte"] = filtros['data_fim']
                
                body["query"]["bool"]["filter"].append(range_filter)
            
            # Filtro de seção
            if 'secao' in filtros:
                body["query"]["bool"]["filter"].append({
                    "term": {"secao": filtros['secao']}
                })
            
            # Filtro de tipo de documento
            if 'tipo_documento' in filtros:
                body["query"]["bool"]["filter"].append({
                    "term": {"tipo_documento": filtros['tipo_documento']}
                })
        
        # Se não houver consulta nem filtros, usa match_all
        if not query and (not filtros or not body["query"]["bool"]["filter"]):
            body["query"] = {"match_all": {}}
        
        return body
    
    def sugerir_termos(self, index_name, texto, campo='texto_completo', max_sugestoes=5):
        """
        Sugere termos relacionados a um texto.
        
        Args:
            index_name (str): Nome do índice
            texto (str): Texto para sugestão
            campo (str): Campo a ser usado para sugestão
            max_sugestoes (int): Número máximo de sugestões
            
        Returns:
            list: Lista de sugestões
        """
        if not self.es:
            return []
        
        # Verifica se o índice existe
        if not self.es.indices.exists(index=index_name):
            logger.warning(f"Índice '{index_name}' não existe")
            return []
        
        try:
            # Constrói a consulta de sugestão
            body = {
                "suggest": {
                    "text": texto,
                    "simple_phrase": {
                        "phrase": {
                            "field": campo,
                            "size": max_sugestoes,
                            "gram_size": 3,
                            "direct_generator": [{
                                "field": campo,
                                "suggest_mode": "always"
                            }],
                            "highlight": {
                                "pre_tag": "<em>",
                                "post_tag": "</em>"
                            }
                        }
                    }
                }
            }
            
            # Executa a consulta
            response = self.es.search(
                index=index_name,
                body=body
            )
            
            # Extrai as sugestões
            sugestoes = []
            for suggestion in response['suggest']['simple_phrase']:
                for option in suggestion['options']:
                    sugestoes.append({
                        'texto': option['text'],
                        'score': option['score']
                    })
            
            return sugestoes
        
        except Exception as e:
            logger.error(f"Erro ao sugerir termos: {str(e)}")
            return []
    
    def buscar_similares(self, index_name, doc_id, max_resultados=10):
        """
        Busca documentos similares a um documento específico.
        
        Args:
            index_name (str): Nome do índice
            doc_id (str): ID do documento de referência
            max_resultados (int): Número máximo de resultados
            
        Returns:
            dict: Resultados da busca
        """
        if not self.es:
            return {
                'success': False,
                'error': 'Elasticsearch não disponível',
                'total': 0,
                'took': 0,
                'hits': []
            }
        
        try:
            # Busca o documento de referência
            try:
                doc = self.es.get(index=index_name, id=doc_id)
            except:
                logger.error(f"Documento com ID '{doc_id}' não encontrado")
                return {
                    'success': False,
                    'error': f"Documento com ID '{doc_id}' não encontrado",
                    'total': 0,
                    'took': 0,
                    'hits': []
                }
            
            # Extrai o texto do documento
            source = doc['_source']
            texto = " ".join([
                source.get('titulo', ''),
                source.get('resumo', ''),
                source.get('texto_completo', '')
            ])
            
            # Constrói a consulta de similaridade
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "more_like_this": {
                                    "fields": ["titulo", "resumo", "texto_completo"],
                                    "like": texto,
                                    "min_term_freq": 1,
                                    "max_query_terms": 12,
                                    "min_doc_freq": 1
                                }
                            }
                        ],
                        "must_not": [
                            {
                                "ids": {
                                    "values": [doc_id]
                                }
                            }
                        ]
                    }
                }
            }
            
            # Executa a consulta
            response = self.es.search(
                index=index_name,
                body=body,
                size=max_resultados
            )
            
            # Processa os resultados
            resultados = {
                'success': True,
                'total': response['hits']['total']['value'],
                'took': response['took'],
                'hits': response['hits']['hits'],
                'documento_referencia': {
                    'id': doc_id,
                    'titulo': source.get('titulo', ''),
                    'resumo': source.get('resumo', '')
                }
            }
            
            logger.info(f"Busca de similares executada com sucesso: {resultados['total']} resultados encontrados")
            return resultados
        
        except Exception as e:
            logger.error(f"Erro ao buscar documentos similares: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'took': 0,
                'hits': []
            }
    
    def estatisticas_indice(self, index_name):
        """
        Obtém estatísticas sobre um índice.
        
        Args:
            index_name (str): Nome do índice
            
        Returns:
            dict: Estatísticas do índice
        """
        if not self.es:
            return {'success': False, 'error': 'Elasticsearch não disponível'}
        
        try:
            # Verifica se o índice existe
            if not self.es.indices.exists(index=index_name):
                logger.warning(f"Índice '{index_name}' não existe")
                return {'success': False, 'error': f"Índice '{index_name}' não existe"}
            
            # Obtém estatísticas do índice
            stats = self.es.indices.stats(index=index_name)
            
            # Obtém contagem de documentos
            count = self.es.count(index=index_name)
            
            # Processa as estatísticas
            return {
                'success': True,
                'nome': index_name,
                'documentos': count['count'],
                'tamanho': stats['indices'][index_name]['total']['store']['size_in_bytes'],
                'tamanho_formatado': stats['indices'][index_name]['total']['store']['size'],
                'operacoes': {
                    'busca': stats['indices'][index_name]['total']['search']['query_total'],
                    'indexacao': stats['indices'][index_name]['total']['indexing']['index_total']
                }
            }
        
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do índice '{index_name}': {str(e)}")
            return {'success': False, 'error': str(e)}
