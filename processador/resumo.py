"""
Módulo de geração de resumos para o Agente Processador.

Este módulo implementa a classe GeradorResumo, responsável por
criar resumos automáticos dos textos extraídos do DOU.
"""

import re
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('processador.resumo')

class GeradorResumo:
    """
    Classe para geração de resumos automáticos dos textos do DOU.
    
    Esta classe implementa métodos para criar resumos concisos
    a partir de textos longos, utilizando técnicas de sumarização extrativa.
    """
    
    def __init__(self, tamanho_maximo=200, metodo='extrativo'):
        """
        Inicializa o gerador de resumos.
        
        Args:
            tamanho_maximo (int): Tamanho máximo do resumo em caracteres
            metodo (str): Método de sumarização ('extrativo' ou 'abstrativo')
        """
        self.tamanho_maximo = tamanho_maximo
        self.metodo = metodo
        
        # Inicializa recursos do NLTK
        try:
            # Verifica se os recursos necessários estão disponíveis
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.warning("Recursos do NLTK não encontrados. Tentando baixar...")
            try:
                nltk.download('punkt')
                nltk.download('stopwords')
                logger.info("Recursos do NLTK baixados com sucesso")
            except Exception as e:
                logger.error(f"Erro ao baixar recursos do NLTK: {str(e)}")
                logger.warning("Usando métodos alternativos para tokenização e stopwords")
        
        # Carrega stopwords em português
        try:
            self.stopwords = set(stopwords.words('portuguese'))
        except:
            # Fallback para lista básica de stopwords em português
            self.stopwords = {
                'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'até',
                'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'depois',
                'do', 'dos', 'e', 'ela', 'elas', 'ele', 'eles', 'em', 'entre', 'era',
                'eram', 'éramos', 'essa', 'essas', 'esse', 'esses', 'esta', 'estas', 'este',
                'esteja', 'estejam', 'estejamos', 'estes', 'esteve', 'estive', 'estivemos',
                'estiver', 'estivera', 'estiveram', 'estiverem', 'estivermos', 'estou', 'eu',
                'foi', 'fomos', 'for', 'fora', 'foram', 'forem', 'formos', 'fosse', 'fossem',
                'fui', 'há', 'haja', 'hajam', 'hajamos', 'hão', 'havemos', 'hei', 'houve',
                'houvemos', 'houver', 'houvera', 'houveram', 'houverei', 'houverem', 'houveremos',
                'houveria', 'houveriam', 'houvermos', 'houverá', 'houverão', 'houveríamos',
                'houverão', 'houvesse', 'houvessem', 'houvéramos', 'houvéssemos', 'isso', 'isto',
                'já', 'lhe', 'lhes', 'mais', 'mas', 'me', 'mesmo', 'meu', 'meus', 'minha',
                'minhas', 'muito', 'na', 'nas', 'nem', 'no', 'nos', 'nós', 'nossa', 'nossas',
                'nosso', 'nossos', 'num', 'numa', 'o', 'os', 'ou', 'para', 'pela', 'pelas',
                'pelo', 'pelos', 'por', 'qual', 'quando', 'que', 'quem', 'são', 'se', 'seja',
                'sejam', 'sejamos', 'sem', 'será', 'serão', 'seria', 'seriam', 'seríamos',
                'seu', 'seus', 'só', 'somos', 'sou', 'sua', 'suas', 'também', 'te', 'tem',
                'tém', 'temos', 'tenha', 'tenham', 'tenhamos', 'tenho', 'terá', 'terão',
                'teria', 'teriam', 'teríamos', 'teu', 'teus', 'teve', 'tinha', 'tinham',
                'tínhamos', 'tive', 'tivemos', 'tiver', 'tivera', 'tiveram', 'tiverem',
                'tivermos', 'tu', 'tua', 'tuas', 'um', 'uma', 'você', 'vocês', 'vos'
            }
    
    def gerar_resumo(self, texto):
        """
        Gera um resumo do texto fornecido.
        
        Args:
            texto (str): Texto a ser resumido
            
        Returns:
            str: Resumo gerado
        """
        if not texto or len(texto) <= self.tamanho_maximo:
            return texto
        
        if self.metodo == 'extrativo':
            return self._resumo_extrativo(texto)
        else:
            # Fallback para método extrativo se o abstrativo não estiver implementado
            return self._resumo_extrativo(texto)
    
    def _resumo_extrativo(self, texto):
        """
        Gera um resumo extrativo selecionando as sentenças mais importantes.
        
        Args:
            texto (str): Texto a ser resumido
            
        Returns:
            str: Resumo extrativo
        """
        # Pré-processamento do texto
        texto = self._pre_processar_texto(texto)
        
        try:
            # Tokeniza o texto em sentenças
            sentencas = sent_tokenize(texto, language='portuguese')
        except:
            # Fallback para tokenização simples
            sentencas = re.split(r'[.!?]+', texto)
            sentencas = [s.strip() for s in sentencas if s.strip()]
        
        if not sentencas:
            return ""
        
        # Se houver apenas uma sentença, retorna ela truncada
        if len(sentencas) == 1:
            return self._truncar_texto(sentencas[0])
        
        # Calcula a pontuação de cada sentença
        pontuacoes = self._pontuar_sentencas(sentencas)
        
        # Ordena as sentenças por pontuação
        sentencas_ordenadas = [sent for _, sent in sorted(
            zip(pontuacoes, sentencas), 
            key=lambda x: x[0], 
            reverse=True
        )]
        
        # Seleciona as sentenças mais importantes até atingir o tamanho máximo
        resumo = ""
        for sentenca in sentencas_ordenadas:
            if len(resumo) + len(sentenca) + 1 <= self.tamanho_maximo:
                resumo += sentenca + " "
            else:
                break
        
        # Se não conseguiu incluir nenhuma sentença completa, trunca a primeira
        if not resumo:
            resumo = self._truncar_texto(sentencas_ordenadas[0])
        
        return resumo.strip()
    
    def _pre_processar_texto(self, texto):
        """
        Realiza pré-processamento no texto antes da geração do resumo.
        
        Args:
            texto (str): Texto original
            
        Returns:
            str: Texto pré-processado
        """
        # Remove quebras de linha e espaços extras
        texto = re.sub(r'\s+', ' ', texto)
        texto = texto.strip()
        
        return texto
    
    def _pontuar_sentencas(self, sentencas):
        """
        Calcula a pontuação de cada sentença com base na frequência de palavras.
        
        Args:
            sentencas (list): Lista de sentenças
            
        Returns:
            list: Lista de pontuações para cada sentença
        """
        # Tokeniza todas as palavras do texto
        palavras = []
        for sentenca in sentencas:
            palavras.extend(self._tokenizar_palavras(sentenca))
        
        # Calcula a frequência de cada palavra
        freq_palavras = FreqDist(palavras)
        
        # Calcula a pontuação de cada sentença
        pontuacoes = []
        for sentenca in sentencas:
            palavras_sentenca = self._tokenizar_palavras(sentenca)
            
            # Evita divisão por zero
            if not palavras_sentenca:
                pontuacoes.append(0)
                continue
            
            # Pontuação baseada na frequência das palavras
            pontuacao = sum(freq_palavras[palavra] for palavra in palavras_sentenca) / len(palavras_sentenca)
            
            # Bônus para sentenças no início do texto (primeiras 3 sentenças)
            if sentencas.index(sentenca) < 3:
                pontuacao *= 1.2
            
            pontuacoes.append(pontuacao)
        
        return pontuacoes
    
    def _tokenizar_palavras(self, texto):
        """
        Tokeniza um texto em palavras, removendo stopwords.
        
        Args:
            texto (str): Texto a ser tokenizado
            
        Returns:
            list: Lista de palavras relevantes
        """
        # Converte para minúsculas e remove pontuação
        texto = texto.lower()
        texto = re.sub(r'[^\w\s]', '', texto)
        
        # Tokeniza em palavras
        palavras = texto.split()
        
        # Remove stopwords
        palavras = [palavra for palavra in palavras if palavra not in self.stopwords]
        
        return palavras
    
    def _truncar_texto(self, texto):
        """
        Trunca um texto para o tamanho máximo definido.
        
        Args:
            texto (str): Texto a ser truncado
            
        Returns:
            str: Texto truncado
        """
        if len(texto) <= self.tamanho_maximo:
            return texto
        
        # Trunca no último espaço antes do limite
        texto_truncado = texto[:self.tamanho_maximo]
        ultimo_espaco = texto_truncado.rfind(' ')
        
        if ultimo_espaco > 0:
            texto_truncado = texto_truncado[:ultimo_espaco]
        
        return texto_truncado + "..."
