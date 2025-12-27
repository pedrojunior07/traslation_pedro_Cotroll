"""
Script de migração para adicionar a tabela translation_tokens ao banco de dados.

Execute este script para criar a tabela sem perder dados existentes:
    python migrate_add_translation_tokens.py
"""

from sqlalchemy import create_engine, text
from config import Settings

settings = Settings()


def create_translation_tokens_table():
    """Cria a tabela translation_tokens se ela não existir."""

    # Cria engine de conexão
    database_url = (
        f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    engine = create_engine(database_url)

    # SQL para criar a tabela
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS translation_tokens (
        id INT AUTO_INCREMENT PRIMARY KEY,
        translation_log_id INT NOT NULL,
        location VARCHAR(255) NOT NULL,
        original_text TEXT NOT NULL,
        translated_text TEXT NOT NULL,
        original_length INT NOT NULL,
        translated_length INT NOT NULL,
        was_truncated BOOLEAN DEFAULT FALSE,
        size_ratio FLOAT NOT NULL,
        units INT DEFAULT 1,
        warnings TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_translation_log_id (translation_log_id),
        FOREIGN KEY (translation_log_id) REFERENCES translation_logs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✓ Tabela 'translation_tokens' criada com sucesso!")
            print("  - Índice em 'translation_log_id' criado")
            print("  - Foreign key para 'translation_logs' criada")
    except Exception as e:
        print(f"✗ Erro ao criar tabela: {e}")
        return False

    return True


def verify_table():
    """Verifica se a tabela foi criada corretamente."""

    database_url = (
        f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = :db_name
                AND table_name = 'translation_tokens'
            """), {"db_name": settings.db_name})

            count = result.fetchone()[0]

            if count == 1:
                print("\n✓ Verificação: Tabela existe no banco de dados")

                # Verifica colunas
                result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = :db_name
                    AND table_name = 'translation_tokens'
                    ORDER BY ordinal_position
                """), {"db_name": settings.db_name})

                columns = [row[0] for row in result.fetchall()]
                print(f"  Colunas encontradas: {', '.join(columns)}")

                return True
            else:
                print("\n✗ Verificação: Tabela não encontrada!")
                return False

    except Exception as e:
        print(f"\n✗ Erro ao verificar tabela: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRAÇÃO: Adicionar tabela translation_tokens")
    print("=" * 60)
    print()

    print(f"Conectando ao banco de dados:")
    print(f"  Host: {settings.db_host}:{settings.db_port}")
    print(f"  Database: {settings.db_name}")
    print(f"  User: {settings.db_user}")
    print()

    # Cria a tabela
    if create_translation_tokens_table():
        # Verifica se foi criada corretamente
        if verify_table():
            print()
            print("=" * 60)
            print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            print()
            print("Próximos passos:")
            print("  1. Reinicie a API para carregar o novo modelo")
            print("  2. A tabela será populada automaticamente nas próximas traduções")
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
