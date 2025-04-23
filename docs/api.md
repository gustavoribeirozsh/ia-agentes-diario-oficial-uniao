# API do Sistema de Agentes de IA para o DOU

Este documento descreve as interfaces de programação (APIs) disponíveis para interagir com o sistema de agentes de IA para o Diário Oficial da União (DOU).

## Interfaces de Linha de Comando (CLI)

Cada agente do sistema fornece uma interface de linha de comando para facilitar sua utilização.

### Agente Coletor (DOU-Collector)

```
python -m coletor.main [opções]
```

**Opções:**
- `--data DATA`: Data alvo no formato DD-MM-AAAA
- `--secao {1,2,3,e}`: Seção do DOU (1, 2, 3 ou "e" para extra)
- `--output OUTPUT`: Diretório de saída para os dados coletados
- `--modo {completo,incremental}`: Modo de coleta (padrão: completo)
- `--max-paginas MAX_PAGINAS`: Número máximo de páginas a coletar
- `--config CONFIG`: Caminho para arquivo de configuração

**Exemplo:**
```
python -m coletor.main --data 07-04-2025 --secao 3 --output /dados/brutos
```

### Agente Processador (DOU-Processor)

```
python -m processador.main [opções]
```

**Opções:**
- `--input INPUT`: Caminho para o arquivo JSON com dados brutos do DOU (obrigatório)
- `--output OUTPUT`: Caminho para o arquivo de saída com dados processados
- `--modelo MODELO`: Modelo spaCy a ser utilizado (ex: pt_core_news_lg)
- `--tamanho-resumo TAMANHO_RESUMO`: Tamanho máximo dos resumos gerados
- `--config CONFIG`: Caminho para arquivo de configuração

**Exemplo:**
```
python -m processador.main --input /dados/brutos/2025-04-07_secao3.json --output /dados/processados/processado_2025-04-07_secao3.json
```

### Agente Organizador (DOU-Organizer)

```
python -m organizador.main [opções]
```

**Opções:**
- `--input INPUT`: Caminho para o arquivo JSON com dados processados do DOU (obrigatório)
- `--output OUTPUT`: Caminho para o arquivo CSV de saída
- `--formato {csv,excel,json}`: Formato do arquivo de saída
- `--separador SEPARADOR`: Separador para o arquivo CSV (padrão: ,)
- `--encoding ENCODING`: Encoding para o arquivo CSV (padrão: utf-8)
- `--config CONFIG`: Caminho para arquivo de configuração

**Exemplo:**
```
python -m organizador.main --input /dados/processados/processado_2025-04-07_secao3.json --output /dados/csv/2025-04-07_secao3.csv
```

### Agente de Busca (DOU-Searcher)

```
python -m busca.main [opções]
```

**Opções:**
- `--input INPUT`: Caminho para o arquivo CSV ou diretório com dados organizados
- `--index INDEX`: Nome do índice Elasticsearch
- `--query QUERY`: Consulta de busca
- `--output OUTPUT`: Caminho para o arquivo de saída com resultados da busca
- `--formato {csv,json,txt}`: Formato do arquivo de saída (padrão: json)
- `--data-inicio DATA_INICIO`: Data de início para filtro (formato YYYY-MM-DD)
- `--data-fim DATA_FIM`: Data de fim para filtro (formato YYYY-MM-DD)
- `--secao SECAO`: Seção do DOU para filtro
- `--tipo-documento TIPO_DOCUMENTO`: Tipo de documento para filtro
- `--max-resultados MAX_RESULTADOS`: Número máximo de resultados (padrão: 100)
- `--modo {indexar,buscar,ambos}`: Modo de operação (padrão: buscar)
- `--config CONFIG`: Caminho para arquivo de configuração

**Exemplo:**
```
python -m busca.main --index dou --query "licitação infraestrutura" --output /dados/resultados/busca_licitacao.json
```

### Agente Coordenador (DOU-Coordinator)

```
python -m coordenador.main [opções]
```

**Opções:**
- `--data DATA`: Data alvo no formato DD-MM-AAAA
- `--secao {1,2,3}`: Seção do DOU (1, 2, 3)
- `--modo {completo,coleta,processamento,organizacao,busca,monitor}`: Modo de operação (padrão: completo)
- `--monitor`: Ativar modo de monitoramento
- `--intervalo INTERVALO`: Intervalo de monitoramento em segundos (padrão: 60)
- `--output-dir OUTPUT_DIR`: Diretório de saída para os arquivos gerados
- `--config CONFIG`: Caminho para arquivo de configuração

**Exemplo:**
```
python -m coordenador.main --data 07-04-2025 --secao 3 --modo completo --output-dir /dados
```

## APIs Programáticas

Além das interfaces de linha de comando, os agentes também podem ser utilizados programaticamente em scripts Python.

### Agente Coletor

```python
from coletor.extrator import DOUExtrator
from datetime import datetime

# Inicializa o extrator
extrator = DOUExtrator(
    data=datetime(2025, 4, 7),
    secao=3,
    modo='completo',
    max_paginas=None
)

# Executa a extração
resultado = extrator.extrair()

# Salva os resultados
import json
with open('dados_brutos.json', 'w', encoding='utf-8') as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
```

