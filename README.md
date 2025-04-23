# Agentes de IA para o Diário Oficial da União (DOU)

Este projeto implementa um sistema de cinco agentes de IA especializados para automatizar a extração, processamento e organização de dados do Diário Oficial da União (DOU) do Brasil.

## Visão Geral

O sistema é composto por cinco agentes que trabalham em conjunto:

1. **Agente Coletor (DOU-Collector)**: Responsável por acessar o site oficial do DOU e extrair o conteúdo bruto das publicações.
2. **Agente Processador (DOU-Processor)**: Transforma o conteúdo bruto em dados estruturados usando técnicas de processamento de linguagem natural.
3. **Agente Organizador (DOU-Organizer)**: Compila os dados em formato CSV com colunas estruturadas.
4. **Agente de Busca (DOU-Searcher)**: Permite a recuperação eficiente de informações específicas dentro dos dados organizados.
5. **Agente Coordenador (DOU-Coordinator)**: Gerencia o fluxo de trabalho entre todos os outros agentes.

## Requisitos

- Python 3.8+
- Bibliotecas Python (instaláveis via `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - selenium
  - pandas
  - nltk
  - spacy
  - pika (para comunicação entre agentes)
  - elasticsearch-py (para o agente de busca)

## Instalação

1. Clone este repositório:
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

## Uso

### Executando o Sistema Completo

Para iniciar todo o sistema com o Agente Coordenador gerenciando o fluxo de trabalho:

```
python -m coordenador.main --data 07-04-2025 --secao 3
```

### Executando Agentes Individualmente

Cada agente pode ser executado individualmente para testes:

```
# Agente Coletor
python -m coletor.main --data 07-04-2025 --secao 3

# Agente Processador
python -m processador.main --input dados/brutos/07-04-2025_secao3.json

# Agente Organizador
python -m organizador.main --input dados/processados/07-04-2025_secao3.json

# Agente de Busca
python -m busca.main --index dou_secao3 --query "licitação infraestrutura"

# Agente Coordenador (modo monitoramento)
python -m coordenador.main --monitor
```

## Estrutura do Projeto

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
├── docs/                 # Documentação
│   ├── arquitetura.md    # Documentação da arquitetura
│   └── api.md            # Documentação da API
├── dados/                # Diretório para armazenar dados
│   ├── brutos/           # Dados brutos coletados
│   ├── processados/      # Dados após processamento
│   └── csv/              # Arquivos CSV finais
├── requirements.txt      # Dependências do projeto
└── README.md             # Este arquivo
```

## Fluxo de Trabalho

1. O **Agente Coordenador** inicia o processo, definindo parâmetros como data alvo e seções de interesse.
2. O **Agente Coletor** acessa o site do DOU e extrai o conteúdo bruto das publicações especificadas.
3. O **Agente Processador** transforma os dados brutos em estruturas organizadas, identificando metadados.
4. O **Agente Organizador** compila os dados processados em arquivos CSV com a estrutura definida.
5. O **Agente de Busca** indexa os dados organizados para permitir consultas eficientes.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contribuições

Contribuições são bem-vindas! Por favor, sinta-se à vontade para enviar um Pull Request.
