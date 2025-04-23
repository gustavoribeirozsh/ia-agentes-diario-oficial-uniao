# Arquitetura do Sistema de Agentes de IA para o DOU

## Visão Geral da Arquitetura

Este documento descreve a arquitetura técnica do sistema de agentes de IA para o Diário Oficial da União (DOU). O sistema foi projetado seguindo princípios de arquitetura modular, com agentes especializados que se comunicam entre si para formar um pipeline completo de processamento de dados.

## Componentes Principais

### 1. Agentes Especializados

O sistema é composto por cinco agentes especializados, cada um com responsabilidades bem definidas:

#### 1.1. Agente Coletor (DOU-Collector)

**Responsabilidade**: Acessar o site oficial do DOU e extrair o conteúdo bruto das publicações.

**Componentes internos**:
- **Extrator**: Implementa a lógica de acesso ao site do DOU e extração de conteúdo.
- **Cache**: Armazena temporariamente o conteúdo extraído para evitar requisições repetidas.

**Fluxo de dados**:
1. Recebe parâmetros de data e seção
2. Acessa o site do DOU
3. Extrai o conteúdo bruto das páginas
4. Salva os dados em formato JSON

#### 1.2. Agente Processador (DOU-Processor)

**Responsabilidade**: Transformar o conteúdo bruto em dados estruturados usando técnicas de processamento de linguagem natural.

**Componentes internos**:
- **Processador NLP**: Aplica técnicas de processamento de linguagem natural aos textos.
- **Gerador de Resumos**: Cria resumos automáticos dos textos extraídos.

**Fluxo de dados**:
1. Carrega os dados brutos em formato JSON
2. Processa o texto usando spaCy
3. Extrai entidades, palavras-chave e metadados
4. Gera resumos dos textos
5. Salva os dados processados em formato JSON

#### 1.3. Agente Organizador (DOU-Organizer)

**Responsabilidade**: Compilar os dados em formato CSV com colunas estruturadas.

**Componentes internos**:
- **CSV Builder**: Gera arquivos CSV, Excel ou JSON a partir dos dados processados.
- **Validador**: Verifica a integridade e consistência dos dados.

**Fluxo de dados**:
1. Carrega os dados processados em formato JSON
2. Valida os dados
3. Organiza os dados em formato tabular
4. Salva os dados em formato CSV, Excel ou JSON

#### 1.4. Agente de Busca (DOU-Searcher)

**Responsabilidade**: Permitir a recuperação eficiente de informações específicas dentro dos dados organizados.

**Componentes internos**:
- **Indexador**: Indexa os dados no Elasticsearch.
- **Processador de Consulta**: Executa consultas e processa os resultados.

**Fluxo de dados**:
1. Indexa os dados organizados no Elasticsearch
2. Recebe consultas de busca
3. Executa as consultas no Elasticsearch
4. Processa e formata os resultados
5. Retorna os resultados da busca

#### 1.5. Agente Coordenador (DOU-Coordinator)

**Responsabilidade**: Gerenciar o fluxo de trabalho entre todos os outros agentes.

**Componentes internos**:
- **Orquestrador**: Coordena a execução dos diferentes agentes.
- **Monitor**: Monitora o status dos agentes e o progresso das tarefas.

**Fluxo de dados**:
1. Recebe parâmetros de execução
2. Coordena a execução sequencial dos agentes
3. Monitora o progresso e status das tarefas
4. Gera relatórios de execução

### 2. Utilitários Compartilhados

O sistema inclui módulos utilitários compartilhados entre os agentes:

#### 2.1. Configuração (utils.config)

Gerencia as configurações globais do sistema, carregando-as de um arquivo JSON e fornecendo métodos para acessá-las.

#### 2.2. Logging (utils.logger)

Implementa um sistema de logging consistente para todos os agentes, com suporte a diferentes níveis de log e rotação de arquivos.

#### 2.3. Mensageria (utils.mensageria)

Fornece funcionalidades para comunicação assíncrona entre os agentes, utilizando RabbitMQ como broker de mensagens.

## Fluxo de Trabalho do Sistema

O fluxo de trabalho completo do sistema segue estas etapas:

