# -*- coding: utf-8 -*-
"""
Script para importar glossário completo CCS JV EN→PT (Moçambique)
Inclui todos os termos, abreviações e expressões técnicas.
"""
import mysql.connector
from mysql.connector import Error
from typing import List, Tuple

# Glossário completo EN→PT (Moçambique) - CCS JV
GLOSSARY_ENTRIES = [
    # Termos principais
    ("Purchaser", "Contratante", "en", "pt", "termo_contratual"),
    ("Supplier", "Fornecedor", "en", "pt", "termo_contratual"),
    ("Subcontractor", "Subcontratado", "en", "pt", "termo_contratual"),
    ("Contractor", "Contratante", "en", "pt", "termo_contratual"),
    ("Client", "Cliente", "en", "pt", "termo_contratual"),
    ("Vendor", "Fornecedor", "en", "pt", "termo_contratual"),
    ("Lower Tier Subcontractor", "Subcontratado de Nível Inferior", "en", "pt", "termo_contratual"),

    # Termos operacionais
    ("Goods", "Bens", "en", "pt", "termo_operacional"),
    ("Supply", "Fornecimento", "en", "pt", "termo_operacional"),
    ("Scope of Work", "Âmbito do Trabalho", "en", "pt", "termo_operacional"),
    ("Liquidated Damages", "Multa Contratual", "en", "pt", "termo_contratual"),
    ("Force Majeure", "Caso Fortuito", "en", "pt", "termo_contratual"),
    ("Warranty", "Garantia", "en", "pt", "termo_contratual"),
    ("Invoicing", "Faturação", "en", "pt", "termo_financeiro"),
    ("Advance Payment Bond", "Garantia de Adiantamento", "en", "pt", "termo_financeiro"),
    ("VAT Regularization Note", "Nota de Regularização do IVA", "en", "pt", "termo_financeiro"),

    # Termos técnicos/legais
    ("Dual Use items", "Itens de Uso Duplo", "en", "pt", "termo_tecnico"),
    ("Conflict Minerals", "Minerais de Conflito", "en", "pt", "termo_tecnico"),
    ("Applicable Law", "Legislação Aplicável", "en", "pt", "termo_legal"),
    ("Governmental Instrumentality", "Entidade Governamental", "en", "pt", "termo_legal"),
    ("Hazardous Materials", "Materiais Perigosos", "en", "pt", "termo_tecnico"),

    # Locais
    ("Site", "Obra", "en", "pt", "local"),
    ("Afungi Site", "Obra de Afungi", "en", "pt", "local"),
    ("Delivery Point", "Local de Entrega", "en", "pt", "local"),

    # Siglas e abreviações - mantidas iguais
    ("NUIT", "NUIT", "en", "pt", "sigla"),
    ("TAX ID", "NUIT", "en", "pt", "sigla"),
    ("IDENTIFICAÇÃO FISCAL", "NUIT", "pt", "pt", "sigla"),  # Corrigir português mal traduzido
    ("QID FISCAL", "NUIT", "pt", "pt", "sigla"),  # Corrigir erro comum
    ("Tel. No.", "Tel.", "en", "pt", "abreviacao"),
    ("Tel. Não.", "Tel.", "pt", "pt", "abreviacao"),  # Corrigir português mal traduzido
    ("Nr Tel", "Tel.", "pt", "pt", "abreviacao"),  # Variação
    ("E-mail address", "E-mail", "en", "pt", "abreviacao"),
    ("Endereço de correio electrónico", "E-mail", "pt", "pt", "abreviacao"),  # Corrigir português mal traduzido
    ("Endereço de e-mail", "E-mail", "pt", "pt", "abreviacao"),  # Variação
    ("Our reference", "Nossa referência", "en", "pt", "abreviacao"),
    ("Subject", "Assunto", "en", "pt", "abreviacao"),
    ("Job", "Projeto", "en", "pt", "termo_operacional"),
    ("Requesting Center", "Centro Requisitante", "en", "pt", "termo_operacional"),
    ("Proc. Dept.", "Dept. de Aquisições", "en", "pt", "abreviacao"),
    ("Procurem.Office", "Escritório de Aquisições", "en", "pt", "abreviacao"),
    ("Buyer", "Comprador", "en", "pt", "termo_operacional"),
    ("For internal use", "Para uso interno", "en", "pt", "termo_geral"),
    ("PR Ref.", "Ref. RP", "en", "pt", "abreviacao"),
    ("Vendor code", "Código do Fornecedor", "en", "pt", "termo_operacional"),

    # Moeda
    ("MZN", "MZN", "en", "pt", "moeda"),
    ("DDP", "DDP", "en", "pt", "sigla"),

    # Documentos
    ("Purchase Order (PO)", "Ordem de Compra", "en", "pt", "documento"),
    ("Purchase Order", "Ordem de Compra", "en", "pt", "documento"),
    ("Work Order (WO)", "Ordem de Serviço", "en", "pt", "documento"),
    ("Work Order", "Ordem de Serviço", "en", "pt", "documento"),
    ("General Terms and Conditions (GTC)", "Condições Gerais", "en", "pt", "documento"),
    ("General Terms and Conditions", "Condições Gerais", "en", "pt", "documento"),
    ("Letter of Acceptance", "Carta de Aceitação", "en", "pt", "documento"),
    ("Attachment", "Anexo", "en", "pt", "documento"),

    # Siglas importantes
    ("Health, Safety, Environment (HSE)", "Saúde, Segurança e Ambiente", "en", "pt", "sigla"),
    ("HSE", "SSA", "en", "pt", "sigla"),
    ("Value Added Tax (VAT)", "IVA", "en", "pt", "sigla"),
    ("VAT", "IVA", "en", "pt", "sigla"),
    ("London Court of International Arbitration (LCIA)", "LCIA", "en", "pt", "sigla"),
    ("LCIA", "LCIA", "en", "pt", "sigla"),
    ("Exploration and Production Concession Contract (EPCC)", "Contrato de Concessão de Exploração e Produção", "en", "pt", "sigla"),
    ("EPCC", "CCEP", "en", "pt", "sigla"),
    ("Organization for Economic Co-operation and Development (OECD)", "OCDE", "en", "pt", "sigla"),
    ("OECD", "OCDE", "en", "pt", "sigla"),
    ("Foreign Corrupt Practices Act (FCPA)", "FCPA", "en", "pt", "sigla"),
    ("FCPA", "FCPA", "en", "pt", "sigla"),
    ("Federal Aviation Administration (FFA)", "FFA", "en", "pt", "sigla"),
    ("FFA", "FFA", "en", "pt", "sigla"),

    # Empresas e locais
    ("CCS JV", "CCS JV", "en", "pt", "empresa"),
    ("TOTAL ENERGIES EP Mozambique Area 1, Limitada", "TOTAL ENERGIES EP Moçambique Área 1, Limitada", "en", "pt", "empresa"),
    ("Kerry Project Logistics (Mozambique) lda", "Kerry Project Logistics (Moçambique) Lda", "en", "pt", "empresa"),
    ("Pemba", "Pemba", "en", "pt", "local"),
    ("Maputo", "Maputo", "en", "pt", "local"),

    # Expressões legais/contratuais comuns
    ("shall be", "deverá ser", "en", "pt", "expressao_legal"),
    ("in accordance with", "em conformidade com", "en", "pt", "expressao_legal"),
    ("unless otherwise provided", "salvo disposição em contrário", "en", "pt", "expressao_legal"),
    ("subject to", "sujeito a", "en", "pt", "expressao_legal"),
    ("duly signed", "devidamente assinado", "en", "pt", "expressao_legal"),
    ("binding on both Parties", "vinculante para ambas as Partes", "en", "pt", "expressao_legal"),
    ("supersedes any previous agreement", "substitui qualquer acordo anterior", "en", "pt", "expressao_legal"),

    # Unidades de medida
    ("UM (Unit of Measure)", "UM (Unidade de Medida)", "en", "pt", "unidade"),
    ("Unit of Measure", "Unidade de Medida", "en", "pt", "unidade"),
    ("UM", "UM", "en", "pt", "unidade"),
    ("NR (Number)", "NR (Número)", "en", "pt", "unidade"),
    ("LS (Lump Sum)", "LS (Valor Global)", "en", "pt", "unidade"),
    ("BX (Box)", "CX (Caixa)", "en", "pt", "unidade"),
    ("DRM (Drum)", "TMB (Tambor)", "en", "pt", "unidade"),
    ("KT (Kit)", "KT (Kit)", "en", "pt", "unidade"),

    # Datas e valores
    ("Effective Date", "Data de Efeito", "en", "pt", "termo_geral"),
    ("Expiry Date", "Data de Expiração", "en", "pt", "termo_geral"),
    ("Maximum Amount", "Valor Máximo", "en", "pt", "termo_financeiro"),
    ("Base Amount", "Valor Base", "en", "pt", "termo_financeiro"),
    ("Scheduled Commencement Date", "Data de Início Agendada", "en", "pt", "termo_geral"),
    ("Scheduled Completion Date", "Data de Conclusão Agendada", "en", "pt", "termo_geral"),

    # Campos comuns em documentos
    ("Technical office", "Gabinete técnico", "en", "pt", "termo_operacional"),
    ("Escritório técnico", "Gabinete técnico", "pt", "pt", "termo_operacional"),  # Corrigir variação
    ("dated", "datado de", "en", "pt", "termo_geral"),
    ("de", "datado de", "pt", "pt", "termo_geral"),  # Contexto: "31637004 de 21.10.2024"
    ("Agreement No.", "Acordo n.º", "en", "pt", "termo_geral"),
    ("Acordo n.o", "Acordo n.º", "pt", "pt", "termo_geral"),  # Corrigir erro de formatação

    # Adicionais identificados no exemplo
    ("MOZAMBIQUE", "MOÇAMBIQUE", "en", "pt", "local"),
    ("Mozambique", "Moçambique", "en", "pt", "local"),
    ("TAX ID", "ID FISCAL", "en", "pt", "sigla"),
    ("BRANCH", "SUCURSAL", "en", "pt", "termo_geral"),

    # Termos de serviço
    ("PROVISION OF MEDICAL SERVICES", "PROVISÃO DOS SERVIÇOS MÉDICOS", "en", "pt", "termo_operacional"),
    ("OCCUPATIONAL HEALTH", "SAÚDE OCUPACIONAL", "en", "pt", "termo_operacional"),
    ("AMBULANCE SERVICES", "SERVIÇOS DE AMBULÂNCIA", "en", "pt", "termo_operacional"),

    # Termos de pagamento
    ("Payment", "Pagamento", "en", "pt", "termo_financeiro"),
    ("upon completion", "após a conclusão", "en", "pt", "expressao_legal"),
    ("calendar days", "dias de calendário", "en", "pt", "termo_geral"),
    ("receipt date", "data de recepção", "en", "pt", "termo_geral"),
    ("original invoice", "fatura original", "en", "pt", "termo_financeiro"),
    ("Service Acceptance Paper (SAP)", "Documento de Aceitação do Serviço", "en", "pt", "documento"),
    ("SAP", "DAC", "en", "pt", "sigla"),
    ("Authorized Representatives", "Representantes Autorizados", "en", "pt", "termo_legal"),
]


