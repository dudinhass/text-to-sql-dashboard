import os
import sys
import warnings
import asyncio
from functools import lru_cache
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import create_sql_agent

warnings.filterwarnings("ignore")
load_dotenv()

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

app = FastAPI(title="Global Crisis Data Assistant - Web API")

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global agent variable
agent_executor = None

@lru_cache(maxsize=128)
def run_agent_query(query_text: str):
    if not agent_executor:
        raise Exception("IA não inicializada.")
    return agent_executor.invoke({"input": query_text})

@app.on_event("startup")
def startup_event():
    global agent_executor
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL não encontrada.")
        return
        
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ GROQ_API_KEY não encontrada.")
        return

    try:
        print("🔌 Conectando ao Banco de Dados...")
        db = SQLDatabase.from_uri(db_url)
        
        print("🧠 Inicializando IA (Groq Llama 3.3)...")
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

        custom_prefix = """Você é um Analista de Dados Sênior especializado em macroeconomia e geopolítica.
O banco de dados é modelado em Star Schema, focado na Crise Global e Irã.

## Regras do Banco:
1. Tabela dimensão: `dim_tempo` (chave: `id_data`, campos: `data_completa`, `dia`, `mes`, `ano`).
2. Tabelas fato: `fato_petroleo`, `fato_combustivel`, `fato_mercado_acoes`, `fato_frete_maritimo`, `fato_moedas`, `fato_sentimento_noticias`.
3. TODAS as tabelas fato possuem FK `id_data` → `dim_tempo`.
4. SEMPRE faça JOIN com `dim_tempo` via `id_data` para dados temporais.
5. Verifique o schema com sql_db_schema antes de montar queries.
6. Apenas SELECT. Nunca DML.

## Regras da Resposta:
1. Responda em Português do Brasil.
2. NUNCA mostre ou mencione a query SQL na resposta.
3. Foque TOTALMENTE na pergunta feita. Não desvie do tema central.
4. Estruture a resposta em 3 partes obrigatórias:
   **a) Resumo executivo (1-2 frases):** O dado principal respondendo a pergunta diretamente.
   **b) Detalhamento dos dados:** Apresente os valores relevantes usando listas ou tabela Markdown. Inclua período de referência, valores mín/máx, variação percentual quando aplicável.
   **c) Interpretação analítica (2-3 frases):** Contextualize o dado dentro do cenário macroeconômico/geopolítico. Aponte causas prováveis, correlações observadas ou implicações.
5. Formatação obrigatória:
   - **Negrito** para valores numéricos e métricas-chave.
   - Tabela Markdown quando houver comparação de múltiplas datas ou múltiplos indicadores.
   - Listas com marcadores (•) para enumeração de fatores.
6. Formate números de forma legível: R$ 5,32 | US$ 82.45 | +1,2% | -3,8%.
7. Não escreva frases genéricas como 'os dados mostram...' sem trazer o número concreto.
"""

        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="tool-calling",
            verbose=True,
            prefix=custom_prefix,
            return_intermediate_steps=True
        )
        print("✅ Backend pronto com IA real!")
    except Exception as e:
        print(f"❌ Erro na inicialização do agente: {e}")

class ChatRequest(BaseModel):
    query: str

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not agent_executor:
        raise HTTPException(status_code=500, detail="IA não inicializada. Verifique se o servidor iniciou corretamente.")
    
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="A pergunta não pode ser vazia.")
        
    try:
        print(f"\n[QUERY] '{query_text}'")
        # Executa o agente em thread separada com timeout de 120s para não bloquear o event loop
        response = await asyncio.wait_for(
            asyncio.to_thread(run_agent_query, query_text),
            timeout=120.0
        )
        
        final_answer = response.get('output', "Não foi possível gerar uma resposta clara.")
        intermediate_steps = response.get('intermediate_steps', [])
        
        sql_query = None
        query_result_raw = None
        chart_data = None

        for step in intermediate_steps:
            action, result = step
            if action.tool == "sql_db_query":
                if isinstance(action.tool_input, dict) and 'query' in action.tool_input:
                    sql_query = action.tool_input['query']
                else:
                    sql_query = str(action.tool_input)
                query_result_raw = result
                break

        # Tenta montar chart_data a partir do resultado da query
        if query_result_raw and isinstance(query_result_raw, str):
            try:
                import ast
                rows = ast.literal_eval(query_result_raw)
                if isinstance(rows, list) and len(rows) >= 2:
                    labels = []
                    values = []
                    for row in rows:
                        if isinstance(row, (list, tuple)) and len(row) >= 2:
                            labels.append(str(row[0]))
                            val = row[1]
                            if val is not None:
                                values.append(float(val))
                            else:
                                values.append(None)
                    if len(values) >= 2 and any(v is not None for v in values):
                        chart_data = {
                            "labels": labels,
                            "datasets": [{
                                "label": query_text[:40],
                                "data": values,
                                "borderColor": "#7F56D9",
                                "backgroundColor": "rgba(127, 86, 217, 0.1)",
                                "borderWidth": 2,
                                "tension": 0.4,
                                "fill": True,
                                "pointBackgroundColor": "#7F56D9",
                                "pointBorderColor": "#fff",
                                "pointHoverBackgroundColor": "#fff",
                                "pointHoverBorderColor": "#7F56D9"
                            }]
                        }
            except Exception:
                chart_data = None
        
        result_payload = {
            "answer": final_answer,
            "sql": sql_query if sql_query else "Consulta direta não realizada.",
            "chart_data": chart_data
        }
        
        return result_payload
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="A consulta demorou demais (>120s). Tente reformular a pergunta de forma mais específica.")
    except Exception as e:
        print(f"[ERRO] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
