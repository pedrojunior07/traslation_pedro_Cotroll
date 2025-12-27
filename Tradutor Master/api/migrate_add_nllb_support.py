"""
Migração: Adiciona suporte para NLLB-200 como provider alternativo de tradução.
"""
from sqlalchemy import create_engine, text
from api.config import Settings, build_db_url

settings = Settings()
db_url = build_db_url(settings)
engine = create_engine(db_url)

def migrate():
    with engine.begin() as conn:
        # Verifica se as colunas já existem
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'translate_config'
            AND COLUMN_NAME = 'provider'
        """))
        exists = result.fetchone()[0] > 0

        if exists:
            print("✓ Colunas NLLB já existem")
            return

        print("Adicionando colunas para suporte NLLB...")

        # Adiciona coluna provider
        conn.execute(text("""
            ALTER TABLE translate_config
            ADD COLUMN provider VARCHAR(32) DEFAULT 'libretranslate' AFTER id
        """))

        # Adiciona coluna nllb_base_url
        conn.execute(text("""
            ALTER TABLE translate_config
            ADD COLUMN nllb_base_url VARCHAR(255) DEFAULT 'http://102.211.186.111:8000' AFTER base_url
        """))

        print("✓ Migração concluída com sucesso!")

if __name__ == "__main__":
    migrate()
