import os
import sys
import warnings
from dotenv import load_dotenv

# Força o terminal do Windows a aceitar Emojis em UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Ignorar alguns warnings internos do LangChain/SQLAlchemy
warnings.filterwarnings("ignore")

from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import create_sql_agent

def main():
    load_dotenv()

    # 1. Configurar Banco de Dados
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Erro: Variável DATABASE_URL não encontrada no .env.")
        sys.exit(1)
        
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # 2. Configurar Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ Erro: Variável GROQ_API_KEY não encontrada no .env.")
        sys.exit(1)

    print("🔌 Conectando ao banco de dados...")
    db = SQLDatabase.from_uri(db_url)
    
    print("🧠 Inicializando IA (Groq Llama 3.3)...")
    # Utilizamos temperature=0 para que a IA seja determinística e objetiva nas queries
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    # 3. Engenharia de Prompt (System Prompt)
    # Isso é fundamental para ensinar a IA sobre o nosso Star Schema
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

    # 4. Criar o Agente Text-to-SQL
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="tool-calling",
        verbose=True,  # verbose=True mostra o raciocínio e o SQL gerado no terminal
        prefix=custom_prefix
    )

    print("\n" + "="*60)
    print("🤖 Motor Conversacional Text-to-SQL Inicializado!")
    print("Dica: Faça perguntas sobre petróleo, S&P 500, sentimentos, etc.")
    print("Digite 'sair' para encerrar.")
    print("="*60)

    # 5. Loop Conversacional
    while True:
        try:
            pergunta = input("\n👤 Sua Pergunta: ")
            if pergunta.lower() in ["sair", "exit", "quit"]:
                print("Até logo!")
                break
            if not pergunta.strip():
                continue
                
            print("\n⚙️  A IA está criando o SQL e consultando o banco de dados...")
            
            # Invocar o agente
            resposta = agent_executor.invoke({"input": pergunta})
            
            print("\n" + "-"*60)
            print("🤖 Resposta Final:")
            print(resposta['output'])
            print("-"*60)
            
        except KeyboardInterrupt:
            print("\nAté logo!")
            break
        except Exception as e:
            print(f"\n❌ Ocorreu um erro: {e}")

if __name__ == "__main__":
    main()
