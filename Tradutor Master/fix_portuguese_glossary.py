# -*- coding: utf-8 -*-
"""
Glossário de correção PT→PT
Corrige traduções mal feitas do LibreTranslate
"""
import mysql.connector
from mysql.connector import Error

# Glossário PT→PT para corrigir traduções ruins
PORTUGUESE_CORRECTIONS = [
    # Correções de campos comuns
    ("IDENTIFICAÇÃO FISCAL", "NUIT", "pt", "pt", "sigla"),
    ("QID FISCAL", "NUIT", "pt", "pt", "sigla"),
    ("Tel. Não.", "Tel.", "pt", "pt", "abreviacao"),
    ("Endereço de correio electrónico", "E-mail", "pt", "pt", "abreviacao"),
    ("Endereço de e-mail", "E-mail", "pt", "pt", "abreviacao"),

    # Números e quantidades
    ("Número de ordem de trabalho", "Ordem de Serviço n.º", "pt", "pt", "documento"),
    ("Número de ordem", "n.º", "pt", "pt", "abreviacao"),

    # Acordo
    ("Acordo n.o", "Acordo n.º", "pt", "pt", "termo_geral"),

    # Localidades
    ("Moçambico", "Moçambique", "pt", "pt", "local"),
    ("MOZAMBICO", "MOÇAMBIQUE", "pt", "pt", "local"),

    # Escritório/Gabinete
    ("Escritório técnico", "Gabinete técnico", "pt", "pt", "termo_operacional"),

    # GNL vs LNG
    ("GNL", "LNG", "pt", "pt", "sigla"),
    ("AMA1 GNL EPC", "AMA1 LNG EPC", "pt", "pt", "termo_tecnico"),

    # Montante/Valor
    ("Montante de base", "Valor Base", "pt", "pt", "termo_financeiro"),
    ("Montante máximo", "Valor Máximo", "pt", "pt", "termo_financeiro"),
    ("Montante", "Valor", "pt", "pt", "termo_financeiro"),

    # Fabricante/Fornecedor
    ("Fabricante", "Fornecedor", "pt", "pt", "termo_contratual"),

    # Centro
    ("Centro de Solicitação", "Centro Requisitante", "pt", "pt", "termo_operacional"),

    # Datas
    ("Data de início programada", "Data de Início Agendada", "pt", "pt", "termo_geral"),
    ("Data de Conclusão Agendada", "Data de Conclusão Agendada", "pt", "pt", "termo_geral"),

    # Envio/Submissão
    ("Endereço de e-mail para envio de PDF", "E-mail para envio de PDF", "pt", "pt", "termo_geral"),

    # Outros erros comuns
    ("de acordo com os termos e condições", "em conformidade com os termos e condições", "pt", "pt", "expressao_legal"),
    ("nós lhe damos", "atribuímos-lhe", "pt", "pt", "expressao_legal"),
    ("presente trabalho Ordem", "presente Ordem de Serviço", "pt", "pt", "termo_contratual"),
    ("disposições como detalhado abaixo", "prestações conforme detalhado abaixo", "pt", "pt", "expressao_legal"),
]


def import_corrections():
    """Importa correções PT→PT para o banco"""
    try:
        conn = mysql.connector.connect(
            host="102.211.186.44",
            port=3306,
            user="root",
            password="",
            database="tradutor_db",
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci"
        )

        cursor = conn.cursor()

        print(f"📚 Importando {len(PORTUGUESE_CORRECTIONS)} correções PT→PT...")

        query = """
        INSERT INTO token_dictionary
        (term, translation, source_lang, target_lang, category, is_active, usage_count)
        VALUES (%s, %s, %s, %s, %s, 1, 0)
        ON DUPLICATE KEY UPDATE
        translation = VALUES(translation),
        category = VALUES(category),
        is_active = 1
        """

        success = 0
        for term, translation, source, target, category in PORTUGUESE_CORRECTIONS:
            try:
                cursor.execute(query, (term, translation, source, target, category))
                success += 1
            except Error as e:
                print(f"⚠ Erro: {term} - {e}")

        conn.commit()

        print(f"\n✅ {success} correções importadas!")

        # Mostrar total PT→PT
        cursor.execute("""
            SELECT COUNT(*) FROM token_dictionary
            WHERE source_lang = 'pt' AND target_lang = 'pt'
        """)
        total = cursor.fetchone()[0]
        print(f"📊 Total de correções PT→PT no banco: {total}")

        cursor.close()
        conn.close()

    except Error as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    import sys
    import io

    # Configurar UTF-8 para Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("="*70)
    print("  IMPORTADOR DE CORREÇÕES PT→PT")
    print("="*70)
    print()

    import_corrections()
