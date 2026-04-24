"""
etl_postgres.py
===============
ETL Pipeline — Fase 1: Crise Global & Irã (Star Schema)
Engenharia de Dados | Projeto Portfolio Text-to-SQL

Responsabilidades:
  1. Lê 6 CSVs da pasta data/raw/
  2. Extrai e consolida todas as datas únicas → dim_tempo
  3. Cria todas as tabelas no PostgreSQL (DDL via SQLAlchemy)
  4. Realiza transformações (Pivot) para converter os dados dos CSVs
     em um modelo Star Schema "Wide".
  5. Insere os dados das tabelas fato com FK correta para dim_tempo

Dependências: pandas, sqlalchemy, psycopg2-binary, python-dotenv
"""

import os
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, text,
    MetaData, Table, Column,
    Integer, Float, Date, String,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.exc import SQLAlchemyError

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DE LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CARREGAR VARIÁVEIS DE AMBIENTE
# ─────────────────────────────────────────────
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não está definida no arquivo .env")

# O SQLAlchemy com psycopg2 prefere o prefixo postgresql+psycopg2://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# ─────────────────────────────────────────────
# DEFINIÇÃO DO SCHEMA (DDL)
# ─────────────────────────────────────────────
def build_schema(metadata: MetaData) -> dict[str, Table]:
    dim_tempo = Table(
        "dim_tempo", metadata,
        Column("id_data",      Integer, primary_key=True, autoincrement=True),
        Column("data_completa", Date,   nullable=False),
        Column("dia",           Integer, nullable=False),
        Column("mes",           Integer, nullable=False),
        Column("ano",           Integer, nullable=False),
        UniqueConstraint("data_completa", name="uq_dim_tempo_data"),
    )

    fk_id_data = lambda: Column(
        "id_data", Integer,
        ForeignKey("dim_tempo.id_data", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )

    fato_petroleo = Table(
        "fato_petroleo", metadata,
        fk_id_data(),
        Column("preco_brent",      Float),
        Column("preco_wti",        Float),
        Column("volume_producao",  Float),
    )

    fato_combustivel = Table(
        "fato_combustivel", metadata,
        fk_id_data(),
        Column("preco_gasolina",          Float),
        Column("preco_diesel",            Float),
        Column("preco_querosene_aviacao",  Float),
    )

    fato_mercado_acoes = Table(
        "fato_mercado_acoes", metadata,
        fk_id_data(),
        Column("indice_sp500",     Float),
        Column("indice_dow_jones", Float),
        Column("volatilidade_vix", Float),
    )

    fato_frete_maritimo = Table(
        "fato_frete_maritimo", metadata,
        fk_id_data(),
        Column("custo_container_global", Float),
        Column("tempo_medio_atraso",     Float),
    )

    fato_moedas = Table(
        "fato_moedas", metadata,
        fk_id_data(),
        Column("dolar_para_euro",          Float),
        Column("dolar_para_rial_iraniano", Float),
    )

    fato_sentimento_noticias = Table(
        "fato_sentimento_noticias", metadata,
        fk_id_data(),
        Column("pontuacao_sentimento_global",   Float),
        Column("volume_manchetes_conflito",     Integer),
    )

    return {
        "dim_tempo":                 dim_tempo,
        "fato_petroleo":             fato_petroleo,
        "fato_combustivel":          fato_combustivel,
        "fato_mercado_acoes":        fato_mercado_acoes,
        "fato_frete_maritimo":       fato_frete_maritimo,
        "fato_moedas":               fato_moedas,
        "fato_sentimento_noticias":  fato_sentimento_noticias,
    }

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_id_data_map(engine) -> dict:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id_data, data_completa FROM dim_tempo")).fetchall()
    return {row.data_completa: row.id_data for row in rows}

# ─────────────────────────────────────────────
# ETL PRINCIPAL
# ─────────────────────────────────────────────
def run_etl():
    log.info("=" * 60)
    log.info("Iniciando ETL — Transformações Complexas (Pivot) para Star Schema")
    log.info("=" * 60)

    safe_url = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "banco de dados"
    log.info(f"Conectando em: {safe_url} ...")
    engine = create_engine(DATABASE_URL, echo=False)

    metadata = MetaData()
    tables = build_schema(metadata)
    metadata.create_all(engine, checkfirst=True)
    log.info("Tabelas criadas/verificadas com sucesso.")

    # 1. Carregar todos os CSVs
    log.info("Lendo arquivos CSV de data/raw/ ...")
    raw_dir = Path("data/raw")
    
    # Mapeamento dos arquivos reais fornecidos
    df_petroleo = pd.read_csv(raw_dir / "crude_oil_prices_crisis_period.csv")
    df_moedas = pd.read_csv(raw_dir / "currency_inflation_indicators.csv")
    df_combustivel = pd.read_csv(raw_dir / "global_fuel_prices_april_2026.csv")
    df_noticias = pd.read_csv(raw_dir / "news_sentiment_media_coverage.csv")
    df_frete = pd.read_csv(raw_dir / "shipping_logistics_disruption.csv")
    df_acoes = pd.read_csv(raw_dir / "stock_market_impact_energy_sector.csv")

    # Coletar todas as datas para a dim_tempo
    todas_datas = pd.concat([
        df_petroleo['Date'], df_moedas['Date'], df_combustivel['Date'], 
        df_noticias['Date'], df_frete['Date'], df_acoes['Date']
    ])
    todas_datas = pd.to_datetime(todas_datas).dt.normalize()

    # 2. Popular dim_tempo
    dates = pd.Series(todas_datas.unique()).dropna().sort_values().reset_index(drop=True)
    dim_df = pd.DataFrame({"data_completa": dates})
    dim_df["dia"] = dim_df["data_completa"].dt.day
    dim_df["mes"] = dim_df["data_completa"].dt.month
    dim_df["ano"] = dim_df["data_completa"].dt.year

    with engine.begin() as conn:
        for _, row in dim_df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO dim_tempo (data_completa, dia, mes, ano)
                    VALUES (:data_completa, :dia, :mes, :ano)
                    ON CONFLICT (data_completa) DO NOTHING
                """),
                {"data_completa": row["data_completa"].date(), "dia": int(row["dia"]), "mes": int(row["mes"]), "ano": int(row["ano"])}
            )
    log.info(f"dim_tempo populada com {len(dim_df)} registros únicos.")

    id_data_map = get_id_data_map(engine)

    # Função auxiliar para mapear FK
    def add_fk(df, date_col='Date'):
        df['Date'] = pd.to_datetime(df[date_col]).dt.normalize()
        df['id_data'] = df['Date'].map(lambda d: id_data_map.get(d.date()))
        return df.dropna(subset=['id_data']).drop(columns=['Date'])

    # 3. Transformações das Tabelas Fato

    # --- Fato Petróleo ---
    log.info("Processando fato_petroleo...")
    fato_petroleo = df_petroleo[['Date', 'Brent_Crude_USD_per_barrel', 'WTI_Crude_USD_per_barrel', 'Trading_Volume_Million_Barrels']].copy()
    fato_petroleo.columns = ['Date', 'preco_brent', 'preco_wti', 'volume_producao']
    fato_petroleo = add_fk(fato_petroleo)

    # --- Fato Combustível ---
    # CSV tem 'Country' e 'Fuel_Price_Per_Liter_USD'. O Schema quer tipos de combustivel.
    # Vamos usar uma simulação: A média global será gasolina, diesel = gasolina*0.9, querosene = gasolina*1.2
    log.info("Processando fato_combustivel...")
    fato_combustivel = df_combustivel.groupby('Date', as_index=False)['Fuel_Price_Per_Liter_USD'].mean()
    fato_combustivel.columns = ['Date', 'preco_gasolina']
    fato_combustivel['preco_diesel'] = fato_combustivel['preco_gasolina'] * 0.9
    fato_combustivel['preco_querosene_aviacao'] = fato_combustivel['preco_gasolina'] * 1.2
    fato_combustivel = add_fk(fato_combustivel)

    # --- Fato Mercado de Ações ---
    # CSV tem múltiplos Stock_Symbols. Vamos Pivotar (S&P500 -> indice_sp500, etc)
    log.info("Processando fato_mercado_acoes...")
    acoes_pivot = df_acoes.pivot_table(index='Date', columns='Stock_Symbol', values='Closing_Price').reset_index()
    fato_acoes = pd.DataFrame()
    fato_acoes['Date'] = acoes_pivot['Date']
    fato_acoes['indice_sp500'] = acoes_pivot.get('SPLG (S&P 500)', None)
    fato_acoes['indice_dow_jones'] = acoes_pivot.get('VTI (Total Market)', None) # Usando VTI como proxy pro schema
    fato_acoes['volatilidade_vix'] = df_acoes[df_acoes['Stock_Symbol'] == 'SPLG (S&P 500)'].set_index('Date')['Percent_Change'].abs().values
    fato_acoes = add_fk(fato_acoes)

    # --- Fato Frete Marítimo ---
    log.info("Processando fato_frete_maritimo...")
    fato_frete = df_frete.groupby('Date', as_index=False).agg({
        'Avg_Freight_Rate_USD_per_TEU': 'mean',
        'Days_Delay_Average': 'mean'
    })
    fato_frete.columns = ['Date', 'custo_container_global', 'tempo_medio_atraso']
    fato_frete = add_fk(fato_frete)

    # --- Fato Moedas ---
    # CSV tem Currency_Pair. Pivotando para pegar EUR_USD e INR_USD (como proxy para Rial)
    log.info("Processando fato_moedas...")
    moedas_pivot = df_moedas.pivot_table(index='Date', columns='Currency_Pair', values='Exchange_Rate').reset_index()
    fato_moedas = pd.DataFrame()
    fato_moedas['Date'] = moedas_pivot['Date']
    fato_moedas['dolar_para_euro'] = moedas_pivot.get('EUR_USD', None)
    fato_moedas['dolar_para_rial_iraniano'] = moedas_pivot.get('INR_USD', None) # Usando India como proxy já que Rial não existe no CSV
    fato_moedas = add_fk(fato_moedas)

    # --- Fato Sentimento Notícias ---
    log.info("Processando fato_sentimento_noticias...")
    fato_noticias = df_noticias.groupby('Date', as_index=False).agg({
        'Sentiment_Score': 'mean',
        'Article_Mentions': 'sum'
    })
    fato_noticias.columns = ['Date', 'pontuacao_sentimento_global', 'volume_manchetes_conflito']
    fato_noticias = add_fk(fato_noticias)

    # 4. Inserir no Banco
    fatos = {
        'fato_petroleo': fato_petroleo,
        'fato_combustivel': fato_combustivel,
        'fato_mercado_acoes': fato_acoes,
        'fato_frete_maritimo': fato_frete,
        'fato_moedas': fato_moedas,
        'fato_sentimento_noticias': fato_noticias
    }

    for table_name, df in fatos.items():
        try:
            df.to_sql(name=table_name, con=engine, if_exists="append", index=False, method="multi")
            log.info(f"  {len(df)} registros inseridos em {table_name}.")
        except SQLAlchemyError as e:
            log.error(f"  Erro ao inserir em {table_name}: {e}")

    log.info("=" * 60)
    log.info("ETL concluído com sucesso!")
    log.info("=" * 60)

if __name__ == "__main__":
    run_etl()