1. O **Agente Coordenador** inicia o processo, definindo parâmetros como data alvo e seções de interesse.
2. O **Agente Coletor** acessa o site do DOU e extrai o conteúdo bruto das publicações especificadas.
3. O **Agente Processador** transforma os dados brutos em estruturas organizadas, identificando metadados.
4. O **Agente Organizador** compila os dados processados em arquivos CSV com a estrutura definida.
5. O **Agente de Busca** indexa os dados organizados para permitir consultas eficientes.

## Diagrama de Arquitetura

```
+------------------+     +---------------------+     +--------------------+
| Agente Coletor   |---->| Agente Processador  |---->| Agente Organizador |
| (DOU-Collector)  |     | (DOU-Processor)     |     | (DOU-Organizer)    |
+------------------+     +---------------------+     +--------------------+
                                                            |
                                                            v
+------------------+     +---------------------+     +--------------------+
| Agente           |<----| Agente Coordenador  |<----| Agente de Busca    |
| Coordenador      |     | (DOU-Coordinator)   |     | (DOU-Searcher)     |
| (Monitor)        |     |                     |     |                    |
+------------------+     +---------------------+     +--------------------+
        ^                         |
        |                         v
+------------------+     +---------------------+
| Utilitários      |<--->| Sistema de          |
| Compartilhados   |     | Armazenamento       |
+------------------+     +---------------------+
```

## Armazenamento de Dados

O sistema utiliza diferentes formatos de armazenamento em cada etapa do processamento:

1. **Dados Brutos**: Armazenados em formato JSON, contendo o conteúdo extraído do DOU.
2. **Dados Processados**: Armazenados em formato JSON, com estruturas enriquecidas por processamento de linguagem natural.
3. **Dados Organizados**: Armazenados em formato CSV, Excel ou JSON, com estrutura tabular.
4. **Índice de Busca**: Armazenado no Elasticsearch, otimizado para consultas rápidas.

## Considerações Técnicas

### Escalabilidade

O sistema foi projetado para ser escalável de várias formas:

- **Escalabilidade Horizontal**: Cada agente pode ser executado em máquinas diferentes.
- **Processamento em Lote**: Suporte a processamento de grandes volumes de dados em lotes.
- **Cache**: Implementação de cache para reduzir requisições repetidas.

### Resiliência

Mecanismos de resiliência implementados:

- **Retry com Backoff Exponencial**: Para lidar com falhas temporárias de rede.
- **Validação de Dados**: Para garantir a integridade dos dados em cada etapa.
- **Logging Detalhado**: Para facilitar a identificação e resolução de problemas.

### Extensibilidade

O sistema foi projetado para ser facilmente extensível:

- **Arquitetura Modular**: Novos agentes podem ser adicionados sem modificar os existentes.
- **Configuração Centralizada**: Parâmetros configuráveis sem necessidade de modificar o código.
- **Interfaces Bem Definidas**: Comunicação clara entre os componentes.

## Requisitos Técnicos

### Software

- Python 3.8 ou superior
- Elasticsearch 7.x ou superior (para o Agente de Busca)
- RabbitMQ 3.x ou superior (opcional, para comunicação entre agentes)

### Hardware Recomendado

- CPU: 4 cores ou mais
- RAM: 8GB ou mais (16GB recomendado para processamento de grandes volumes)
- Armazenamento: 50GB ou mais, dependendo do volume de dados a ser processado

## Considerações de Segurança

- **Acesso ao DOU**: O sistema respeita os termos de uso do site do DOU, implementando delays entre requisições.
- **Armazenamento de Dados**: Os dados são armazenados localmente, sem envio para serviços externos.
- **Configuração**: Senhas e credenciais devem ser armazenadas em variáveis de ambiente ou arquivos protegidos.

## Limitações Conhecidas

- O sistema depende da estrutura atual do site do DOU. Mudanças significativas no site podem requerer atualizações no Agente Coletor.
- O processamento de linguagem natural tem limitações inerentes na compreensão de contexto e semântica.
- A performance do Elasticsearch depende da configuração adequada e dos recursos de hardware disponíveis.
