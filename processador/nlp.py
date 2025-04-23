"""
Módulo de processamento de linguagem natural para o Agente Processador.

Este módulo implementa a classe ProcessadorNLP, responsável por aplicar
técnicas de processamento de linguagem natural aos textos do DOU.
"""

import re
import spacy
from collections import Counter
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('processador.nlp')

class ProcessadorNLP:
    """
    Classe para processamento de linguagem natural dos textos do DOU.
    
    Esta classe implementa métodos para processar textos, extrair entidades,
    palavras-chave e metadados, e classificar documentos.
    """
    
    # Tipos de documentos que podem ser identificados
    TIPOS_DOCUMENTO = [
        'licitacao', 'contrato', 'extrato', 'aviso', 'edital', 
        'portaria', 'decreto', 'resolucao', 'despacho', 'outros'
    ]
    
    def __init__(self, modelo='pt_core_news_lg'):
        """
        Inicializa o processador NLP.
        
        Args:
            modelo (str): Nome do modelo spaCy a ser utilizado
        """
        try:
            self.nlp = spacy.load(modelo)
            logger.info(f"Modelo spaCy '{modelo}' carregado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo spaCy '{modelo}': {str(e)}")
            logger.warning("Tentando carregar modelo alternativo 'pt_core_news_sm'")
            try:
                self.nlp = spacy.load('pt_core_news_sm')
                logger.info("Modelo alternativo carregado com sucesso")
            except Exception as e2:
                logger.error(f"Erro ao carregar modelo alternativo: {str(e2)}")
                logger.critical("Não foi possível carregar nenhum modelo spaCy. Tentando baixar modelo...")
                try:
                    import subprocess
                    subprocess.run([sys.executable, "-m", "spacy", "download", "pt_core_news_sm"], check=True)
                    self.nlp = spacy.load('pt_core_news_sm')
                    logger.info("Modelo baixado e carregado com sucesso")
                except Exception as e3:
                    logger.critical(f"Falha ao baixar e carregar modelo: {str(e3)}")
                    raise RuntimeError("Não foi possível inicializar o processador NLP")
        
        # Configurações adicionais do pipeline
        self.configurar_pipeline()
    
    def configurar_pipeline(self):
        """Configura o pipeline de processamento do spaCy."""
        # Adiciona componentes personalizados se necessário
        pass
    
    def processar_texto(self, texto):
        """
        Processa um texto usando o pipeline do spaCy.
        
        Args:
            texto (str): Texto a ser processado
            
        Returns:
            spacy.tokens.Doc: Documento processado pelo spaCy
        """
        # Pré-processamento do texto
        texto = self._pre_processar_texto(texto)
        
        # Processa o texto com o spaCy
        return self.nlp(texto)
    
    def _pre_processar_texto(self, texto):
        """
        Realiza pré-processamento no texto antes de enviá-lo ao spaCy.
        
        Args:
            texto (str): Texto original
            
        Returns:
            str: Texto pré-processado
        """
        # Remove caracteres especiais e normaliza espaços
        texto = re.sub(r'\s+', ' ', texto)
        texto = texto.strip()
        
        return texto
    
    def extrair_entidades(self, doc):
        """
        Extrai entidades nomeadas do documento.
        
        Args:
            doc (spacy.tokens.Doc): Documento processado pelo spaCy
            
        Returns:
            list: Lista de entidades extraídas com tipo e texto
        """
        entidades = []
        
        for ent in doc.ents:
            entidades.append({
                'texto': ent.text,
                'tipo': ent.label_,
                'inicio': ent.start_char,
                'fim': ent.end_char
            })
        
        return entidades
    
    def extrair_palavras_chave(self, doc, n=10):
        """
        Extrai as principais palavras-chave do documento.
        
        Args:
            doc (spacy.tokens.Doc): Documento processado pelo spaCy
            n (int): Número máximo de palavras-chave a retornar
            
        Returns:
            list: Lista de palavras-chave com pontuação
        """
        # Filtra tokens relevantes (substantivos, verbos, adjetivos)
        tokens = [token.lemma_ for token in doc 
                 if not token.is_stop and not token.is_punct and not token.is_space
                 and token.pos_ in ('NOUN', 'VERB', 'ADJ') 
                 and len(token.text) > 3]
        
        # Conta frequência
        contador = Counter(tokens)
        
        # Retorna as n palavras mais frequentes
        return [{'palavra': palavra, 'frequencia': freq} 
                for palavra, freq in contador.most_common(n)]
    
    def extrair_metadados_texto(self, doc):
        """
        Extrai metadados do texto, como datas, valores monetários, etc.
        
        Args:
            doc (spacy.tokens.Doc): Documento processado pelo spaCy
            
        Returns:
            dict: Dicionário com metadados extraídos
        """
        metadados = {
            'datas': [],
            'valores_monetarios': [],
            'numeros_processos': [],
            'cnpj': [],
            'cpf': []
        }
        
        # Extrai datas
        padrao_data = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        metadados['datas'] = re.findall(padrao_data, doc.text)
        
        # Extrai valores monetários
        padrao_valor = r'R\$\s*\d+(?:[.,]\d+)*'
        metadados['valores_monetarios'] = re.findall(padrao_valor, doc.text)
        
        # Extrai números de processos
        padrao_processo = r'\b\d{5,7}[-.]?\d{3,}[/.]?\d{4}[-.]?\d{1,2}\b'
        metadados['numeros_processos'] = re.findall(padrao_processo, doc.text)
        
        # Extrai CNPJ
        padrao_cnpj = r'\b\d{2}\.?\d{3}\.?\d{3}/\d{4}-\d{2}\b'
        metadados['cnpj'] = re.findall(padrao_cnpj, doc.text)
        
        # Extrai CPF
        padrao_cpf = r'\b\d{3}\.?\d{3}\.?\d{3}-\d{2}\b'
        metadados['cpf'] = re.findall(padrao_cpf, doc.text)
        
        return metadados
    
    def classificar_documento(self, doc):
        """
        Classifica o tipo de documento com base em seu conteúdo.
        
        Args:
            doc (spacy.tokens.Doc): Documento processado pelo spaCy
            
        Returns:
            str: Tipo de documento identificado
        """
        texto_lower = doc.text.lower()
        
        # Palavras-chave para cada tipo de documento
        keywords = {
            'licitacao': ['licitação', 'pregão', 'concorrência', 'tomada de preço', 'licitatório'],
            'contrato': ['contrato', 'termo aditivo', 'contratante', 'contratado'],
            'extrato': ['extrato', 'resumo'],
            'aviso': ['aviso', 'comunicado', 'informa'],
            'edital': ['edital', 'seleção', 'processo seletivo'],
            'portaria': ['portaria', 'nomear', 'designar', 'exonerar'],
            'decreto': ['decreto', 'decreta'],
            'resolucao': ['resolução', 'resolve'],
            'despacho': ['despacho', 'decide']
        }
        
        # Conta ocorrências de palavras-chave para cada tipo
        scores = {tipo: 0 for tipo in self.TIPOS_DOCUMENTO}
        
        for tipo, palavras in keywords.items():
            for palavra in palavras:
                if palavra in texto_lower:
                    scores[tipo] += texto_lower.count(palavra)
        
        # Identifica o tipo com maior pontuação
        tipo_max = max(scores.items(), key=lambda x: x[1])
        
        # Se nenhum tipo teve pontuação, classifica como 'outros'
        if tipo_max[1] == 0:
            return 'outros'
        
        return tipo_max[0]
