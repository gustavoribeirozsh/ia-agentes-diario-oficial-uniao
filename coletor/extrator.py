"""
Módulo de extração de dados do DOU.

Este módulo contém a classe DOUExtrator, responsável por acessar o site
oficial do DOU e extrair o conteúdo bruto das publicações.
"""

import os
import time
import random
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

from coletor.cache import Cache
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('coletor.extrator')

class DOUExtrator:
    """
    Classe responsável por extrair conteúdo do Diário Oficial da União.
    
    Esta classe implementa métodos para acessar o site do DOU, navegar pelas
    páginas e extrair o conteúdo das publicações.
    """
    
    BASE_URL = "https://www.in.gov.br/leiturajornal"
    
    def __init__(self, data, secao=3, modo='completo', max_paginas=None, config=None):
        """
        Inicializa o extrator do DOU.
        
        Args:
            data (datetime): Data alvo para extração
            secao (int): Seção do DOU (1, 2, 3 ou 'e' para extra)
            modo (str): Modo de coleta ('completo' ou 'incremental')
            max_paginas (int): Número máximo de páginas a coletar
            config (Config): Objeto de configuração
        """
        self.data = data
        self.secao = secao
        self.modo = modo
        self.max_paginas = max_paginas
        self.config = config or {}
        
        # Inicializa o cache se estiver habilitado
        cache_dir = self.config.get('cache_dir', os.path.join('..', 'dados', 'cache'))
        self.usar_cache = self.config.get('usar_cache', True)
        if self.usar_cache:
            self.cache = Cache(cache_dir)
        
        # Configurações para requisições
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.delay_entre_requisicoes = self.config.get('delay_entre_requisicoes', (1, 3))
        
        # Configurações para Selenium (quando necessário)
        self.usar_selenium = self.config.get('usar_selenium', False)
        self.selenium_timeout = self.config.get('selenium_timeout', 30)
    
    def _formatar_url(self):
        """
        Formata a URL para acessar a seção específica do DOU na data desejada.
        
        Returns:
            str: URL formatada
        """
        data_formatada = self.data.strftime('%d-%m-%Y')
        return f"{self.BASE_URL}?secao=dou{self.secao}&data={data_formatada}"
    
    def _esperar_entre_requisicoes(self):
        """Implementa um delay entre requisições para evitar sobrecarga no servidor."""
        min_delay, max_delay = self.delay_entre_requisicoes
        time.sleep(random.uniform(min_delay, max_delay))
    
    def _fazer_requisicao(self, url, usar_selenium=False):
        """
        Faz uma requisição HTTP para a URL especificada.
        
        Args:
            url (str): URL para acessar
            usar_selenium (bool): Se deve usar Selenium para a requisição
            
        Returns:
            str: Conteúdo HTML da página
            
        Raises:
            Exception: Se a requisição falhar após todas as tentativas
        """
        # Verifica se o conteúdo está no cache
        if self.usar_cache:
            cached_content = self.cache.get(url)
            if cached_content:
                logger.debug(f"Conteúdo recuperado do cache para: {url}")
                return cached_content
        
        # Tenta fazer a requisição com retries
        for tentativa in range(1, self.max_retries + 1):
            try:
                if usar_selenium or self.usar_selenium:
                    return self._requisicao_selenium(url)
                else:
                    return self._requisicao_requests(url)
            except Exception as e:
                logger.warning(f"Tentativa {tentativa}/{self.max_retries} falhou para {url}: {str(e)}")
                if tentativa < self.max_retries:
                    # Backoff exponencial
                    time.sleep(2 ** tentativa)
                else:
                    logger.error(f"Todas as tentativas falharam para {url}")
                    raise
    
    def _requisicao_requests(self, url):
        """Faz uma requisição usando a biblioteca requests."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        # Salva no cache
        if self.usar_cache:
            self.cache.set(url, response.text)
        
        return response.text
    
    def _requisicao_selenium(self, url):
        """Faz uma requisição usando Selenium para páginas que requerem JavaScript."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
            
            # Espera a página carregar completamente
            WebDriverWait(driver, self.selenium_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Espera adicional para garantir que o JavaScript foi executado
            time.sleep(2)
            
            html_content = driver.page_source
            
            # Salva no cache
            if self.usar_cache:
                self.cache.set(url, html_content)
            
            return html_content
        finally:
            driver.quit()
    
    def _extrair_numero_paginas(self, html_content):
        """
        Extrai o número total de páginas da seção.
        
        Args:
            html_content (str): Conteúdo HTML da página inicial
            
        Returns:
            int: Número total de páginas
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Tenta encontrar o elemento que contém o número de páginas
        # Nota: A implementação exata depende da estrutura do site do DOU
        try:
            # Exemplo: busca por um elemento que contenha informação de paginação
            paginacao = soup.select('.paginacao span.total')
            if paginacao:
                return int(paginacao[0].text.strip())
            
            # Alternativa: busca por links de paginação e pega o maior número
            links_paginacao = soup.select('.paginacao a')
            if links_paginacao:
                numeros = []
                for link in links_paginacao:
                    try:
                        numeros.append(int(link.text.strip()))
                    except ValueError:
                        pass
                if numeros:
                    return max(numeros)
            
            # Se não encontrar, assume que há apenas uma página
            logger.warning("Não foi possível determinar o número total de páginas. Assumindo 1.")
            return 1
        
        except Exception as e:
            logger.error(f"Erro ao extrair número de páginas: {str(e)}")
            return 1
    
    def _extrair_conteudo_pagina(self, html_content, numero_pagina):
        """
        Extrai o conteúdo de uma página específica.
        
        Args:
            html_content (str): Conteúdo HTML da página
            numero_pagina (int): Número da página
            
        Returns:
            dict: Conteúdo estruturado da página
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extrai o conteúdo principal
        conteudo_principal = soup.select_one('#conteudo-dou')
        if not conteudo_principal:
            logger.warning(f"Conteúdo principal não encontrado na página {numero_pagina}")
            conteudo_principal = soup.select_one('main') or soup.body
        
        # Extrai os metadados da página
        metadados = self._extrair_metadados(soup)
        
        # Extrai as publicações da página
        publicacoes = self._extrair_publicacoes(soup)
        
        return {
            'numero_pagina': numero_pagina,
            'metadados': metadados,
            'html': str(conteudo_principal) if conteudo_principal else '',
            'texto': conteudo_principal.get_text(separator='\n', strip=True) if conteudo_principal else '',
            'publicacoes': publicacoes
        }
    
    def _extrair_metadados(self, soup):
        """
        Extrai metadados da página.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página
            
        Returns:
            dict: Metadados extraídos
        """
        metadados = {
            'titulo': '',
            'data_publicacao': '',
            'secao': self.secao,
        }
        
        # Tenta extrair o título
        titulo_elem = soup.select_one('h1') or soup.select_one('.titulo-dou')
        if titulo_elem:
            metadados['titulo'] = titulo_elem.get_text(strip=True)
        
        # Tenta extrair a data de publicação
        data_elem = soup.select_one('.data-dou') or soup.select_one('.publicacao-data')
        if data_elem:
            metadados['data_publicacao'] = data_elem.get_text(strip=True)
        else:
            metadados['data_publicacao'] = self.data.strftime('%d/%m/%Y')
        
        return metadados
    
    def _extrair_publicacoes(self, soup):
        """
        Extrai as publicações individuais da página.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup da página
            
        Returns:
            list: Lista de publicações extraídas
        """
        publicacoes = []
        
        # Tenta identificar os elementos que contêm publicações individuais
        # Nota: A implementação exata depende da estrutura do site do DOU
        itens_publicacao = soup.select('.item-dou') or soup.select('article') or soup.select('.materia')
        
        for item in itens_publicacao:
            try:
                # Extrai título da publicação
                titulo_elem = item.select_one('h2') or item.select_one('.titulo')
                titulo = titulo_elem.get_text(strip=True) if titulo_elem else 'Sem título'
                
                # Extrai corpo da publicação
                corpo_elem = item.select_one('.texto') or item.select_one('.conteudo')
                corpo = corpo_elem.get_text(separator='\n', strip=True) if corpo_elem else ''
                
                # Extrai identificador único (se disponível)
                id_elem = item.get('id') or item.select_one('.identificador')
                id_publicacao = id_elem if isinstance(id_elem, str) else id_elem.get_text(strip=True) if id_elem else ''
                
                publicacoes.append({
                    'id': id_publicacao,
                    'titulo': titulo,
                    'corpo': corpo,
                    'html': str(item)
                })
            except Exception as e:
                logger.warning(f"Erro ao extrair publicação: {str(e)}")
        
        return publicacoes
    
    def _verificar_secoes_extras(self):
        """
        Verifica se existem seções extras para a data especificada.
        
        Returns:
            list: Lista de URLs para seções extras
        """
        if self.secao != 'e':  # Só verifica se não estiver já buscando uma seção extra
            try:
                data_formatada = self.data.strftime('%d-%m-%Y')
                url = f"{self.BASE_URL}?data={data_formatada}"
                
                html_content = self._fazer_requisicao(url)
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Busca links para edições extras
                links_extras = []
                for link in soup.select('a'):
                    href = link.get('href', '')
                    texto = link.get_text(strip=True).lower()
                    if ('extra' in href.lower() or 'extra' in texto) and 'dou' in href.lower():
                        links_extras.append(urljoin(self.BASE_URL, href))
                
                return links_extras
            except Exception as e:
                logger.warning(f"Erro ao verificar seções extras: {str(e)}")
                return []
        return []
    
    def extrair(self):
        """
        Executa o processo de extração completo.
        
        Returns:
            dict: Dados extraídos do DOU
        """
        logger.info(f"Iniciando extração para {self.data.strftime('%d/%m/%Y')}, Seção {self.secao}")
        
        # Formata a URL inicial
        url_inicial = self._formatar_url()
        logger.info(f"URL inicial: {url_inicial}")
        
        # Faz a requisição inicial
        html_inicial = self._fazer_requisicao(url_inicial)
        
        # Extrai o número total de páginas
        total_paginas = self._extrair_numero_paginas(html_inicial)
        logger.info(f"Total de páginas identificadas: {total_paginas}")
        
        # Limita o número de páginas se especificado
        if self.max_paginas and self.max_paginas < total_paginas:
            logger.info(f"Limitando extração a {self.max_paginas} páginas")
            total_paginas = self.max_paginas
        
        # Extrai o conteúdo da primeira página
        paginas = [self._extrair_conteudo_pagina(html_inicial, 1)]
        
        # Extrai o conteúdo das páginas restantes
        for num_pagina in tqdm(range(2, total_paginas + 1), desc="Extraindo páginas"):
            # Formata a URL da página
            url_pagina = f"{url_inicial}&pagina={num_pagina}"
            
            # Faz a requisição
            self._esperar_entre_requisicoes()
            try:
                html_pagina = self._fazer_requisicao(url_pagina)
                pagina = self._extrair_conteudo_pagina(html_pagina, num_pagina)
                paginas.append(pagina)
            except Exception as e:
                logger.error(f"Erro ao extrair página {num_pagina}: {str(e)}")
        
        # Verifica se existem seções extras
        secoes_extras = []
        if self.config.get('verificar_secoes_extras', True):
            urls_extras = self._verificar_secoes_extras()
            if urls_extras:
                logger.info(f"Encontradas {len(urls_extras)} seções extras")
                for i, url_extra in enumerate(urls_extras, 1):
                    try:
                        self._esperar_entre_requisicoes()
                        html_extra = self._fazer_requisicao(url_extra)
                        secao_extra = {
                            'url': url_extra,
                            'conteudo': self._extrair_conteudo_pagina(html_extra, i)
                        }
                        secoes_extras.append(secao_extra)
                    except Exception as e:
                        logger.error(f"Erro ao extrair seção extra {i}: {str(e)}")
        
        # Monta o resultado final
        resultado = {
            'data': self.data.strftime('%Y-%m-%d'),
            'secao': self.secao,
            'total_paginas': total_paginas,
            'paginas': paginas,
            'secoes_extras': secoes_extras,
            'timestamp_extracao': datetime.now().isoformat()
        }
        
        logger.info(f"Extração concluída. Total de {len(paginas)} páginas extraídas.")
        return resultado
