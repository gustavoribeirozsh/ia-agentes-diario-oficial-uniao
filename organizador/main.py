"""
Módulo principal do Agente Organizador (DOU-Organizer).

Este módulo contém o ponto de entrada para o Agente Organizador, responsável por
compilar os dados processados em formato CSV com as colunas: Data de Publicação,
Seção, Número da Página, Título e Resumo do Conteúdo.
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from organizador.csv_builder import CSVBuilder
from organizador.validador import ValidadorDados
from utils.config import Config
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('organizador')

def parse_arguments():
    """Parse os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Agente Organizador para o DOU')
    parser.add_argument('--input', type=str, required=True,
                        help='Caminho para o arquivo JSON com dados processados do DOU')
    parser.add_argument('--output', type=str,
                        help='Caminho para o arquivo CSV de saída')
    parser.add_argument('--formato', type=str, choices=['csv', 'excel', 'json'],
                        help='Formato do arquivo de saída')
    parser.add_argument('--separador', type=str, default=',',
                        help='Separador para o arquivo CSV')
    parser.add_argument('--encoding', type=str, default='utf-8',
                        help='Encoding para o arquivo CSV')
    parser.add_argument('--config', type=str,
                        help='Caminho para arquivo de configuração')
    
    return parser.parse_args()

def main():
    """Função principal do Agente Organizador."""
    args = parse_arguments()
    
    # Carrega configurações
    config = Config(args.config)
    
    # Verifica se o arquivo de entrada existe
    if not os.path.exists(args.input):
        logger.error(f"Arquivo de entrada não encontrado: {args.input}")
        return 1
    
    # Define arquivo de saída
    if args.output:
        output_file = args.output
    else:
        input_basename = os.path.basename(args.input)
        nome_base = os.path.splitext(input_basename)[0]
        formato = args.formato or config.get('formato_saida', 'csv')
        output_dir = os.path.join(config.get('dados_dir', '../dados'), formato)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{nome_base}.{formato}")
    
    # Carrega os dados processados
    logger.info(f"Carregando dados processados de {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            dados_processados = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo de entrada: {str(e)}")
        return 1
    
    # Valida os dados
    logger.info("Validando dados processados")
    validador = ValidadorDados()
    if not validador.validar(dados_processados):
        logger.error("Validação de dados falhou")
        logger.error(f"Erros encontrados: {validador.erros}")
        return 1
    
    # Inicializa o construtor de CSV
    csv_builder = CSVBuilder(
        separador=args.separador or config.get('separador_csv', ','),
        encoding=args.encoding or config.get('encoding_csv', 'utf-8')
    )
    
    # Organiza os dados em formato CSV
    logger.info("Organizando dados em formato estruturado")
    try:
        # Extrai dados das páginas regulares
        registros = []
        
        for pagina in dados_processados.get('paginas', []):
            data_publicacao = dados_processados.get('data', '')
            secao = dados_processados.get('secao', '')
            numero_pagina = pagina.get('numero_pagina', '')
            
            for publicacao in pagina.get('publicacoes', []):
                registro = {
                    'data_publicacao': data_publicacao,
                    'secao': secao,
                    'numero_pagina': numero_pagina,
                    'titulo': publicacao.get('titulo', ''),
                    'resumo': publicacao.get('resumo', ''),
                    'entidades': ', '.join([e.get('texto', '') for e in publicacao.get('entidades', [])]),
                    'palavras_chave': ', '.join([p.get('palavra', '') for p in publicacao.get('palavras_chave', [])]),
                    'tipo_documento': publicacao.get('tipo_documento', ''),
                    'id': publicacao.get('id', '')
                }
                
                # Adiciona metadados extraídos
                metadados = publicacao.get('metadados_extraidos', {})
                if metadados:
                    registro['datas_mencionadas'] = ', '.join(metadados.get('datas', []))
                    registro['valores_monetarios'] = ', '.join(metadados.get('valores_monetarios', []))
                    registro['numeros_processos'] = ', '.join(metadados.get('numeros_processos', []))
                    registro['cnpj'] = ', '.join(metadados.get('cnpj', []))
                    registro['cpf'] = ', '.join(metadados.get('cpf', []))
                
                registros.append(registro)
        
        # Extrai dados das seções extras, se existirem
        if 'secoes_extras' in dados_processados and dados_processados['secoes_extras']:
            for secao_extra in dados_processados['secoes_extras']:
                conteudo = secao_extra.get('conteudo', {})
                numero_pagina = conteudo.get('numero_pagina', '')
                
                for publicacao in conteudo.get('publicacoes', []):
                    registro = {
                        'data_publicacao': dados_processados.get('data', ''),
                        'secao': f"{dados_processados.get('secao', '')}E",  # Marca como seção extra
                        'numero_pagina': numero_pagina,
                        'titulo': publicacao.get('titulo', ''),
                        'resumo': publicacao.get('resumo', ''),
                        'entidades': ', '.join([e.get('texto', '') for e in publicacao.get('entidades', [])]),
                        'palavras_chave': ', '.join([p.get('palavra', '') for p in publicacao.get('palavras_chave', [])]),
                        'tipo_documento': publicacao.get('tipo_documento', ''),
                        'id': publicacao.get('id', ''),
                        'url_secao_extra': secao_extra.get('url', '')
                    }
                    
                    # Adiciona metadados extraídos
                    metadados = publicacao.get('metadados_extraidos', {})
                    if metadados:
                        registro['datas_mencionadas'] = ', '.join(metadados.get('datas', []))
                        registro['valores_monetarios'] = ', '.join(metadados.get('valores_monetarios', []))
                        registro['numeros_processos'] = ', '.join(metadados.get('numeros_processos', []))
                        registro['cnpj'] = ', '.join(metadados.get('cnpj', []))
                        registro['cpf'] = ', '.join(metadados.get('cpf', []))
                    
                    registros.append(registro)
        
        # Gera o arquivo de saída
        formato = args.formato or config.get('formato_saida', 'csv')
        
        if formato == 'csv':
            csv_builder.gerar_csv(registros, output_file)
        elif formato == 'excel':
            csv_builder.gerar_excel(registros, output_file)
        elif formato == 'json':
            csv_builder.gerar_json(registros, output_file)
        else:
            logger.warning(f"Formato '{formato}' não suportado. Gerando CSV como fallback.")
            csv_builder.gerar_csv(registros, output_file.replace(f".{formato}", ".csv"))
        
        logger.info(f"Arquivo {formato.upper()} gerado com sucesso: {output_file}")
        logger.info(f"Total de registros: {len(registros)}")
        
        # Notifica o Agente Coordenador sobre a conclusão
        if config.get('usar_mensageria', False):
            from utils.mensageria import publicar_mensagem
            publicar_mensagem(
                'organizacao_concluida',
                {
                    'data': dados_processados.get('data', ''),
                    'secao': dados_processados.get('secao', ''),
                    'arquivo_entrada': args.input,
                    'arquivo_saida': output_file,
                    'formato': formato,
                    'total_registros': len(registros),
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        logger.info("Organização concluída com sucesso")
        return 0
    
    except Exception as e:
        logger.error(f"Erro durante a organização dos dados: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
