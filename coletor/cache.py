"""
Módulo de cache para o Agente Coletor.

Este módulo implementa um sistema de cache para armazenar temporariamente
o conteúdo extraído do DOU, evitando requisições repetidas.
"""

import os
import json
import hashlib
import time
from datetime import datetime, timedelta

from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('coletor.cache')

class Cache:
    """
    Implementa um sistema de cache para armazenar conteúdo extraído do DOU.
    
    O cache armazena o conteúdo em arquivos no sistema de arquivos,
    organizados por hash da URL.
    """
    
    def __init__(self, cache_dir, validade_cache=timedelta(days=7)):
        """
        Inicializa o sistema de cache.
        
        Args:
            cache_dir (str): Diretório para armazenar os arquivos de cache
            validade_cache (timedelta): Tempo de validade do cache
        """
        self.cache_dir = cache_dir
        self.validade_cache = validade_cache
        
        # Cria o diretório de cache se não existir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Inicializa estatísticas
        self.hits = 0
        self.misses = 0
        
        logger.debug(f"Cache inicializado em {cache_dir}")
    
    def _gerar_chave(self, url):
        """
        Gera uma chave de cache a partir da URL.
        
        Args:
            url (str): URL para gerar a chave
            
        Returns:
            str: Chave de cache (hash MD5 da URL)
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _caminho_arquivo(self, chave):
        """
        Retorna o caminho completo para o arquivo de cache.
        
        Args:
            chave (str): Chave de cache
            
        Returns:
            str: Caminho completo para o arquivo
        """
        return os.path.join(self.cache_dir, f"{chave}.json")
    
    def get(self, url):
        """
        Recupera conteúdo do cache.
        
        Args:
            url (str): URL do conteúdo
            
        Returns:
            str: Conteúdo armazenado no cache, ou None se não encontrado ou expirado
        """
        chave = self._gerar_chave(url)
        caminho = self._caminho_arquivo(chave)
        
        if not os.path.exists(caminho):
            self.misses += 1
            return None
        
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Verifica se o cache expirou
            timestamp = datetime.fromisoformat(dados['timestamp'])
            if datetime.now() - timestamp > self.validade_cache:
                logger.debug(f"Cache expirado para {url}")
                self.misses += 1
                return None
            
            self.hits += 1
            return dados['conteudo']
        
        except Exception as e:
            logger.warning(f"Erro ao ler cache para {url}: {str(e)}")
            self.misses += 1
            return None
    
    def set(self, url, conteudo):
        """
        Armazena conteúdo no cache.
        
        Args:
            url (str): URL do conteúdo
            conteudo (str): Conteúdo a ser armazenado
            
        Returns:
            bool: True se o armazenamento foi bem-sucedido, False caso contrário
        """
        chave = self._gerar_chave(url)
        caminho = self._caminho_arquivo(chave)
        
        try:
            dados = {
                'url': url,
                'conteudo': conteudo,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False)
            
            logger.debug(f"Conteúdo armazenado em cache para {url}")
            return True
        
        except Exception as e:
            logger.warning(f"Erro ao armazenar cache para {url}: {str(e)}")
            return False
    
    def limpar_expirados(self):
        """
        Remove entradas expiradas do cache.
        
        Returns:
            int: Número de entradas removidas
        """
        removidos = 0
        
        for arquivo in os.listdir(self.cache_dir):
            if not arquivo.endswith('.json'):
                continue
            
            caminho = os.path.join(self.cache_dir, arquivo)
            
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                timestamp = datetime.fromisoformat(dados['timestamp'])
                if datetime.now() - timestamp > self.validade_cache:
                    os.remove(caminho)
                    removidos += 1
            
            except Exception as e:
                logger.warning(f"Erro ao verificar cache {arquivo}: {str(e)}")
        
        logger.info(f"Limpeza de cache concluída. {removidos} entradas removidas.")
        return removidos
    
    def estatisticas(self):
        """
        Retorna estatísticas de uso do cache.
        
        Returns:
            dict: Estatísticas de uso
        """
        total = self.hits + self.misses
        taxa_acertos = (self.hits / total) * 100 if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total': total,
            'taxa_acertos': f"{taxa_acertos:.2f}%",
            'entradas': len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
        }
