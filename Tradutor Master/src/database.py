# -*- coding: utf-8 -*-
"""
Conexão direta ao MySQL para o desktop app.
Permite acesso ao dicionário e logs sem passar pelo backend API.
"""
import mysql.connector
from mysql.connector import pooling, Error
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from config_manager import ConfigManager


class Database:
    """Conexão direta ao MySQL (sem API intermediária)"""

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Inicializa conexão com MySQL.

        Args:
            config: ConfigManager com credenciais. Se None, cria novo.
        """
        if config is None:
            config = ConfigManager()

        self.config = config

        # Criar pool de conexões
        try:
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="tradutor_pool",
                pool_size=5,
                pool_reset_session=True,
                host=config.get("mysql_host"),
                port=config.get("mysql_port"),
                user=config.get("mysql_user"),
                password=config.get("mysql_password"),
                database=config.get("mysql_database"),
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci"
            )
        except Error as e:
            raise Exception(f"Erro ao criar pool de conexões MySQL: {e}")

    def get_connection(self):
        """Obtém conexão do pool."""
        return self.pool.get_connection()

    def test_connection(self) -> bool:
        """
        Testa conexão com MySQL.

        Returns:
            True se conexão bem-sucedida, False caso contrário
        """
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except:
            return False

    # ========== DICIONÁRIO ==========

    def get_dictionary(self, source: str, target: str) -> Dict[str, str]:
        """
        Busca dicionário de termos para par de idiomas.

        Args:
            source: Código do idioma origem (en, pt, etc)
            target: Código do idioma destino

        Returns:
            Dicionário {termo: tradução}
        """
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            query = """
            SELECT term, translation FROM token_dictionary
            WHERE source_lang = %s AND target_lang = %s AND is_active = 1
            ORDER BY usage_count DESC
            """
            cursor.execute(query, (source, target))
            results = cursor.fetchall()

            return {row["term"]: row["translation"] for row in results}
        finally:
            cursor.close()
            conn.close()

    def search_dictionary(
        self,
        term: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        target: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca termos no dicionário com filtros.

        Args:
            term: Buscar por termo específico (parcial)
            category: Filtrar por categoria
            source: Filtrar por idioma origem
            target: Filtrar por idioma destino

        Returns:
            Lista de dicionários com dados dos termos
        """
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            query = "SELECT * FROM token_dictionary WHERE 1=1"
            params = []

            if term:
                query += " AND term LIKE %s"
                params.append(f"%{term}%")
            if category:
                query += " AND category = %s"
                params.append(category)
            if source:
                query += " AND source_lang = %s"
                params.append(source)
            if target:
                query += " AND target_lang = %s"
                params.append(target)

            query += " ORDER BY usage_count DESC, term ASC LIMIT 1000"

            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def add_dictionary_term(
        self,
        term: str,
        translation: str,
        source: str,
        target: str,
        category: Optional[str] = None
    ) -> bool:
        """
        Adiciona termo ao dicionário.

        Args:
            term: Termo original
            translation: Tradução
            source: Idioma origem
            target: Idioma destino
            category: Categoria opcional

        Returns:
            True se adicionado com sucesso
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            query = """
            INSERT INTO token_dictionary
            (term, translation, source_lang, target_lang, category, is_active, usage_count)
            VALUES (%s, %s, %s, %s, %s, 1, 0)
            ON DUPLICATE KEY UPDATE
            translation = VALUES(translation),
            category = VALUES(category),
            is_active = 1
            """
            cursor.execute(query, (term, translation, source, target, category))
            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao adicionar termo: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def update_dictionary_term(self, term_id: int, **updates) -> bool:
        """
        Atualiza termo do dicionário.

        Args:
            term_id: ID do termo
            **updates: Campos a atualizar (translation, category, is_active, etc)

        Returns:
            True se atualizado com sucesso
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            query = f"UPDATE token_dictionary SET {set_clause} WHERE id = %s"
            params = list(updates.values()) + [term_id]

            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def delete_dictionary_term(self, term_id: int) -> bool:
        """
        Remove termo do dicionário.

        Args:
            term_id: ID do termo

        Returns:
            True se removido com sucesso
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM token_dictionary WHERE id = %s", (term_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def increment_term_usage(self, term: str, source: str, target: str):
        """
        Incrementa contador de uso de um termo.

        Args:
            term: Termo usado
            source: Idioma origem
            target: Idioma destino
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            query = """
            UPDATE token_dictionary
            SET usage_count = usage_count + 1
            WHERE term = %s AND source_lang = %s AND target_lang = %s
            """
            cursor.execute(query, (term, source, target))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    # ========== LOGS DE USO DE TOKENS ==========

    def log_token_usage(
        self,
        device_id: int,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        model: str,
        provider: str = "claude",
        cache_creation: int = 0,
        cache_read: int = 0
    ) -> bool:
        """
        Registra uso de tokens.

        Args:
            device_id: ID do dispositivo
            input_tokens: Tokens de entrada
            output_tokens: Tokens de saída
            cost: Custo em USD
            model: Modelo usado
            provider: Provedor (claude, openai, etc)
            cache_creation: Tokens de criação de cache
            cache_read: Tokens de leitura de cache

        Returns:
            True se registrado com sucesso
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            today = date.today()

            # Verificar se já existe registro para hoje
            cursor.execute(
                "SELECT id FROM token_usage_log WHERE device_id = %s AND date = %s",
                (device_id, today)
            )
            existing = cursor.fetchone()

            if existing:
                # Atualizar registro existente
                query = """
                UPDATE token_usage_log
                SET input_tokens = input_tokens + %s,
                    output_tokens = output_tokens + %s,
                    cache_creation_tokens = cache_creation_tokens + %s,
                    cache_read_tokens = cache_read_tokens + %s,
                    total_cost = total_cost + %s,
                    api_calls = api_calls + 1,
                    model_used = %s,
                    provider = %s
                WHERE id = %s
                """
                cursor.execute(query, (
                    input_tokens, output_tokens, cache_creation, cache_read,
                    cost, model, provider, existing[0]
                ))
            else:
                # Inserir novo registro
                query = """
                INSERT INTO token_usage_log
                (device_id, date, input_tokens, output_tokens,
                 cache_creation_tokens, cache_read_tokens,
                 total_cost, api_calls, model_used, provider)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s)
                """
                cursor.execute(query, (
                    device_id, today, input_tokens, output_tokens,
                    cache_creation, cache_read, cost, model, provider
                ))

            conn.commit()
            return True
        except Error as e:
            print(f"Erro ao registrar uso de tokens: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_token_usage(
        self,
        device_id: int,
        days: int = 30
    ) -> Tuple[Dict, List[Dict]]:
        """
        Obtém estatísticas de uso de tokens.

        Args:
            device_id: ID do dispositivo
            days: Número de dias para buscar

        Returns:
            Tuple (resumo, detalhes_diários)
            - resumo: {total_input, total_output, total_cost, etc}
            - detalhes_diários: Lista de dicts com uso por dia
        """
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            since = date.today() - timedelta(days=days)

            # Buscar dados
            query = """
            SELECT * FROM token_usage_log
            WHERE device_id = %s AND date >= %s
            ORDER BY date DESC
            """
            cursor.execute(query, (device_id, since))
            daily_data = cursor.fetchall()

            # Calcular resumo
            total_input = sum(row["input_tokens"] for row in daily_data)
            total_output = sum(row["output_tokens"] for row in daily_data)
            total_cache_creation = sum(row.get("cache_creation_tokens", 0) for row in daily_data)
            total_cache_read = sum(row.get("cache_read_tokens", 0) for row in daily_data)
            total_cost = sum(row["total_cost"] for row in daily_data)
            total_calls = sum(row["api_calls"] for row in daily_data)

            summary = {
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_cache_creation_tokens": total_cache_creation,
                "total_cache_read_tokens": total_cache_read,
                "total_cost": total_cost,
                "total_calls": total_calls,
                "days_analyzed": days,
            }

            # Converter dates para strings
            for row in daily_data:
                if isinstance(row["date"], date):
                    row["date"] = row["date"].isoformat()

            return summary, daily_data
        finally:
            cursor.close()
            conn.close()

    def close(self) -> None:
        """Fecha o pool de conexões."""
        # Connection pool não precisa de close explícito,
        # mas este método existe para compatibilidade
        pass


if __name__ == "__main__":
    # Teste simples
    print("Testando Database...")

    try:
        db = Database()

        # Testar conexão
        if db.test_connection():
            print("✓ Conexão com MySQL bem-sucedida")

            # Testar busca de dicionário
            dictionary = db.get_dictionary("en", "pt")
            print(f"✓ Dicionário EN→PT: {len(dictionary)} termos")
            if dictionary:
                print(f"  Exemplo: {list(dictionary.items())[0]}")

            # Testar busca com filtros
            results = db.search_dictionary(category="empresa_petroleo")
            print(f"✓ Busca por categoria: {len(results)} resultados")

        else:
            print("✗ Falha ao conectar com MySQL")
    except Exception as e:
        print(f"✗ Erro: {e}")
