"""
Módulo principal do Agente Coletor (DOU-Collector).

Este módulo contém o ponto de entrada para o Agente Coletor, responsável por
acessar o site oficial do DOU e extrair o conteúdo bruto das publicações.
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coletor.extrator import DOUExtrator
from utils.config import Config
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('coletor')

def parse_arguments():
    """Parse os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Agente Coletor para o DOU')
    parser.add_argument('--data', type=str, help='Data alvo no formato DD-MM-AAAA')
    parser.add_argument('--secao', type=int, choices=[1, 2, 3, 'e'], 
                        help='Seção do DOU (1, 2, 3 ou "e" para extra)')
    parser.add_argument('--output', type=str, help='Diretório de saída para os dados coletados')
    parser.add_argument('--modo', choices=['completo', 'incremental'], default='completo',
                        help='Modo de coleta: completo ou incremental')
    parser.add_argument('--max-paginas', type=int, help='Número máximo de páginas a coletar')
    parser.add_argument('--config', type=str, help='Caminho para arquivo de configuração')
    
    return parser.parse_args()

def validar_data(data_str):
    """Valida o formato da data."""
    try:
        return datetime.strptime(data_str, '%d-%m-%Y')
    except ValueError:
        logger.error(f"Formato de data inválido: {data_str}. Use o formato DD-MM-AAAA.")
        sys.exit(1)

def main():
    """Função principal do Agente Coletor."""
    args = parse_arguments()
    
    # Carrega configurações
    config = Config(args.config)
    
    # Valida e processa argumentos
    if args.data:
        data = validar_data(args.data)
    else:
        data = datetime.now()
        logger.info(f"Nenhuma data especificada. Usando data atual: {data.strftime('%d-%m-%Y')}")
    
    secao = args.secao if args.secao else 3
    logger.info(f"Iniciando coleta para a data {data.strftime('%d-%m-%Y')}, Seção {secao}")
    
    # Define diretório de saída
    output_dir = args.output or os.path.join(config.get('dados_dir', '../dados'), 'brutos')
    os.makedirs(output_dir, exist_ok=True)
    
    # Cria e executa o extrator
    extrator = DOUExtrator(
        data=data,
        secao=secao,
        modo=args.modo,
        max_paginas=args.max_paginas,
        config=config
    )
    
    try:
        # Inicia o processo de extração
        resultado = extrator.extrair()
        
        # Salva os resultados
        output_file = os.path.join(
            output_dir, 
            f"{data.strftime('%Y-%m-%d')}_secao{secao}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Coleta concluída com sucesso. Dados salvos em {output_file}")
        logger.info(f"Total de páginas coletadas: {len(resultado['paginas'])}")
        
        # Notifica o Agente Coordenador sobre a conclusão
        if config.get('usar_mensageria', False):
            from utils.mensageria import publicar_mensagem
            publicar_mensagem(
                'coleta_concluida',
                {
                    'data': data.strftime('%Y-%m-%d'),
                    'secao': secao,
                    'arquivo': output_file,
                    'total_paginas': len(resultado['paginas']),
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        return 0
    
    except Exception as e:
        logger.error(f"Erro durante a coleta: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
