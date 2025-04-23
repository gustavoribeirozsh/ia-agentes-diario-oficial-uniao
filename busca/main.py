"""
Módulo principal do Agente de Busca (DOU-Searcher).

Este módulo contém o ponto de entrada para o Agente de Busca, responsável por
permitir a recuperação eficiente de informações específicas dentro dos dados
organizados do DOU.
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from busca.indexador import Indexador
from busca.consulta import ProcessadorConsulta
from utils.config import Config
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('busca')

def parse_arguments():
    """Parse os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Agente de Busca para o DOU')
    parser.add_argument('--input', type=str,
                        help='Caminho para o arquivo CSV ou diretório com dados organizados')
    parser.add_argument('--index', type=str,
                        help='Nome do índice Elasticsearch')
    parser.add_argument('--query', type=str,
                        help='Consulta de busca')
    parser.add_argument('--output', type=str,
                        help='Caminho para o arquivo de saída com resultados da busca')
    parser.add_argument('--formato', type=str, choices=['csv', 'json', 'txt'], default='json',
                        help='Formato do arquivo de saída')
    parser.add_argument('--data-inicio', type=str,
                        help='Data de início para filtro (formato YYYY-MM-DD)')
    parser.add_argument('--data-fim', type=str,
                        help='Data de fim para filtro (formato YYYY-MM-DD)')
    parser.add_argument('--secao', type=str,
                        help='Seção do DOU para filtro')
    parser.add_argument('--tipo-documento', type=str,
                        help='Tipo de documento para filtro')
    parser.add_argument('--max-resultados', type=int, default=100,
                        help='Número máximo de resultados')
    parser.add_argument('--modo', choices=['indexar', 'buscar', 'ambos'], default='buscar',
                        help='Modo de operação: indexar, buscar ou ambos')
    parser.add_argument('--config', type=str,
                        help='Caminho para arquivo de configuração')
    
    return parser.parse_args()

def main():
    """Função principal do Agente de Busca."""
    args = parse_arguments()
    
    # Carrega configurações
    config = Config(args.config)
    
    # Define nome do índice
    index_name = args.index or config.get('elasticsearch_index', 'dou')
    
    # Inicializa o indexador
    indexador = Indexador(
        host=config.get('elasticsearch_host', 'localhost'),
        port=config.get('elasticsearch_port', 9200)
    )
    
    # Inicializa o processador de consulta
    processador_consulta = ProcessadorConsulta(
        host=config.get('elasticsearch_host', 'localhost'),
        port=config.get('elasticsearch_port', 9200)
    )
    
    # Modo de operação: indexar
    if args.modo in ['indexar', 'ambos']:
        if not args.input:
            logger.error("Parâmetro --input é obrigatório para o modo de indexação")
            return 1
        
        # Verifica se o input é um arquivo ou diretório
        if os.path.isfile(args.input):
            # Indexa um único arquivo
            logger.info(f"Indexando arquivo: {args.input}")
            resultado_indexacao = indexador.indexar_arquivo(args.input, index_name)
            logger.info(f"Indexação concluída: {resultado_indexacao['total']} documentos indexados")
        
        elif os.path.isdir(args.input):
            # Indexa todos os arquivos CSV/JSON no diretório
            logger.info(f"Indexando diretório: {args.input}")
            resultado_indexacao = indexador.indexar_diretorio(args.input, index_name)
            logger.info(f"Indexação concluída: {resultado_indexacao['total']} documentos indexados")
        
        else:
            logger.error(f"Caminho de entrada não encontrado: {args.input}")
            return 1
    
    # Modo de operação: buscar
    if args.modo in ['buscar', 'ambos']:
        if not args.query and not args.data_inicio and not args.secao and not args.tipo_documento:
            logger.error("Parâmetro --query ou algum filtro é obrigatório para o modo de busca")
            return 1
        
        # Prepara os filtros
        filtros = {}
        if args.data_inicio:
            filtros['data_inicio'] = args.data_inicio
        if args.data_fim:
            filtros['data_fim'] = args.data_fim
        if args.secao:
            filtros['secao'] = args.secao
        if args.tipo_documento:
            filtros['tipo_documento'] = args.tipo_documento
        
        # Executa a busca
        logger.info(f"Executando busca: {args.query}")
        resultados = processador_consulta.buscar(
            index_name,
            query=args.query,
            filtros=filtros,
            max_resultados=args.max_resultados
        )
        
        logger.info(f"Busca concluída: {len(resultados['hits'])} resultados encontrados")
        
        # Salva os resultados, se solicitado
        if args.output:
            formato = args.formato.lower()
            
            # Garante que o diretório de saída existe
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            
            if formato == 'json':
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(resultados, f, ensure_ascii=False, indent=2)
            
            elif formato == 'csv':
                import csv
                with open(args.output, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    # Escreve o cabeçalho
                    writer.writerow(['score', 'id', 'data_publicacao', 'secao', 'numero_pagina', 'titulo', 'resumo', 'tipo_documento'])
                    # Escreve os resultados
                    for hit in resultados['hits']:
                        source = hit['_source']
                        writer.writerow([
                            hit['_score'],
                            hit['_id'],
                            source.get('data_publicacao', ''),
                            source.get('secao', ''),
                            source.get('numero_pagina', ''),
                            source.get('titulo', ''),
                            source.get('resumo', ''),
                            source.get('tipo_documento', '')
                        ])
            
            elif formato == 'txt':
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(f"Consulta: {args.query}\n")
                    f.write(f"Total de resultados: {resultados['total']}\n")
                    f.write(f"Tempo de busca: {resultados['took']}ms\n\n")
                    
                    for i, hit in enumerate(resultados['hits'], 1):
                        source = hit['_source']
                        f.write(f"Resultado {i} (Score: {hit['_score']})\n")
                        f.write(f"ID: {hit['_id']}\n")
                        f.write(f"Data: {source.get('data_publicacao', '')}\n")
                        f.write(f"Seção: {source.get('secao', '')}\n")
                        f.write(f"Página: {source.get('numero_pagina', '')}\n")
                        f.write(f"Tipo: {source.get('tipo_documento', '')}\n")
                        f.write(f"Título: {source.get('titulo', '')}\n")
                        f.write(f"Resumo: {source.get('resumo', '')}\n")
                        f.write("-" * 80 + "\n\n")
            
            logger.info(f"Resultados salvos em {args.output}")
        
        # Notifica o Agente Coordenador sobre a conclusão
        if config.get('usar_mensageria', False):
            from utils.mensageria import publicar_mensagem
            publicar_mensagem(
                'busca_concluida',
                {
                    'query': args.query,
                    'filtros': filtros,
                    'total_resultados': resultados['total'],
                    'arquivo_saida': args.output if args.output else None,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    logger.info("Operação concluída com sucesso")
    return 0

if __name__ == "__main__":
    sys.exit(main())