### Agente Processador

```python
from processador.nlp import ProcessadorNLP
from processador.resumo import GeradorResumo
import json

# Carrega os dados brutos
with open('dados_brutos.json', 'r', encoding='utf-8') as f:
    dados_brutos = json.load(f)

# Inicializa o processador NLP
processador = ProcessadorNLP(modelo='pt_core_news_lg')

# Inicializa o gerador de resumos
gerador_resumo = GeradorResumo(tamanho_maximo=200)

# Processa uma publicação
texto = dados_brutos['paginas'][0]['publicacoes'][0]['corpo']
doc = processador.processar_texto(texto)
entidades = processador.extrair_entidades(doc)
resumo = gerador_resumo.gerar_resumo(texto)
palavras_chave = processador.extrair_palavras_chave(doc)
tipo_documento = processador.classificar_documento(doc)

print(f"Resumo: {resumo}")
print(f"Entidades: {entidades}")
print(f"Palavras-chave: {palavras_chave}")
print(f"Tipo de documento: {tipo_documento}")
```

### Agente Organizador

```python
from organizador.csv_builder import CSVBuilder
from organizador.validador import ValidadorDados
import json

# Carrega os dados processados
with open('dados_processados.json', 'r', encoding='utf-8') as f:
    dados_processados = json.load(f)

# Valida os dados
validador = ValidadorDados()
if validador.validar(dados_processados):
    print("Dados válidos")
else:
    print(f"Erros de validação: {validador.erros}")
    exit(1)

# Inicializa o construtor de CSV
csv_builder = CSVBuilder(separador=',', encoding='utf-8')

# Extrai registros dos dados processados
registros = []
for pagina in dados_processados['paginas']:
    for publicacao in pagina['publicacoes']:
        registro = {
            'data_publicacao': dados_processados['data'],
            'secao': dados_processados['secao'],
            'numero_pagina': pagina['numero_pagina'],
            'titulo': publicacao['titulo'],
            'resumo': publicacao['resumo']
        }
        registros.append(registro)

# Gera o arquivo CSV
csv_builder.gerar_csv(registros, 'dados_organizados.csv')
```

### Agente de Busca

```python
from busca.indexador import Indexador
from busca.consulta import ProcessadorConsulta

# Inicializa o indexador
indexador = Indexador(host='localhost', port=9200)

# Indexa um arquivo CSV
resultado_indexacao = indexador.indexar_arquivo('dados_organizados.csv', 'dou')
print(f"Indexação: {resultado_indexacao}")

# Inicializa o processador de consulta
processador_consulta = ProcessadorConsulta(host='localhost', port=9200)

# Executa uma consulta
resultados = processador_consulta.buscar(
    'dou',
    query='licitação infraestrutura',
    filtros={
        'data_inicio': '2025-04-01',
        'data_fim': '2025-04-30',
        'secao': '3'
    },
    max_resultados=10
)

# Exibe os resultados
for hit in resultados['hits']:
    print(f"Score: {hit['_score']}")
    print(f"Título: {hit['_source']['titulo']}")
    print(f"Resumo: {hit['_source']['resumo']}")
    print("-" * 50)
```

### Agente Coordenador

```python
from coordenador.orquestrador import Orquestrador
from coordenador.monitor import Monitor
from utils.config import Config
from datetime import datetime

# Carrega configurações
config = Config('config.json')

# Inicializa o orquestrador
orquestrador = Orquestrador(config)

# Executa o fluxo completo para uma data específica
data = datetime(2025, 4, 7)
secao = 3
output_dir = '/dados'

# Etapa 1: Coleta
arquivo_bruto = orquestrador.executar_coleta(data, secao, output_dir)

# Etapa 2: Processamento
arquivo_processado = orquestrador.executar_processamento(arquivo_bruto, output_dir)

# Etapa 3: Organização
arquivo_organizado = orquestrador.executar_organizacao(arquivo_processado, output_dir)

# Etapa 4: Indexação para busca
resultado_indexacao = orquestrador.executar_indexacao(arquivo_organizado)

print(f"Arquivo bruto: {arquivo_bruto}")
print(f"Arquivo processado: {arquivo_processado}")
print(f"Arquivo organizado: {arquivo_organizado}")
print(f"Resultado da indexação: {resultado_indexacao}")

# Inicializa o monitor
monitor = Monitor(config)

# Gera um relatório de atividades
relatorio = monitor.gerar_relatorio(periodo_dias=7)
print(f"Relatório: {relatorio}")
```

## Formato dos Dados

### Dados Brutos (JSON)

```json
{
  "data": "2025-04-07",
  "secao": 3,
  "total_paginas": 303,
  "paginas": [
    {
      "numero_pagina": 1,
      "metadados": {
        "titulo": "DIÁRIO OFICIAL DA UNIÃO",
        "data_publicacao": "07/04/2025",
        "secao": 3
      },
      "html": "...",
      "texto": "...",
      "publicacoes": [
        {
          "id": "pub_1",
          "titulo": "EXTRATO DE CONTRATO Nº 123/2025",
          "corpo": "...",
          "html": "..."
        },
        ...
      ]
    },
    ...
  ],
  "secoes_extras": [],
  "timestamp_extracao": "2025-04-07T10:15:30.123456"
}
```

