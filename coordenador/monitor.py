"""
Módulo de monitoramento para o Agente Coordenador.

Este módulo implementa a classe Monitor, responsável por
monitorar o status dos agentes e o progresso das tarefas.
"""

import os
import time
import json
import threading
from datetime import datetime, timedelta

from utils.logger import setup_logger
from utils.mensageria import consumir_mensagem_unica
from coordenador.orquestrador import Orquestrador

# Configuração do logger
logger = setup_logger('coordenador.monitor')

class Monitor:
    """
    Classe para monitoramento dos agentes do DOU.
    
    Esta classe implementa métodos para monitorar o status dos agentes
    e o progresso das tarefas em execução.
    """
    
    def __init__(self, config):
        """
        Inicializa o monitor.
        
        Args:
            config (Config): Objeto de configuração
        """
        self.config = config
        self.orquestrador = Orquestrador(config)
        self.executando = False
        self.thread_monitor = None
        
        # Diretório para armazenar logs de status
        self.status_dir = os.path.join(
            self.config.get('dados_dir', '../dados'),
            'status'
        )
        os.makedirs(self.status_dir, exist_ok=True)
    
    def iniciar(self, intervalo=60):
        """
        Inicia o monitoramento em um thread separado.
        
        Args:
            intervalo (int): Intervalo de monitoramento em segundos
        """
        if self.executando:
            logger.warning("Monitoramento já está em execução")
            return
        
        self.executando = True
        self.thread_monitor = threading.Thread(
            target=self._loop_monitoramento,
            args=(intervalo,)
        )
        self.thread_monitor.daemon = True
        self.thread_monitor.start()
        
        logger.info(f"Monitoramento iniciado com intervalo de {intervalo} segundos")
        
        # Bloqueia o thread principal
        try:
            while self.executando:
                time.sleep(1)
        except KeyboardInterrupt:
            self.parar()
    
    def parar(self):
        """Para o monitoramento."""
        if not self.executando:
            logger.warning("Monitoramento não está em execução")
            return
        
        self.executando = False
        if self.thread_monitor:
            self.thread_monitor.join(timeout=5)
        
        logger.info("Monitoramento parado")
    
    def _loop_monitoramento(self, intervalo):
        """
        Loop principal de monitoramento.
        
        Args:
            intervalo (int): Intervalo de monitoramento em segundos
        """
        while self.executando:
            try:
                # Verifica o status dos agentes
                status_agentes = self.orquestrador.verificar_status_agentes()
                logger.info(f"Status dos agentes: {status_agentes}")
                
                # Verifica mensagens de conclusão de tarefas
                self._verificar_mensagens()
                
                # Verifica arquivos gerados recentemente
                self._verificar_arquivos_recentes()
                
                # Salva o status atual
                self._salvar_status(status_agentes)
                
                # Aguarda o próximo ciclo
                for _ in range(intervalo):
                    if not self.executando:
                        break
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"Erro durante o monitoramento: {str(e)}")
                time.sleep(10)  # Espera um pouco antes de tentar novamente
    
    def _verificar_mensagens(self):
        """Verifica mensagens de conclusão de tarefas."""
        if not self.config.get('usar_mensageria', False):
            return
        
        try:
            # Verifica mensagens de coleta concluída
            mensagem = consumir_mensagem_unica(
                'coleta_concluida',
                timeout=1,
                host=self.config.get('rabbitmq_host', 'localhost'),
                porta=self.config.get('rabbitmq_port', 5672)
            )
            
            if mensagem:
                logger.info(f"Mensagem de coleta concluída recebida: {mensagem}")
                # Aqui poderia iniciar automaticamente o processamento
            
            # Verifica mensagens de processamento concluído
            mensagem = consumir_mensagem_unica(
                'processamento_concluido',
                timeout=1,
                host=self.config.get('rabbitmq_host', 'localhost'),
                porta=self.config.get('rabbitmq_port', 5672)
            )
            
            if mensagem:
                logger.info(f"Mensagem de processamento concluído recebida: {mensagem}")
                # Aqui poderia iniciar automaticamente a organização
            
            # Verifica mensagens de organização concluída
            mensagem = consumir_mensagem_unica(
                'organizacao_concluida',
                timeout=1,
                host=self.config.get('rabbitmq_host', 'localhost'),
                porta=self.config.get('rabbitmq_port', 5672)
            )
            
            if mensagem:
                logger.info(f"Mensagem de organização concluída recebida: {mensagem}")
                # Aqui poderia iniciar automaticamente a indexação
        
        except Exception as e:
            logger.error(f"Erro ao verificar mensagens: {str(e)}")
    
    def _verificar_arquivos_recentes(self):
        """Verifica arquivos gerados recentemente."""
        try:
            dados_dir = self.config.get('dados_dir', '../dados')
            
            # Verifica arquivos brutos recentes
            brutos_dir = os.path.join(dados_dir, 'brutos')
            if os.path.exists(brutos_dir):
                arquivos_brutos = self._listar_arquivos_recentes(brutos_dir)
                if arquivos_brutos:
                    logger.info(f"Arquivos brutos recentes: {len(arquivos_brutos)}")
            
            # Verifica arquivos processados recentes
            processados_dir = os.path.join(dados_dir, 'processados')
            if os.path.exists(processados_dir):
                arquivos_processados = self._listar_arquivos_recentes(processados_dir)
                if arquivos_processados:
                    logger.info(f"Arquivos processados recentes: {len(arquivos_processados)}")
            
            # Verifica arquivos CSV recentes
            csv_dir = os.path.join(dados_dir, 'csv')
            if os.path.exists(csv_dir):
                arquivos_csv = self._listar_arquivos_recentes(csv_dir)
                if arquivos_csv:
                    logger.info(f"Arquivos CSV recentes: {len(arquivos_csv)}")
        
        except Exception as e:
            logger.error(f"Erro ao verificar arquivos recentes: {str(e)}")
    
    def _listar_arquivos_recentes(self, diretorio, horas=24):
        """
        Lista arquivos criados ou modificados nas últimas horas.
        
        Args:
            diretorio (str): Diretório a ser verificado
            horas (int): Número de horas para considerar um arquivo como recente
            
        Returns:
            list: Lista de arquivos recentes
        """
        arquivos_recentes = []
        limite_tempo = time.time() - (horas * 3600)
        
        for arquivo in os.listdir(diretorio):
            caminho = os.path.join(diretorio, arquivo)
            if os.path.isfile(caminho):
                mtime = os.path.getmtime(caminho)
                if mtime > limite_tempo:
                    arquivos_recentes.append({
                        'caminho': caminho,
                        'tamanho': os.path.getsize(caminho),
                        'modificado': datetime.fromtimestamp(mtime).isoformat()
                    })
        
        return arquivos_recentes
    
    def _salvar_status(self, status_agentes):
        """
        Salva o status atual em um arquivo JSON.
        
        Args:
            status_agentes (dict): Status dos agentes
        """
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'agentes': status_agentes,
                'sistema': {
                    'memoria_disponivel': self._obter_memoria_disponivel(),
                    'espaco_disco': self._obter_espaco_disco()
                }
            }
            
            # Define o arquivo de status
            arquivo_status = os.path.join(
                self.status_dir,
                f"status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Salva o status
            with open(arquivo_status, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
            
            # Mantém apenas os 10 arquivos de status mais recentes
            self._limpar_arquivos_antigos(self.status_dir, 10)
        
        except Exception as e:
            logger.error(f"Erro ao salvar status: {str(e)}")
    
    def _obter_memoria_disponivel(self):
        """
        Obtém a quantidade de memória disponível.
        
        Returns:
            str: Quantidade de memória disponível formatada
        """
        try:
            import psutil
            memoria = psutil.virtual_memory()
            return f"{memoria.available / (1024 * 1024):.2f} MB"
        except:
            return "desconhecido"
    
    def _obter_espaco_disco(self):
        """
        Obtém o espaço em disco disponível.
        
        Returns:
            str: Espaço em disco disponível formatado
        """
        try:
            import psutil
            disco = psutil.disk_usage('/')
            return f"{disco.free / (1024 * 1024 * 1024):.2f} GB"
        except:
            return "desconhecido"
    
    def _limpar_arquivos_antigos(self, diretorio, max_arquivos):
        """
        Remove arquivos antigos, mantendo apenas os mais recentes.
        
        Args:
            diretorio (str): Diretório a ser limpo
            max_arquivos (int): Número máximo de arquivos a manter
        """
        try:
            arquivos = [os.path.join(diretorio, f) for f in os.listdir(diretorio) if os.path.isfile(os.path.join(diretorio, f))]
            if len(arquivos) <= max_arquivos:
                return
            
            # Ordena por data de modificação (mais antigos primeiro)
            arquivos.sort(key=os.path.getmtime)
            
            # Remove os arquivos excedentes
            for arquivo in arquivos[:-max_arquivos]:
                try:
                    os.remove(arquivo)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Erro ao limpar arquivos antigos: {str(e)}")
    
    def gerar_relatorio(self, periodo_dias=7):
        """
        Gera um relatório de atividades para o período especificado.
        
        Args:
            periodo_dias (int): Período em dias para o relatório
            
        Returns:
            dict: Relatório de atividades
        """
        try:
            dados_dir = self.config.get('dados_dir', '../dados')
            data_limite = datetime.now() - timedelta(days=periodo_dias)
            
            relatorio = {
                'periodo': {
                    'inicio': data_limite.isoformat(),
                    'fim': datetime.now().isoformat()
                },
                'arquivos_gerados': {
                    'brutos': len(self._listar_arquivos_recentes(os.path.join(dados_dir, 'brutos'), horas=periodo_dias*24)),
                    'processados': len(self._listar_arquivos_recentes(os.path.join(dados_dir, 'processados'), horas=periodo_dias*24)),
                    'csv': len(self._listar_arquivos_recentes(os.path.join(dados_dir, 'csv'), horas=periodo_dias*24))
                },
                'status_atual': self.orquestrador.verificar_status_agentes()
            }
            
            return relatorio
        
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {str(e)}")
            return {'erro': str(e)}
