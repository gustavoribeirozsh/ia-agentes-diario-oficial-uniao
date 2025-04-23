"""
Módulo de validação de dados para o Agente Organizador.

Este módulo implementa a classe ValidadorDados, responsável por
validar os dados processados antes da geração de arquivos CSV.
"""

import json
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('organizador.validador')

class ValidadorDados:
    """
    Classe para validação dos dados processados.
    
    Esta classe implementa métodos para verificar a integridade e
    consistência dos dados antes da geração de arquivos CSV.
    """
    
    def __init__(self):
        """Inicializa o validador de dados."""
        self.erros = []
    
    def validar(self, dados):
        """
        Valida os dados processados.
        
        Args:
            dados (dict): Dados processados a serem validados
            
        Returns:
            bool: True se os dados são válidos, False caso contrário
        """
        self.erros = []
        
        # Verifica campos obrigatórios
        if not self._validar_campos_obrigatorios(dados):
            return False
        
        # Verifica estrutura das páginas
        if not self._validar_estrutura_paginas(dados):
            return False
        
        # Verifica consistência dos dados
        if not self._validar_consistencia(dados):
            return False
        
        # Se chegou até aqui, os dados são válidos
        return len(self.erros) == 0
    
    def _validar_campos_obrigatorios(self, dados):
        """
        Verifica se os campos obrigatórios estão presentes.
        
        Args:
            dados (dict): Dados processados
            
        Returns:
            bool: True se todos os campos obrigatórios estão presentes
        """
        # Verifica campos de nível superior
        campos_obrigatorios = ['data', 'secao', 'paginas']
        for campo in campos_obrigatorios:
            if campo not in dados:
                self.erros.append(f"Campo obrigatório '{campo}' não encontrado")
                return False
        
        # Verifica se há páginas
        if not dados['paginas']:
            self.erros.append("Nenhuma página encontrada nos dados")
            return False
        
        return True
    
    def _validar_estrutura_paginas(self, dados):
        """
        Verifica se a estrutura das páginas está correta.
        
        Args:
            dados (dict): Dados processados
            
        Returns:
            bool: True se a estrutura das páginas está correta
        """
        for i, pagina in enumerate(dados['paginas']):
            # Verifica campos obrigatórios da página
            if 'numero_pagina' not in pagina:
                self.erros.append(f"Campo 'numero_pagina' não encontrado na página {i+1}")
            
            if 'publicacoes' not in pagina:
                self.erros.append(f"Campo 'publicacoes' não encontrado na página {i+1}")
                continue
            
            # Verifica estrutura das publicações
            for j, publicacao in enumerate(pagina['publicacoes']):
                # Verifica campos obrigatórios da publicação
                campos_publicacao = ['titulo', 'resumo']
                for campo in campos_publicacao:
                    if campo not in publicacao:
                        self.erros.append(f"Campo '{campo}' não encontrado na publicação {j+1} da página {i+1}")
        
        # Verifica seções extras, se existirem
        if 'secoes_extras' in dados and dados['secoes_extras']:
            for i, secao in enumerate(dados['secoes_extras']):
                if 'url' not in secao:
                    self.erros.append(f"Campo 'url' não encontrado na seção extra {i+1}")
                
                if 'conteudo' not in secao:
                    self.erros.append(f"Campo 'conteudo' não encontrado na seção extra {i+1}")
                    continue
                
                conteudo = secao['conteudo']
                if 'publicacoes' not in conteudo:
                    self.erros.append(f"Campo 'publicacoes' não encontrado no conteúdo da seção extra {i+1}")
        
        return len(self.erros) == 0
    
    def _validar_consistencia(self, dados):
        """
        Verifica a consistência dos dados.
        
        Args:
            dados (dict): Dados processados
            
        Returns:
            bool: True se os dados são consistentes
        """
        # Verifica se a data está em formato válido
        if not self._validar_formato_data(dados['data']):
            self.erros.append(f"Formato de data inválido: {dados['data']}")
        
        # Verifica se a seção é válida
        if not self._validar_secao(dados['secao']):
            self.erros.append(f"Seção inválida: {dados['secao']}")
        
        # Verifica se os números de página são consistentes
        numeros_pagina = set()
        for pagina in dados['paginas']:
            if 'numero_pagina' in pagina:
                numero = pagina['numero_pagina']
                if numero in numeros_pagina:
                    self.erros.append(f"Número de página duplicado: {numero}")
                numeros_pagina.add(numero)
        
        return len(self.erros) == 0
    
    def _validar_formato_data(self, data):
        """
        Verifica se a data está em formato válido (YYYY-MM-DD).
        
        Args:
            data (str): Data a ser validada
            
        Returns:
            bool: True se o formato da data é válido
        """
        import re
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', data))
    
    def _validar_secao(self, secao):
        """
        Verifica se a seção é válida (1, 2, 3 ou 'e').
        
        Args:
            secao: Seção a ser validada
            
        Returns:
            bool: True se a seção é válida
        """
        return secao in [1, 2, 3, 'e', '1', '2', '3']
    
    def gerar_relatorio(self):
        """
        Gera um relatório de validação.
        
        Returns:
            dict: Relatório de validação
        """
        return {
            'valido': len(self.erros) == 0,
            'total_erros': len(self.erros),
            'erros': self.erros
        }
    
    def salvar_relatorio(self, arquivo):
        """
        Salva o relatório de validação em um arquivo JSON.
        
        Args:
            arquivo (str): Caminho para o arquivo de saída
            
        Returns:
            bool: True se o salvamento foi bem-sucedido
        """
        try:
            relatorio = self.gerar_relatorio()
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Relatório de validação salvo em {arquivo}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao salvar relatório de validação: {str(e)}")
            return False
