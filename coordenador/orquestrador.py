"""
Módulo de orquestração para o Agente Coordenador.

Este módulo implementa a classe Orquestrador, responsável por
coordenar a execução dos diferentes agentes do sistema.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
import glob
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('coordenador.orquestrador')

class Orquestrador:
    """
    Classe para orquestração dos agentes do DOU.
    
    Esta classe implementa métodos para coordenar a execução
    dos diferentes agentes do sistema, gerenciando o fluxo de
    trabalho completo.
    """
    
    def __init__(self, config):
        """
        Inicializa o orquestrador.
        
        Args:
            config (Config): Objeto de configuração
        """
        self.config = config
        self.python_exec = sys.executable
    
    def executar_coleta(self, data, secao, output_dir):
        """
        Executa o Agente Coletor para extrair dados do DOU.
        
        Args:
            data (datetime): Data alvo
            secao (int): Seção do DOU
            output_dir (str): Diretório de saída
            
        Returns:
            str: Caminho para o arquivo de saída gerado
        """
        logger.info(f"Executando Agente Coletor para {data.strftime('%d-%m-%Y')}, Seção {secao}")
        
        # Formata a data no formato esperado pelo Agente Coletor
        data_str = data.strftime('%d-%m-%Y')
        
        # Define o diretório de saída para os dados brutos
        brutos_dir = os.path.join(output_dir, 'brutos')
        os.makedirs(brutos_dir, exist_ok=True)
        
        # Constrói o comando para executar o Agente Coletor
        cmd = [
            self.python_exec,
            '-m', 'coletor.main',
            '--data', data_str,
            '--secao', str(secao),
            '--output', brutos_dir
        ]
        
        # Adiciona parâmetros adicionais se configurados
        if self.config.get('max_paginas'):
            cmd.extend(['--max-paginas', str(self.config.get('max_paginas'))])
        
        # Executa o comando
        logger.debug(f"Executando comando: {' '.join(cmd)}")
        try:
            resultado = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug(f"Saída do Agente Coletor: {resultado.stdout}")
            
            # Determina o arquivo de saída gerado
            arquivo_saida = os.path.join(brutos_dir, f"{data.strftime('%Y-%m-%d')}_secao{secao}.json")
            
            # Verifica se o arquivo foi gerado
            if not os.path.exists(arquivo_saida):
                logger.warning(f"Arquivo de saída não encontrado: {arquivo_saida}")
                # Tenta encontrar o arquivo mais recente
                arquivo_saida = self.encontrar_arquivo_mais_recente(brutos_dir, f"{data.strftime('%Y-%m-%d')}_secao{secao}")
                if not arquivo_saida:
                    raise FileNotFoundError(f"Nenhum arquivo de saída encontrado para {data.strftime('%Y-%m-%d')}, Seção {secao}")
            
            logger.info(f"Coleta concluída. Arquivo gerado: {arquivo_saida}")
            return arquivo_saida
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar Agente Coletor: {e}")
            logger.error(f"Saída de erro: {e.stderr}")
            raise RuntimeError(f"Falha na execução do Agente Coletor: {e}")
    
    def executar_processamento(self, arquivo_entrada, output_dir):
        """
        Executa o Agente Processador para transformar dados brutos em estruturados.
        
        Args:
            arquivo_entrada (str): Caminho para o arquivo de entrada
            output_dir (str): Diretório de saída
            
        Returns:
            str: Caminho para o arquivo de saída gerado
        """
        logger.info(f"Executando Agente Processador para {arquivo_entrada}")
        
        # Define o diretório de saída para os dados processados
        processados_dir = os.path.join(output_dir, 'processados')
        os.makedirs(processados_dir, exist_ok=True)
        
        # Define o arquivo de saída
        nome_base = os.path.basename(arquivo_entrada)
        arquivo_saida = os.path.join(processados_dir, f"processado_{nome_base}")
        
        # Constrói o comando para executar o Agente Processador
        cmd = [
            self.python_exec,
            '-m', 'processador.main',
            '--input', arquivo_entrada,
            '--output', arquivo_saida
        ]
        
        # Adiciona parâmetros adicionais se configurados
        modelo = self.config.get('modelo_spacy')
        if modelo:
            cmd.extend(['--modelo', modelo])
        
        tamanho_resumo = self.config.get('tamanho_maximo_resumo')
        if tamanho_resumo:
            cmd.extend(['--tamanho-resumo', str(tamanho_resumo)])
        
        # Executa o comando
        logger.debug(f"Executando comando: {' '.join(cmd)}")
        try:
            resultado = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug(f"Saída do Agente Processador: {resultado.stdout}")
            
            # Verifica se o arquivo foi gerado
            if not os.path.exists(arquivo_saida):
                logger.warning(f"Arquivo de saída não encontrado: {arquivo_saida}")
                # Tenta encontrar o arquivo mais recente
                arquivo_saida = self.encontrar_arquivo_mais_recente(processados_dir, f"processado_{nome_base}")
                if not arquivo_saida:
                    raise FileNotFoundError(f"Nenhum arquivo de saída encontrado para {arquivo_entrada}")
            
            logger.info(f"Processamento concluído. Arquivo gerado: {arquivo_saida}")
            return arquivo_saida
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar Agente Processador: {e}")
            logger.error(f"Saída de erro: {e.stderr}")
            raise RuntimeError(f"Falha na execução do Agente Processador: {e}")
    
    def executar_organizacao(self, arquivo_entrada, output_dir):
        """
        Executa o Agente Organizador para compilar dados em formato CSV.
        
        Args:
            arquivo_entrada (str): Caminho para o arquivo de entrada
            output_dir (str): Diretório de saída
            
        Returns:
            str: Caminho para o arquivo de saída gerado
        """
        logger.info(f"Executando Agente Organizador para {arquivo_entrada}")
        
        # Define o diretório de saída para os dados organizados
        formato = self.config.get('formato_saida', 'csv')
        organizados_dir = os.path.join(output_dir, formato)
        os.makedirs(organizados_dir, exist_ok=True)
        
        # Define o arquivo de saída
        nome_base = os.path.basename(arquivo_entrada)
        nome_base = nome_base.replace('processado_', '')
        nome_base = os.path.splitext(nome_base)[0]
        arquivo_saida = os.path.join(organizados_dir, f"{nome_base}.{formato}")
        
        # Constrói o comando para executar o Agente Organizador
        cmd = [
            self.python_exec,
            '-m', 'organizador.main',
            '--input', arquivo_entrada,
            '--output', arquivo_saida,
            '--formato', formato
        ]
        
        # Adiciona parâmetros adicionais se configurados
        separador = self.config.get('separador_csv')
        if separador:
            cmd.extend(['--separador', separador])
        
        encoding = self.config.get('encoding_csv')
        if encoding:
            cmd.extend(['--encoding', encoding])
        
        # Executa o comando
        logger.debug(f"Executando comando: {' '.join(cmd)}")
        try:
            resultado = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug(f"Saída do Agente Organizador: {resultado.stdout}")
            
            # Verifica se o arquivo foi gerado
            if not os.path.exists(arquivo_saida):
                logger.warning(f"Arquivo de saída não encontrado: {arquivo_saida}")
                # Tenta encontrar o arquivo mais recente
                arquivo_saida = self.encontrar_arquivo_mais_recente(organizados_dir, nome_base)
                if not arquivo_saida:
                    raise FileNotFoundError(f"Nenhum arquivo de saída encontrado para {arquivo_entrada}")
            
            logger.info(f"Organização concluída. Arquivo gerado: {arquivo_saida}")
            return arquivo_saida
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar Agente Organizador: {e}")
            logger.error(f"Saída de erro: {e.stderr}")
            raise RuntimeError(f"Falha na execução do Agente Organizador: {e}")
    
    def executar_indexacao(self, arquivo_entrada):
        """
        Executa o Agente de Busca para indexar dados no Elasticsearch.
        
        Args:
            arquivo_entrada (str): Caminho para o arquivo de entrada
            
        Returns:
            dict: Resultado da indexação
        """
        logger.info(f"Executando Agente de Busca para indexar {arquivo_entrada}")
        
        # Define o nome do índice
        index_name = self.config.get('elasticsearch_index', 'dou')
        
        # Constrói o comando para executar o Agente de Busca
        cmd = [
            self.python_exec,
            '-m', 'busca.main',
            '--input', arquivo_entrada,
            '--index', index_name,
            '--modo', 'indexar'
        ]
        
        # Executa o comando
        logger.debug(f"Executando comando: {' '.join(cmd)}")
        try:
            resultado = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug(f"Saída do Agente de Busca: {resultado.stdout}")
            
            # Tenta extrair o resultado da indexação da saída
            try:
                # Procura por um JSON na saída
                import re
                json_match = re.search(r'({.*})', resultado.stdout)
                if json_match:
                    resultado_indexacao = json.loads(json_match.group(1))
                else:
                    resultado_indexacao = {'success': True, 'message': 'Indexação concluída', 'total': 'desconhecido'}
            except:
                resultado_indexacao = {'success': True, 'message': 'Indexação concluída', 'total': 'desconhecido'}
            
            logger.info(f"Indexação concluída: {resultado_indexacao}")
            return resultado_indexacao
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar Agente de Busca: {e}")
            logger.error(f"Saída de erro: {e.stderr}")
            return {'success': False, 'error': str(e), 'total': 0}
    
    def executar_busca(self, query, filtros=None, max_resultados=100):
        """
        Executa o Agente de Busca para realizar consultas.
        
        Args:
            query (str): Consulta de busca
            filtros (dict): Filtros adicionais
            max_resultados (int): Número máximo de resultados
            
        Returns:
            dict: Resultados da busca
        """
        logger.info(f"Executando Agente de Busca para consulta: {query}")
        
        # Define o nome do índice
        index_name = self.config.get('elasticsearch_index', 'dou')
        
        # Constrói o comando para executar o Agente de Busca
        cmd = [
            self.python_exec,
            '-m', 'busca.main',
            '--index', index_name,
            '--query', query,
            '--modo', 'buscar',
            '--max-resultados', str(max_resultados),
            '--formato', 'json'
        ]
        
        # Adiciona filtros, se fornecidos
        if filtros:
            if 'data_inicio' in filtros:
                cmd.extend(['--data-inicio', filtros['data_inicio']])
            if 'data_fim' in filtros:
                cmd.extend(['--data-fim', filtros['data_fim']])
            if 'secao' in filtros:
                cmd.extend(['--secao', str(filtros['secao'])])
            if 'tipo_documento' in filtros:
                cmd.extend(['--tipo-documento', filtros['tipo_documento']])
        
        # Define um arquivo temporário para os resultados
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            arquivo_resultados = tmp.name
        
        cmd.extend(['--output', arquivo_resultados])
        
        # Executa o comando
        logger.debug(f"Executando comando: {' '.join(cmd)}")
        try:
            resultado = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug(f"Saída do Agente de Busca: {resultado.stdout}")
            
            # Carrega os resultados do arquivo
            try:
                with open(arquivo_resultados, 'r', encoding='utf-8') as f:
                    resultados = json.load(f)
                
                logger.info(f"Busca concluída: {resultados.get('total', 0)} resultados encontrados")
                return resultados
            
            except Exception as e:
                logger.error(f"Erro ao carregar resultados da busca: {str(e)}")
                return {'success': False, 'error': str(e), 'total': 0, 'hits': []}
            
            finally:
                # Remove o arquivo temporário
                try:
                    os.unlink(arquivo_resultados)
                except:
                    pass
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar Agente de Busca: {e}")
            logger.error(f"Saída de erro: {e.stderr}")
            return {'success': False, 'error': str(e), 'total': 0, 'hits': []}
    
    def encontrar_arquivo_mais_recente(self, diretorio, padrao):
        """
        Encontra o arquivo mais recente em um diretório que corresponde a um padrão.
        
        Args:
            diretorio (str): Diretório onde procurar
            padrao (str): Padrão para o nome do arquivo
            
        Returns:
            str: Caminho para o arquivo mais recente, ou None se não encontrado
        """
        # Verifica se o diretório existe
        if not os.path.exists(diretorio):
            logger.warning(f"Diretório não encontrado: {diretorio}")
            return None
        
        # Busca arquivos que correspondem ao padrão
        arquivos = glob.glob(os.path.join(diretorio, f"*{padrao}*"))
        
        if not arquivos:
            logger.warning(f"Nenhum arquivo encontrado para o padrão: {padrao}")
            return None
        
        # Retorna o arquivo mais recente
        return max(arquivos, key=os.path.getmtime)
    
    def verificar_status_agentes(self):
        """
        Verifica o status de todos os agentes.
        
        Returns:
            dict: Status de cada agente
        """
        status = {}
        
        # Verifica o Agente Coletor
        try:
            cmd = [self.python_exec, '-m', 'coletor.main', '--help']
            subprocess.run(cmd, check=True, capture_output=True)
            status['coletor'] = 'disponível'
        except:
            status['coletor'] = 'indisponível'
        
        # Verifica o Agente Processador
        try:
            cmd = [self.python_exec, '-m', 'processador.main', '--help']
            subprocess.run(cmd, check=True, capture_output=True)
            status['processador'] = 'disponível'
        except:
            status['processador'] = 'indisponível'
        
        # Verifica o Agente Organizador
        try:
            cmd = [self.python_exec, '-m', 'organizador.main', '--help']
            subprocess.run(cmd, check=True, capture_output=True)
            status['organizador'] = 'disponível'
        except:
            status['organizador'] = 'indisponível'
        
        # Verifica o Agente de Busca
        try:
            cmd = [self.python_exec, '-m', 'busca.main', '--help']
            subprocess.run(cmd, check=True, capture_output=True)
            status['busca'] = 'disponível'
        except:
            status['busca'] = 'indisponível'
        
        return status