def import_glossary_to_db():
    """
    Importa glossário para o banco de dados MySQL.
    """
    print("🔌 Conectando ao banco de dados...")

    try:
        # Conectar ao MySQL (ajuste as credenciais conforme necessário)
        conn = mysql.connector.connect(
            host="102.211.186.44",
            port=3306,
            user="root",
            password="",  # Ajuste a senha
            database="tradutor_db",
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci"
        )

        cursor = conn.cursor()

        print(f"📚 Importando {len(GLOSSARY_ENTRIES)} termos do glossário CCS JV...")

        # Query de inserção/atualização
        query = """
        INSERT INTO token_dictionary
        (term, translation, source_lang, target_lang, category, is_active, usage_count)
        VALUES (%s, %s, %s, %s, %s, 1, 0)
        ON DUPLICATE KEY UPDATE
        translation = VALUES(translation),
        category = VALUES(category),
        is_active = 1
        """

        success_count = 0
        error_count = 0

        for term, translation, source, target, category in GLOSSARY_ENTRIES:
            try:
                cursor.execute(query, (term, translation, source, target, category))
                success_count += 1
            except Error as e:
                print(f"⚠ Erro ao importar '{term}': {e}")
                error_count += 1

        # Commit
        conn.commit()

        print(f"\n✅ Importação concluída!")
        print(f"   ✓ {success_count} termos importados/atualizados")
        if error_count > 0:
            print(f"   ⚠ {error_count} erros")

        # Mostrar estatísticas
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM token_dictionary
            WHERE source_lang = 'en' AND target_lang = 'pt'
            GROUP BY category
        """)

        print("\n📊 Estatísticas por categoria:")
        for row in cursor.fetchall():
            category, count = row
            print(f"   • {category}: {count} termos")

        cursor.close()
        conn.close()

    except Error as e:
        print(f"❌ Erro na conexão ao MySQL: {e}")
        print("\n💡 Dica: Verifique se:")
        print("   1. O MySQL está rodando")
        print("   2. As credenciais estão corretas")
        print("   3. O banco 'tradutor_db' existe")
        print("   4. A tabela 'token_dictionary' existe")


def export_to_csv():
    """
    Exporta glossário para CSV (alternativa ao banco de dados).
    """
    import csv

    filename = "glossario_ccs_jv_en_pt.csv"

    print(f"💾 Exportando glossário para {filename}...")

    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["Termo (EN)", "Tradução (PT)", "Idioma Origem", "Idioma Destino", "Categoria"])

        for term, translation, source, target, category in GLOSSARY_ENTRIES:
            writer.writerow([term, translation, source, target, category])

    print(f"✅ Glossário exportado: {filename}")
    print(f"   Total: {len(GLOSSARY_ENTRIES)} termos")


if __name__ == "__main__":
    import sys
    import io

    # Configurar encoding UTF-8 para Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 70)
    print("  IMPORTADOR DE GLOSSARIO CCS JV - EN->PT (Mocambique)")
    print("=" * 70)
    print()

    # Mostrar opções
    print("Escolha uma opção:")
    print("  1. Importar para banco de dados MySQL")
    print("  2. Exportar para CSV")
    print("  3. Ambos")
    print()

    choice = input("Opção [1-3]: ").strip()

    if choice == "1":
        import_glossary_to_db()
    elif choice == "2":
        export_to_csv()
    elif choice == "3":
        import_glossary_to_db()
        print()
        export_to_csv()
    else:
        print("❌ Opção inválida")
