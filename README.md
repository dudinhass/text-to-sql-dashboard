# 🌍 Global Crisis Data Assistant | AI-Powered Text-to-SQL

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![LangChain](https://img.shields.io/badge/LangChain-Groq_Llama_3.3-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)

<div align="center">
  
![Demonstração do Projeto](demo.mp4)

</div>

---

## 🎯 O Problema vs. A Solução

Dashboards estáticos estão obsoletos. Gráficos pré-construídos respondem apenas às perguntas que alguém já fez antes — e no mundo de crises geopolíticas e choques econômicos em tempo real, isso é insuficiente. Analistas perdem horas formatando queries SQL manualmente, apenas para obter um número que ficará desatualizado amanhã.

O **Global Crisis Data Assistant** democratiza o acesso aos dados. Qualquer pessoa — analista, jornalista, gestor — pode digitar uma pergunta em português (*"Como o sentimento das notícias afetou o preço do Diesel no período da crise do Irã?"*) e receber em segundos uma resposta analítica estruturada, com gráfico e SQL auditável. O sistema traduz linguagem natural em queries SQL complexas com JOINs, agregações e filtros temporais, usando o modelo Llama 3.3 70B via Groq — tudo isso sobre um banco de dados relacional com dados reais de petróleo, câmbio, frete marítimo, mercado de ações e sentimento de notícias.

---

## 🏗️ Arquitetura do Projeto

```
Fontes de Dados Brutas
        │
        ▼
┌───────────────────┐
│   ETL (Pandas)    │  ← etl_postgres.py
│  Coleta, limpa e  │
│  normaliza os     │
│  dados históricos │
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────┐
│   Banco Relacional — Star Schema  │  ← Neon / PostgreSQL
│                                   │
│   dim_tempo  ◄──  fato_petroleo   │
│              ◄──  fato_combustivel│
│              ◄──  fato_moedas     │
│              ◄──  fato_mercado_   │
│                   acoes           │
│              ◄──  fato_frete_     │
│                   maritimo        │
│              ◄──  fato_sentimento_│
│                   noticias        │
└────────┬──────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│   Back-end FastAPI + LRU Cache       │  ← main.py
│                                      │
│   POST /chat  →  LangChain SQL Agent │
│                  (Groq Llama 3.3 70B)│
│                  ↓                   │
│              Executa SELECT no BD    │
│                  ↓                   │
│          Retorna answer + SQL +      │
│              chart_data (JSON)       │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│   Front-end SaaS UI (Bento Box)  │  ← static/index.html + script.js
│                                  │
│  • Resposta Markdown renderizada │
│  • Gráfico Chart.js              │
│  • Query SQL expansível          │
│  • Suggestion Chips              │
└──────────────────────────────────┘
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos

- Python 3.11+
- Uma conta no [Neon](https://neon.tech) (ou outro PostgreSQL) com o banco já populado via `etl_postgres.py`
- Uma API Key do [Groq](https://console.groq.com) (gratuita)

### Passo a passo

**1. Clone o repositório**

```bash
git clone https://github.com/seu-usuario/global-crisis-assistant.git
cd global-crisis-assistant
```

**2. Crie e ative o ambiente virtual**

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

**4. Configure as variáveis de ambiente**

```bash
# Copie o arquivo de exemplo
cp .env.example .env
```

Abra o arquivo `.env` e preencha com suas credenciais:

```env
DATABASE_URL="postgresql://usuario:senha@host/nome_banco?sslmode=require"
GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**5. (Opcional) Popule o banco de dados**

Se você ainda não tiver os dados no banco, execute o pipeline ETL:

```bash
python etl_postgres.py
```

**6. Suba o servidor**

```bash
uvicorn main:app --reload
```

Acesse em: **http://127.0.0.1:8000** 🎉

---

## 📁 Estrutura do Projeto

```
global-crisis-assistant/
│
├── main.py               # Servidor FastAPI principal + endpoints
├── api.py                # Versão standalone da API (legado)
├── etl_postgres.py       # Pipeline ETL: coleta e carga no PostgreSQL
├── text_to_sql.py        # Módulo de lógica Text-to-SQL
├── requirements.txt      # Dependências Python
├── .env.example          # Modelo de variáveis de ambiente
│
└── static/               # Front-end SaaS (servido pelo FastAPI)
    ├── index.html        # Estrutura HTML (Bento Box UI)
    ├── style.css         # Design system completo
    └── script.js         # Lógica de interação e fetch API
```

---

## 🛠️ Stack Técnica

| Camada | Tecnologia | Função |
|---|---|---|
| **LLM** | Groq — Llama 3.3 70B | Tradução de linguagem natural para SQL |
| **Orquestração** | LangChain SQL Agent | Execução autônoma de queries com feedback |
| **Back-end** | FastAPI + Uvicorn | API REST assíncrona com `lru_cache` |
| **Banco de Dados** | PostgreSQL (Neon) | Star Schema com dados históricos reais |
| **Front-end** | HTML + Vanilla JS | SaaS UI com Chart.js e Marked.js |
| **ETL** | Pandas + SQLAlchemy | Coleta, limpeza e carga de dados |

---

## 💡 Exemplos de Perguntas

```
📌 "Qual foi a variação do Petróleo Brent nos últimos 30 dias?"
📌 "O sentimento das notícias afetou o preço do Diesel?"
📌 "Qual a correlação entre o S&P 500 e o Frete Marítimo?"
📌 "Qual foi a média do Dólar durante o período de maior tensão?"
📌 "Quando o Brent atingiu seu pico máximo e qual era o sentimento naquele dia?"
```

---

## ⚠️ Segurança

- **Nunca** comite o arquivo `.env` — ele está no `.gitignore`.
- O agente de IA é configurado para executar **apenas operações de leitura (SELECT)**. Operações DML (INSERT, UPDATE, DELETE) são explicitamente proibidas no system prompt.
- Use variáveis de ambiente para **todas** as credenciais.

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

<p align="center">Feito com ☕ e muito SQL | <strong>Global Crisis Data Assistant</strong></p>
