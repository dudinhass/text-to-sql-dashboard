import os
import sys
import warnings
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import create_sql_agent

warnings.filterwarnings("ignore")

load_dotenv()

app = FastAPI(
    title="Text-to-SQL API",
    description="API que converte linguagem natural em queries PostgreSQL usando LangChain e Groq Llama 3.",
    version="1.0"
)

# Permitir CORS para o Frontend (qualquer origem na fase de dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variável global para armazenar o agente
agent_executor = None

@app.on_event("startup")
def startup_event():
    global agent_executor
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL não encontrada.")
        sys.exit(1)
        
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ GROQ_API_KEY não encontrada.")
        sys.exit(1)

    try:
        print("🔌 Conectando ao Banco de Dados para a API...")
        db = SQLDatabase.from_uri(db_url)
        
        print("🧠 Inicializando IA (Groq Llama 3.3)...")
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

        custom_prefix = """Você é um Engenheiro de Dados Sênior e Analista focado em PostgreSQL.
O banco de dados é modelado em formato Star Schema (Esquema Estrela) focado na Crise Global e Irã.

Regras IMPORTANTES:
1. A tabela central (dimensão) é a `dim_tempo`. Ela possui a chave primária `id_data` e informações como `data_completa`, `dia`, `mes`, `ano`.
2. As tabelas fato são: `fato_petroleo`, `fato_combustivel`, `fato_mercado_acoes`, `fato_frete_maritimo`, `fato_moedas`, `fato_sentimento_noticias`. 
3. TODAS as tabelas fato possuem a chave estrangeira `id_data` apontando para a `dim_tempo`.
4. Para relacionar qualquer métrica de uma tabela fato com datas, você DEVE SEMPRE fazer um JOIN com a tabela `dim_tempo` usando a coluna `id_data`. 
   Exemplo: `SELECT p.preco_brent, t.data_completa FROM fato_petroleo p JOIN dim_tempo t ON p.id_data = t.id_data`
5. Antes de executar qualquer query, verifique o schema correto com a tool de sql_db_schema.
6. Nunca faça DML (INSERT, UPDATE, DELETE, DROP). Você só tem permissão de leitura (SELECT).
7. Sempre formule sua resposta final de forma analítica, em Português do Brasil, trazendo os dados formatados e explicando brevemente o resultado.
"""

        # IMPORTANTE: return_intermediate_steps=True nos permite capturar a Query SQL gerada!
        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="tool-calling",
            verbose=True,
            prefix=custom_prefix,
            return_intermediate_steps=True
        )
        print("✅ API Text-to-SQL iniciada com sucesso!")
    except Exception as e:
        print(f"❌ Erro na inicialização da API: {e}")
        sys.exit(1)


class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_database(request: QueryRequest):
    """
    Recebe uma pergunta em português, converte para SQL usando IA, 
    executa no banco de dados e retorna a resposta + o SQL utilizado.
    """
    if not agent_executor:
        raise HTTPException(status_code=500, detail="Agente de IA não está inicializado.")
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="A pergunta não pode ser vazia.")
        
    try:
        # Invoca a IA pedindo para retornar também os passos intermediários
        response = agent_executor.invoke({"input": request.question})
        
        final_answer = response.get('output', "Não foi possível gerar uma resposta clara.")
        intermediate_steps = response.get('intermediate_steps', [])
        
        # O LangChain armazena o histórico do que as tools fizeram em intermediate_steps.
        # Vamos varrer os passos e tentar encontrar a execução do SQL.
        sql_query = None
        for step in intermediate_steps:
            action, result = step
            # action é um objeto AgentAction que guarda o nome da tool invocada
            if action.tool == "sql_db_query":
                # O input enviado para a tool de sql_db_query é a própria query SQL gerada!
                if isinstance(action.tool_input, dict) and 'query' in action.tool_input:
                    sql_query = action.tool_input['query']
                else:
                    sql_query = str(action.tool_input)
                break
                
        return {
            "answer": final_answer,
            "sql_query": sql_query if sql_query else "Query SQL não encontrada/necessária."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "A API Text-to-SQL está online!"}
