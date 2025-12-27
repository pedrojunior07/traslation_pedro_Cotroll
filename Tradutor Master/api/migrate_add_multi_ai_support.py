"""
Script de migração para adicionar suporte a múltiplos provedores de IA.

Execute este script para adicionar as novas colunas à tabela ai_config:
    python api/migrate_add_multi_ai_support.py
"""

import sys
import os

# Adiciona o diretório pai ao path para permitir imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Tenta importar de diferentes locais
try:
    from api.config import Settings
except ImportError:
    from config import Settings

settings = Settings()


def add_multi_ai_columns():
    """Adiciona colunas para suportar Gemini e Grok."""

    # Encode password to handle special characters
    encoded_password = quote_plus(settings.db_password)

    database_url = (
        f"mysql+pymysql://{settings.db_user}:{encoded_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    engine = create_engine(database_url)

    # Lista de colunas a adicionar: (nome, tipo, default, posição, has_default)
    columns_to_add = [
        ("provider", "VARCHAR(32)", "'openai'", "enabled", True),
        ("gemini_api_key", "TEXT", None, "api_key", False),
        ("gemini_model", "VARCHAR(128)", "'gemini-1.5-flash'", "gemini_api_key", True),
        ("grok_api_key", "TEXT", None, "gemini_model", False),
        ("grok_model", "VARCHAR(128)", "'grok-2-latest'", "grok_api_key", True),
        ("timeout", "FLOAT", "30.0", "grok_model", True),
        ("max_retries", "INT", "3", "timeout", True),
    ]

    try:
        with engine.connect() as conn:
            # Verifica quais colunas já existem
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :db_name
                AND table_name = 'ai_config'
            """), {"db_name": settings.db_name})

            existing_columns = {row[0] for row in result.fetchall()}

            # Adiciona apenas colunas que não existem
            for col_name, col_type, default_val, after_col, has_default in columns_to_add:
                if col_name in existing_columns:
                    print(f"  ⏭️  Coluna '{col_name}' já existe, pulando...")
                else:
                    # TEXT columns cannot have DEFAULT values in MySQL
                    if has_default and default_val is not None:
                        sql = f"ALTER TABLE ai_config ADD COLUMN {col_name} {col_type} DEFAULT {default_val} AFTER {after_col}"
                    else:
                        sql = f"ALTER TABLE ai_config ADD COLUMN {col_name} {col_type} AFTER {after_col}"

                    try:
                        conn.execute(text(sql))
                        print(f"✓ Coluna '{col_name}' adicionada")
                    except Exception as e:
                        print(f"✗ Erro ao adicionar '{col_name}': {e}")
                        return False

            conn.commit()
            print("\n✓ Migração concluída com sucesso!")
    except Exception as e:
        print(f"✗ Erro ao executar migração: {e}")
        return False

    return True


def verify_columns():
    """Verifica se as colunas foram criadas."""

    # Encode password to handle special characters
    encoded_password = quote_plus(settings.db_password)

    database_url = (
        f"mysql+pymysql://{settings.db_user}:{encoded_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :db_name
                AND table_name = 'ai_config'
                ORDER BY ordinal_position
            """), {"db_name": settings.db_name})

            columns = [row[0] for row in result.fetchall()]
            print("\n✓ Colunas na tabela ai_config:")
            for col in columns:
                print(f"  - {col}")

            expected = ['provider', 'gemini_api_key', 'gemini_model', 'grok_api_key', 'grok_model', 'timeout', 'max_retries']
            missing = [col for col in expected if col not in columns]

            if missing:
                print(f"\n⚠️  Colunas faltando: {', '.join(missing)}")
                return False

            print("\n✓ Todas as colunas esperadas estão presentes!")
            return True

    except Exception as e:
        print(f"\n✗ Erro ao verificar colunas: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRAÇÃO: Adicionar Suporte a Múltiplos Provedores de IA")
    print("=" * 60)
    print()

    print(f"Conectando ao banco de dados:")
    print(f"  Host: {settings.db_host}:{settings.db_port}")
    print(f"  Database: {settings.db_name}")
    print(f"  User: {settings.db_user}")
    print()

    if add_multi_ai_columns():
        if verify_columns():
            print()
            print("=" * 60)
            print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            print()
            print("Provedores suportados:")
            print("  - OpenAI (GPT-4, GPT-3.5, etc)")
            print("  - Google Gemini (Gemini 1.5 Flash/Pro)")
            print("  - xAI Grok (Grok 2)")
            print()
        else:
            print()
            print("=" * 60)
            print("MIGRAÇÃO FALHOU NA VERIFICAÇÃO")
            print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("MIGRAÇÃO FALHOU")
        print("=" * 60)
