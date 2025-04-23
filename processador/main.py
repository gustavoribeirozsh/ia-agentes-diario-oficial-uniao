"""
Módulo principal do Agente Processador (DOU-Processor).

Este módulo contém o ponto de entrada para o Agente Processador, responsável por
transformar o conteúdo bruto extraído pelo Agente Coletor em dados estruturados
usando técnicas de processamento de linguagem natural.
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processador.nlp import ProcessadorNLP
from processador.resumo import GeradorResumo
from utils.config import Config
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('processador')

def parse_arguments():
    """Parse os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Agente Processador para o DOU')
    parser.add_argument('--input', type=str, required=True,
                        help='Caminho para o arquivo JSON com dados brutos do DOU')
    parser.add_argument('--output', type=str,
                        help='Caminho para o arquivo de saída com dados processados')
    parser.add_argument('--modelo', type=str,
                        help='Modelo spaCy a ser utilizado (ex: pt_core_news_lg)')
    parser.add_argument('--tamanho-resumo', type=int,
                        help='Tamanho máximo dos resumos gerados')
    parser.add_argument('--config', type=str,
                        help='Caminho para arquivo de configuração')
    
    return parser.parse_args()

def main():
    """Função principal do Agente Processador."""
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
        output_dir = os.path.join(config.get('dados_dir', '../dados'), 'processados')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"processado_{input_basename}")
    
    # Carrega os dados brutos
    logger.info(f"Carregando dados brutos de {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            dados_brutos = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo de entrada: {str(e)}")
        return 1
    
    # Inicializa o processador NLP
    modelo = args.modelo or config.get('modelo_spacy', 'pt_core_news_lg')
    processador = ProcessadorNLP(modelo=modelo)
    
    # Inicializa o gerador de resumos
    tamanho_resumo = args.tamanho_resumo or config.get('tamanho_maximo_resumo', 200)
    gerador_resumo = GeradorResumo(tamanho_maximo=tamanho_resumo)
    
    # Processa os dados
    logger.info("Iniciando processamento dos dados")
    try:
        # Extrai metadados gerais
        dados_processados = {
            'data': dados_brutos.get('data'),
            'secao': dados_brutos.get('secao'),
            'total_paginas': dados_brutos.get('total_paginas'),
            'timestamp_processamento': datetime.now().isoformat(),
            'paginas': []
        }
        
        # Processa cada página
        total_paginas = len(dados_brutos.get('paginas', []))
        logger.info(f"Processando {total_paginas} páginas")
        
        for i, pagina_bruta in enumerate(dados_brutos.get('paginas', []), 1):
            logger.info(f"Processando página {i}/{total_paginas}")
            
            # Extrai metadados da página
            pagina_processada = {
                'numero_pagina': pagina_bruta.get('numero_pagina'),
                'metadados': pagina_bruta.get('metadados', {}),
                'publicacoes': []
            }
            
            # Processa cada publicação da página
            for publicacao_bruta in pagina_bruta.get('publicacoes', []):
                # Processa o texto da publicação
                texto = publicacao_bruta.get('corpo', '')
                doc = processador.processar_texto(texto)
                
                # Extrai entidades
                entidades = processador.extrair_entidades(doc)
                
                # Gera resumo
                resumo = gerador_resumo.gerar_resumo(texto)
                
                # Extrai palavras-chave
                palavras_chave = processador.extrair_palavras_chave(doc)
                
                # Classifica o tipo de documento
                tipo_documento = processador.classificar_documento(doc)
                
                # Monta a publicação processada
                publicacao_processada = {
                    'id': publicacao_bruta.get('id', ''),
                    'titulo': publicacao_bruta.get('titulo', ''),
                    'resumo': resumo,
                    'entidades': entidades,
                    'palavras_chave': palavras_chave,
                    'tipo_documento': tipo_documento,
                    'metadados_extraidos': processador.extrair_metadados_texto(doc)
                }
                
                pagina_processada['publicacoes'].append(publicacao_processada)
            
            dados_processados['paginas'].append(pagina_processada)
        
        # Processa seções extras, se existirem
        if 'secoes_extras' in dados_brutos and dados_brutos['secoes_extras']:
            dados_processados['secoes_extras'] = []
            
            for secao_extra in dados_brutos['secoes_extras']:
                secao_processada = {
                    'url': secao_extra.get('url', ''),
                    'conteudo': {}
                }
                
                conteudo_bruto = secao_extra.get('conteudo', {})
                conteudo_processado = {
                    'numero_pagina': conteudo_bruto.get('numero_pagina'),
                    'metadados': conteudo_bruto.get('metadados', {}),
                    'publicacoes': []
                }
                
                for publicacao_bruta in conteudo_bruto.get('publicacoes', []):
                    texto = publicacao_bruta.get('corpo', '')
                    doc = processador.processar_texto(texto)
                    
                    publicacao_processada = {
                        'id': publicacao_bruta.get('id', ''),
                        'titulo': publicacao_bruta.get('titulo', ''),
                        'resumo': gerador_resumo.gerar_resumo(texto),
                        'entidades': processador.extrair_entidades(doc),
                        'palavras_chave': processador.extrair_palavras_chave(doc),
                        'tipo_documento': processador.classificar_documento(doc),
                        'metadados_extraidos': processador.extrair_metadados_texto(doc)
                    }
                    
                    conteudo_processado['publicacoes'].append(publicacao_processada)
                
                secao_processada['conteudo'] = conteudo_processado
                dados_processados['secoes_extras'].append(secao_processada)
        
        # Salva os dados processados
        logger.info(f"Salvando dados processados em {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dados_processados, f, ensure_ascii=False, indent=2)
        
        # Notifica o Agente Coordenador sobre a conclusão
        if config.get('usar_mensageria', False):
            from utils.mensageria import publicar_mensagem
            publicar_mensagem(
                'processamento_concluido',
                {
                    'data': dados_brutos.get('data'),
                    'secao': dados_brutos.get('secao'),
                    'arquivo_entrada': args.input,
                    'arquivo_saida': output_file,
                    'total_paginas': total_paginas,
                    'total_publicacoes': sum(len(p.get('publicacoes', [])) for p in dados_processados['paginas']),
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        logger.info("Processamento concluído com sucesso")
        return 0
    
    except Exception as e:
        logger.error(f"Erro durante o processamento: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
