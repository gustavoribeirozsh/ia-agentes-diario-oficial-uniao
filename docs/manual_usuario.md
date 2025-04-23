# Documentação do Sistema de Agentes de IA para o Diário Oficial da União (DOU)

## Visão Geral

Este documento fornece instruções detalhadas sobre a instalação, configuração e uso do sistema de agentes de IA para o Diário Oficial da União (DOU). O sistema é composto por cinco agentes especializados que trabalham em conjunto para automatizar a extração, processamento e organização de dados do DOU.

## Arquitetura do Sistema

O sistema é composto pelos seguintes agentes:

1. **Agente Coletor (DOU-Collector)**: Responsável por acessar o site oficial do DOU e extrair o conteúdo bruto das publicações.
2. **Agente Processador (DOU-Processor)**: Transforma o conteúdo bruto em dados estruturados usando técnicas de processamento de linguagem natural.
3. **Agente Organizador (DOU-Organizer)**: Compila os dados em formato CSV com as colunas: Data de Publicação, Seção, Número da Página, Título e Resumo do Conteúdo.
4. **Agente de Busca (DOU-Searcher)**: Permite a recuperação eficiente de informações específicas dentro dos dados organizados.
5. **Agente Coordenador (DOU-Coordinator)**: Gerencia o fluxo de trabalho entre todos os outros agentes e serve como ponto de interação principal.

## Requisitos do Sistema

