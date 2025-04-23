"""
Módulo de mensageria para os agentes do DOU.

Este módulo implementa funções para comunicação assíncrona
entre os diferentes agentes do sistema.
"""

import json
import pika
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('utils.mensageria')

def conectar_rabbitmq(host='localhost', porta=5672, usuario='guest', senha='guest'):
    """
    Estabelece conexão com o servidor RabbitMQ.
    
    Args:
        host (str): Host do servidor RabbitMQ
        porta (int): Porta do servidor RabbitMQ
        usuario (str): Nome de usuário para autenticação
        senha (str): Senha para autenticação
        
    Returns:
        pika.BlockingConnection: Conexão com o RabbitMQ
    """
    try:
        credentials = pika.PlainCredentials(usuario, senha)
        parameters = pika.ConnectionParameters(
            host=host,
            port=porta,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        return pika.BlockingConnection(parameters)
    except Exception as e:
        logger.error(f"Erro ao conectar ao RabbitMQ: {str(e)}")
        raise

def publicar_mensagem(topico, mensagem, host='localhost', porta=5672, usuario='guest', senha='guest'):
    """
    Publica uma mensagem em um tópico específico.
    
    Args:
        topico (str): Nome do tópico (exchange)
        mensagem (dict): Mensagem a ser publicada
        host (str): Host do servidor RabbitMQ
        porta (int): Porta do servidor RabbitMQ
        usuario (str): Nome de usuário para autenticação
        senha (str): Senha para autenticação
        
    Returns:
        bool: True se a mensagem foi publicada com sucesso, False caso contrário
    """
    try:
        # Estabelece conexão
        connection = conectar_rabbitmq(host, porta, usuario, senha)
        channel = connection.channel()
        
        # Declara o exchange
        channel.exchange_declare(exchange=topico, exchange_type='fanout', durable=True)
        
        # Converte a mensagem para JSON
        mensagem_json = json.dumps(mensagem, ensure_ascii=False)
        
        # Publica a mensagem
        channel.basic_publish(
            exchange=topico,
            routing_key='',
            body=mensagem_json.encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensagem persistente
                content_type='application/json',
                content_encoding='utf-8'
            )
        )
        
        # Fecha a conexão
        connection.close()
        
        logger.debug(f"Mensagem publicada no tópico '{topico}'")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao publicar mensagem no tópico '{topico}': {str(e)}")
        return False

def consumir_mensagens(topico, callback, host='localhost', porta=5672, usuario='guest', senha='guest'):
    """
    Consome mensagens de um tópico específico.
    
    Args:
        topico (str): Nome do tópico (exchange)
        callback (callable): Função de callback para processar as mensagens
        host (str): Host do servidor RabbitMQ
        porta (int): Porta do servidor RabbitMQ
        usuario (str): Nome de usuário para autenticação
        senha (str): Senha para autenticação
    """
    try:
        # Estabelece conexão
        connection = conectar_rabbitmq(host, porta, usuario, senha)
        channel = connection.channel()
        
        # Declara o exchange
        channel.exchange_declare(exchange=topico, exchange_type='fanout', durable=True)
        
        # Declara uma fila exclusiva
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        
        # Vincula a fila ao exchange
        channel.queue_bind(exchange=topico, queue=queue_name)
        
        # Define o callback para processar mensagens
        def process_message(ch, method, properties, body):
            try:
                mensagem = json.loads(body.decode('utf-8'))
                callback(mensagem)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Erro ao processar mensagem: {str(e)}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # Configura o consumo
        channel.basic_consume(queue=queue_name, on_message_callback=process_message)
        
        logger.info(f"Iniciando consumo de mensagens do tópico '{topico}'")
        channel.start_consuming()
    
    except Exception as e:
        logger.error(f"Erro ao consumir mensagens do tópico '{topico}': {str(e)}")
        raise

def consumir_mensagem_unica(topico, timeout=30, host='localhost', porta=5672, usuario='guest', senha='guest'):
    """
    Consome uma única mensagem de um tópico específico.
    
    Args:
        topico (str): Nome do tópico (exchange)
        timeout (int): Tempo máximo de espera em segundos
        host (str): Host do servidor RabbitMQ
        porta (int): Porta do servidor RabbitMQ
        usuario (str): Nome de usuário para autenticação
        senha (str): Senha para autenticação
        
    Returns:
        dict: Mensagem consumida ou None se ocorrer timeout
    """
    try:
        # Estabelece conexão
        connection = conectar_rabbitmq(host, porta, usuario, senha)
        channel = connection.channel()
        
        # Declara o exchange
        channel.exchange_declare(exchange=topico, exchange_type='fanout', durable=True)
        
        # Declara uma fila exclusiva
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        
        # Vincula a fila ao exchange
        channel.queue_bind(exchange=topico, queue=queue_name)
        
        # Variável para armazenar a mensagem
        mensagem_recebida = None
        
        # Define o callback para processar mensagens
        def process_message(ch, method, properties, body):
            nonlocal mensagem_recebida
            mensagem_recebida = json.loads(body.decode('utf-8'))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            connection.close()
        
        # Configura o consumo
        channel.basic_consume(queue=queue_name, on_message_callback=process_message)
        
        # Inicia o consumo com timeout
        connection.add_timeout(timeout, lambda: connection.close())
        
        try:
            channel.start_consuming()
        except pika.exceptions.ConnectionClosedByBroker:
            pass
        
        return mensagem_recebida
    
    except Exception as e:
        logger.error(f"Erro ao consumir mensagem do tópico '{topico}': {str(e)}")
        return None
