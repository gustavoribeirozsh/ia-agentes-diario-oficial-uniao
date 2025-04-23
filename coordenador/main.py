"""
Módulo principal do Agente Coordenador (DOU-Coordinator).

Este módulo contém o ponto de entrada para o Agente Coordenador, responsável por
gerenciar o fluxo de trabalho entre todos os outros agentes e servir como ponto
de interação principal.
"""

import argparse
import json
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coordenador.orquestrador import Orquestrador
from coordenador.monitor import Monitor
from utils.config import Config
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('coordenador')

def parse_arguments():
    """Parse os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Agente Coordenador para o DOU')
    parser.add_argument('--data', type=str,
                        help='Data alvo no formato DD-MM-AAAA')
    parser.add_argument('--secao', type=int, choices=[1, 2, 3],
                        help='Seção do DOU (1, 2, 3)')
    parser.add_argument('--modo', choices=['completo', 'coleta', 'processamento', 'organizacao', 'busca', 'monitor'],
                        default='completo',
                        help='Modo de operação do coordenador')
    parser.add_argument('--monitor', action='store_true',
                        help='Ativar modo de monitoramento')
    parser.add_argument('--intervalo', type=int, default=60,
                        help='Intervalo de monitoramento em segundos')
    parser.add_argument('--output-dir', type=str,
                        help='Diretório de saída para os arquivos gerados')
    parser.add_argument('--config', type=str,
                        help='Caminho para arquivo de configuração')
    
    return parser.parse_args()

def main():
    """Função principal do Agente Coordenador."""
    args = parse_arguments()
    
    # Carrega configurações
    config = Config(args.config)
    
    # Define diretório de saída
    output_dir = args.output_dir or config.get('dados_dir', '../dados')
    os.makedirs(output_dir, exist_ok=True)
    
    # Modo de monitoramento
    if args.monitor or args.modo == 'monitor':
        logger.info("Iniciando Agente Coordenador em modo de monitoramento")
        
        intervalo = args.intervalo or config.get('intervalo_monitoramento', 60)
        monitor = Monitor(config)
        
        try:
            monitor.iniciar(intervalo)
        except KeyboardInterrupt:
            logger.info("Monitoramento interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro durante o monitoramento: {str(e)}")
        
        return 0
    
    # Inicializa o orquestrador
    orquestrador = Orquestrador(config)
    
    # Verifica e processa a data
    if args.data:
        try:
            data = datetime.strptime(args.data, '%d-%m-%Y')
        except ValueError:
            logger.error(f"Formato de data inválido: {args.data}. Use o formato DD-MM-AAAA.")
            return 1
    else:
        # Se não for especificada, usa o dia anterior
        data = datetime.now() - timedelta(days=1)
        logger.info(f"Nenhuma data especificada. Usando data anterior: {data.strftime('%d-%m-%Y')}")
    
    # Verifica e processa a seção
    secao = args.secao if args.secao else 3
    logger.info(f"Iniciando processamento para a data {data.strftime('%d-%m-%Y')}, Seção {secao}")
    
    # Define o modo de operação
    modo = args.modo
    
    try:
        if modo == 'completo':
            # Executa o fluxo completo
            logger.info("Iniciando fluxo de trabalho completo")
            
            # Etapa 1: Coleta
            logger.info("Etapa 1: Coleta de dados do DOU")
            arquivo_bruto = orquestrador.executar_coleta(data, secao, output_dir)
            
            # Etapa 2: Processamento
            logger.info("Etapa 2: Processamento dos dados coletados")
            arquivo_processado = orquestrador.executar_processamento(arquivo_bruto, output_dir)
            
            # Etapa 3: Organização
            logger.info("Etapa 3: Organização dos dados processados")
            arquivo_organizado = orquestrador.executar_organizacao(arquivo_processado, output_dir)
            
            # Etapa 4: Indexação para busca
            logger.info("Etapa 4: Indexação dos dados para busca")
            resultado_indexacao = orquestrador.executar_indexacao(arquivo_organizado)
            
            logger.info("Fluxo de trabalho completo executado com sucesso")
            
            # Gera relatório final
            relatorio = {
                'data': data.strftime('%Y-%m-%d'),
                'secao': secao,
                'timestamp': datetime.now().isoformat(),
                'etapas': {
                    'coleta': {
                        'arquivo': arquivo_bruto,
                        'status': 'concluido'
                    },
                    'processamento': {
                        'arquivo': arquivo_processado,
                        'status': 'concluido'
                    },
                    'organizacao': {
                        'arquivo': arquivo_organizado,
                        'status': 'concluido'
                    },
                    'indexacao': {
                        'resultado': resultado_indexacao,
                        'status': 'concluido' if resultado_indexacao.get('success', False) else 'falha'
                    }
                }
            }
            
            # Salva o relatório
            relatorio_file = os.path.join(output_dir, f"relatorio_{data.strftime('%Y-%m-%d')}_secao{secao}.json")
            with open(relatorio_file, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Relatório final salvo em {relatorio_file}")
        
        elif modo == 'coleta':
            # Executa apenas a etapa de coleta
            logger.info("Executando apenas a etapa de coleta")
            arquivo_bruto = orquestrador.executar_coleta(data, secao, output_dir)
            logger.info(f"Coleta concluída. Arquivo gerado: {arquivo_bruto}")
        
        elif modo == 'processamento':
            # Executa apenas a etapa de processamento
            logger.info("Executando apenas a etapa de processamento")
            
            # Busca o arquivo mais recente para a data e seção especificadas
            arquivo_bruto = orquestrador.encontrar_arquivo_mais_recente(
                os.path.join(output_dir, 'brutos'),
                f"{data.strftime('%Y-%m-%d')}_secao{secao}"
            )
            
            if not arquivo_bruto:
                logger.error(f"Nenhum arquivo bruto encontrado para {data.strftime('%Y-%m-%d')}, Seção {secao}")
                return 1
            
            arquivo_processado = orquestrador.executar_processamento(arquivo_bruto, output_dir)
            logger.info(f"Processamento concluído. Arquivo gerado: {arquivo_processado}")
        
        elif modo == 'organizacao':
            # Executa apenas a etapa de organização
            logger.info("Executando apenas a etapa de organização")
            
            # Busca o arquivo mais recente para a data e seção especificadas
            arquivo_processado = orquestrador.encontrar_arquivo_mais_recente(
                os.path.join(output_dir, 'processados'),
                f"processado_{data.strftime('%Y-%m-%d')}_secao{secao}"
            )
            
            if not arquivo_processado:
                logger.error(f"Nenhum arquivo processado encontrado para {data.strftime('%Y-%m-%d')}, Seção {secao}")
                return 1
            
            arquivo_organizado = orquestrador.executar_organizacao(arquivo_processado, output_dir)
            logger.info(f"Organização concluída. Arquivo gerado: {arquivo_organizado}")
        
        elif modo == 'busca':
            # Executa apenas a etapa de indexação para busca
            logger.info("Executando apenas a etapa de indexação para busca")
            
            # Busca o arquivo mais recente para a data e seção especificadas
            arquivo_organizado = orquestrador.encontrar_arquivo_mais_recente(
                os.path.join(output_dir, 'csv'),
                f"processado_{data.strftime('%Y-%m-%d')}_secao{secao}"
            )
            
            if not arquivo_organizado:
                logger.error(f"Nenhum arquivo organizado encontrado para {data.strftime('%Y-%m-%d')}, Seção {secao}")
                return 1
            
            resultado_indexacao = orquestrador.executar_indexacao(arquivo_organizado)
            logger.info(f"Indexação concluída: {resultado_indexacao}")
        
        logger.info("Operação concluída com sucesso")
        return 0
    
    except Exception as e:
        logger.error(f"Erro durante a execução: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