- Python 3.8 ou superior
- Bibliotecas Python (instaláveis via `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - selenium
  - pandas
  - nltk
  - spacy
  - pika (para comunicação entre agentes)
  - elasticsearch-py (para o agente de busca)
  - lxml
  - python-dotenv
  - tqdm
  - pytest
  - black
  - isort
  - flake8

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/agentes-dou.git
cd agentes-dou
```

2. Crie e ative um ambiente virtual:
```
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```
pip install -r requirements.txt
```

4. Baixe os modelos necessários para o spaCy:
```
python -m spacy download pt_core_news_lg
```

5. Baixe os recursos necessários para o NLTK:
```
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

6. (Opcional) Configure o Elasticsearch para o Agente de Busca:
   - Instale o Elasticsearch seguindo as instruções em https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html
   - Inicie o serviço Elasticsearch

## Configuração

O sistema pode ser configurado através de um arquivo JSON. Crie um arquivo `config.json` na raiz do projeto com as seguintes configurações:

```json
{
  "dados_dir": "/caminho/para/diretorio/dados",
  "cache_dir": "/caminho/para/diretorio/cache",
  
  "usar_cache": true,
  "timeout": 30,
  "max_retries": 3,
  "delay_entre_requisicoes": [1, 3],
  "usar_selenium": false,
  "verificar_secoes_extras": true,
  
  "modelo_spacy": "pt_core_news_lg",
  "tamanho_maximo_resumo": 200,
  "limiar_similaridade": 0.7,
  
  "formato_saida": "csv",
  "separador_csv": ",",
  "encoding_csv": "utf-8",
  
  "elasticsearch_host": "localhost",
  "elasticsearch_port": 9200,
  "elasticsearch_index": "dou",
  
  "intervalo_monitoramento": 60,
  "usar_mensageria": false,
  "rabbitmq_host": "localhost",
  "rabbitmq_port": 5672,
  
  "nivel_log": "INFO",
  "arquivo_log": "/caminho/para/logs/agentes_dou.log"
}
```

## Uso

### Executando o Sistema Completo

Para iniciar todo o sistema com o Agente Coordenador gerenciando o fluxo de trabalho:

```
python -m coordenador.main --data 07-04-2025 --secao 3 --config config.json
```

### Executando Agentes Individualmente

Cada agente pode ser executado individualmente para testes:

#### Agente Coletor

```
python -m coletor.main --data 07-04-2025 --secao 3 --output /caminho/para/saida
```

Parâmetros:
- `--data`: Data alvo no formato DD-MM-AAAA
- `--secao`: Seção do DOU (1, 2, 3 ou "e" para extra)
- `--output`: Diretório de saída para os dados coletados
- `--modo`: Modo de coleta: completo ou incremental
- `--max-paginas`: Número máximo de páginas a coletar
- `--config`: Caminho para arquivo de configuração

#### Agente Processador

```
python -m processador.main --input /caminho/para/arquivo/bruto.json --output /caminho/para/saida/processado.json
```

Parâmetros:
- `--input`: Caminho para o arquivo JSON com dados brutos do DOU
- `--output`: Caminho para o arquivo de saída com dados processados
- `--modelo`: Modelo spaCy a ser utilizado (ex: pt_core_news_lg)
- `--tamanho-resumo`: Tamanho máximo dos resumos gerados
- `--config`: Caminho para arquivo de configuração

#### Agente Organizador

```
python -m organizador.main --input /caminho/para/arquivo/processado.json --output /caminho/para/saida/organizado.csv
```

Parâmetros:
- `--input`: Caminho para o arquivo JSON com dados processados do DOU
- `--output`: Caminho para o arquivo CSV de saída
- `--formato`: Formato do arquivo de saída (csv, excel, json)
- `--separador`: Separador para o arquivo CSV
- `--encoding`: Encoding para o arquivo CSV
- `--config`: Caminho para arquivo de configuração

#### Agente de Busca

```
python -m busca.main --index dou_secao3 --query "licitação infraestrutura" --output /caminho/para/saida/resultados.json
```

Parâmetros:
- `--input`: Caminho para o arquivo CSV ou diretório com dados organizados
- `--index`: Nome do índice Elasticsearch
- `--query`: Consulta de busca
- `--output`: Caminho para o arquivo de saída com resultados da busca
- `--formato`: Formato do arquivo de saída (csv, json, txt)
- `--data-inicio`: Data de início para filtro (formato YYYY-MM-DD)
- `--data-fim`: Data de fim para filtro (formato YYYY-MM-DD)
- `--secao`: Seção do DOU para filtro
- `--tipo-documento`: Tipo de documento para filtro
- `--max-resultados`: Número máximo de resultados
- `--modo`: Modo de operação: indexar, buscar ou ambos
- `--config`: Caminho para arquivo de configuração

#### Agente Coordenador

```
python -m coordenador.main --data 07-04-2025 --secao 3 --modo completo --output-dir /caminho/para/saida
```

Parâmetros:
- `--data`: Data alvo no formato DD-MM-AAAA
- `--secao`: Seção do DOU (1, 2, 3)
- `--modo`: Modo de operação do coordenador (completo, coleta, processamento, organizacao, busca, monitor)
- `--monitor`: Ativar modo de monitoramento
- `--intervalo`: Intervalo de monitoramento em segundos
- `--output-dir`: Diretório de saída para os arquivos gerados
- `--config`: Caminho para arquivo de configuração

## Fluxo de Trabalho

1. O **Agente Coordenador** inicia o processo, definindo parâmetros como data alvo e seções de interesse.
2. O **Agente Coletor** acessa o site do DOU e extrai o conteúdo bruto das publicações especificadas.
3. O **Agente Processador** transforma os dados brutos em estruturas organizadas, identificando metadados.
4. O **Agente Organizador** compila os dados processados em arquivos CSV com a estrutura definida.
5. O **Agente de Busca** indexa os dados organizados para permitir consultas eficientes.

## Estrutura de Diretórios

```
agentes_dou/
├── coletor/              # Agente Coletor
│   ├── __init__.py
│   ├── main.py           # Ponto de entrada
│   ├── extrator.py       # Lógica de extração
│   └── cache.py          # Sistema de cache
├── processador/          # Agente Processador
│   ├── __init__.py
│   ├── main.py           # Ponto de entrada
│   ├── nlp.py            # Processamento de linguagem natural
│   └── resumo.py         # Geração de resumos
├── organizador/          # Agente Organizador
│   ├── __init__.py
│   ├── main.py           # Ponto de entrada
│   ├── csv_builder.py    # Construção de CSV
│   └── validador.py      # Validação de dados
├── busca/                # Agente de Busca
│   ├── __init__.py
│   ├── main.py           # Ponto de entrada
│   ├── indexador.py      # Indexação de documentos
│   └── consulta.py       # Processamento de consultas
├── coordenador/          # Agente Coordenador
│   ├── __init__.py
│   ├── main.py           # Ponto de entrada
│   ├── orquestrador.py   # Orquestração de agentes
│   └── monitor.py        # Monitoramento de status
├── utils/                # Utilitários compartilhados
│   ├── __init__.py
│   ├── config.py         # Configurações globais
│   ├── logger.py         # Sistema de logging
│   └── mensageria.py     # Sistema de mensagens
├── dados/                # Diretório para armazenar dados
│   ├── brutos/           # Dados brutos coletados
│   ├── processados/      # Dados após processamento
│   └── csv/              # Arquivos CSV finais
├── requirements.txt      # Dependências do projeto
└── README.md             # Documentação básica
```

## Solução de Problemas

### Problemas Comuns

1. **Erro ao conectar ao site do DOU**:
   - Verifique sua conexão com a internet
   - Aumente o valor de `timeout` nas configurações
   - Aumente o valor de `max_retries` nas configurações
   - Ative o modo `usar_selenium` nas configurações

2. **Erro ao carregar modelo spaCy**:
   - Verifique se o modelo foi baixado corretamente: `python -m spacy validate`
   - Tente baixar um modelo menor: `python -m spacy download pt_core_news_sm`

3. **Erro ao conectar ao Elasticsearch**:
   - Verifique se o serviço Elasticsearch está em execução
   - Verifique as configurações de host e porta
   - Verifique se há restrições de firewall

4. **Memória insuficiente**:
   - Reduza o tamanho do lote de processamento
   - Use um modelo spaCy menor
   - Aumente a memória disponível para o Python

### Logs

Os logs são armazenados no arquivo especificado na configuração `arquivo_log`. Você pode ajustar o nível de log através da configuração `nivel_log`.

## Contribuições

Contribuições são bem-vindas! Por favor, sinta-se à vontade para enviar um Pull Request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