### Dados Processados (JSON)

```json
{
  "data": "2025-04-07",
  "secao": 3,
  "total_paginas": 303,
  "timestamp_processamento": "2025-04-07T10:30:45.123456",
  "paginas": [
    {
      "numero_pagina": 1,
      "metadados": {
        "titulo": "DIÁRIO OFICIAL DA UNIÃO",
        "data_publicacao": "07/04/2025",
        "secao": 3
      },
      "publicacoes": [
        {
          "id": "pub_1",
          "titulo": "EXTRATO DE CONTRATO Nº 123/2025",
          "resumo": "Contrato entre Ministério da Infraestrutura e Empresa XYZ para construção de rodovia...",
          "entidades": [
            {"texto": "Ministério da Infraestrutura", "tipo": "ORG", "inicio": 15, "fim": 43},
            {"texto": "Empresa XYZ", "tipo": "ORG", "inicio": 48, "fim": 59},
            ...
          ],
          "palavras_chave": [
            {"palavra": "contrato", "frequencia": 5},
            {"palavra": "infraestrutura", "frequencia": 3},
            ...
          ],
          "tipo_documento": "contrato",
          "metadados_extraidos": {
            "datas": ["01/03/2025", "31/12/2025"],
            "valores_monetarios": ["R$ 10.500.000,00"],
            "numeros_processos": ["12345.678901/2025-01"],
            "cnpj": ["12.345.678/0001-90"],
            "cpf": []
          }
        },
        ...
      ]
    },
    ...
  ]
}
```

### Dados Organizados (CSV)

```csv
data_publicacao,secao,numero_pagina,titulo,resumo,entidades,palavras_chave,tipo_documento,id,datas_mencionadas,valores_monetarios,numeros_processos,cnpj,cpf
2025-04-07,3,1,EXTRATO DE CONTRATO Nº 123/2025,Contrato entre Ministério da Infraestrutura e Empresa XYZ para construção de rodovia...,Ministério da Infraestrutura,Empresa XYZ,contrato,infraestrutura,contrato,pub_1,01/03/2025,31/12/2025,R$ 10.500.000,00,12345.678901/2025-01,12.345.678/0001-90,
...
```

### Resultados de Busca (JSON)

```json
{
  "success": true,
  "total": 15,
  "took": 25,
  "hits": [
    {
      "_index": "dou",
      "_id": "pub_1",
      "_score": 0.9876543,
      "_source": {
        "data_publicacao": "2025-04-07",
        "secao": "3",
        "numero_pagina": "1",
        "titulo": "EXTRATO DE CONTRATO Nº 123/2025",
        "resumo": "Contrato entre Ministério da Infraestrutura e Empresa XYZ para construção de rodovia...",
        "tipo_documento": "contrato"
      }
    },
    ...
  ]
}
```

## Integração com Outros Sistemas

### Webhooks

O sistema não fornece webhooks nativamente, mas você pode implementar notificações via webhook utilizando o sistema de mensageria:

```python
from utils.mensageria import consumir_mensagens
import requests

def notificar_webhook(mensagem):
    # URL do webhook
    webhook_url = "https://exemplo.com/webhook"
    
    # Envia a mensagem para o webhook
    response = requests.post(webhook_url, json=mensagem)
    print(f"Notificação enviada: {response.status_code}")

# Consome mensagens e notifica via webhook
consumir_mensagens('coleta_concluida', notificar_webhook)
```

### Exportação de Dados

Para integração com outros sistemas, você pode utilizar os formatos de exportação suportados pelo Agente Organizador:

- CSV: Para sistemas de planilhas e bancos de dados
- JSON: Para APIs e sistemas web
- Excel: Para usuários finais e relatórios

### Integração com Elasticsearch

O Agente de Busca já fornece integração com Elasticsearch, que pode ser utilizado por outros sistemas para consultas avançadas:

```python
from elasticsearch import Elasticsearch

# Conecta ao Elasticsearch
es = Elasticsearch(["http://localhost:9200"])

# Executa uma consulta
response = es.search(
    index="dou",
    body={
        "query": {
            "bool": {
                "must": [
                    {"match": {"texto_completo": "licitação infraestrutura"}}
                ],
                "filter": [
                    {"term": {"secao": "3"}},
                    {"range": {"data_publicacao": {"gte": "2025-04-01", "lte": "2025-04-30"}}}
                ]
            }
        }
    }
)

# Processa os resultados
for hit in response['hits']['hits']:
    print(hit['_source']['titulo'])
```

## Considerações de Segurança

- As APIs não implementam autenticação por padrão. Para ambientes de produção, recomenda-se implementar um mecanismo de autenticação adequado.
- Para expor as APIs via HTTP, considere utilizar um framework como Flask ou FastAPI com middleware de segurança.
- O acesso ao Elasticsearch deve ser protegido em ambientes de produção, utilizando autenticação e TLS.
