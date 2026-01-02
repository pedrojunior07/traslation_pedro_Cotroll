# -*- coding: utf-8 -*-
"""
Script para importar glossário CCS JV EN → PT (Moçambique) no banco de dados.
"""
import sys
import os

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database

# Glossário CCS JV EN → PT (Moçambique)
GLOSSARY = {
    # Termos principais
    "Purchaser": "Contratante",
    "Supplier": "Fornecedor",
    "Subcontractor": "Subcontratado",
    "Contractor": "Contratante",
    "Client": "Cliente",
    "Vendor": "Fornecedor",
    "Lower Tier Subcontractor": "Subcontratado de Nível Inferior",
    "Goods": "Bens",
    "Supply": "Fornecimento",
    "Scope of Work": "Âmbito do Trabalho",
    "Liquidated Damages": "Multa Contratual",
    "Force Majeure": "Caso Fortuito",
    "Warranty": "Garantia",
    "Invoicing": "Faturação",
    "Advance Payment Bond": "Garantia de Adiantamento",
    "VAT Regularization Note": "Nota de Regularização do IVA",
    "Dual Use items": "Itens de Uso Duplo",
    "Conflict Minerals": "Minerais de Conflito",
    "Applicable Law": "Legislação Aplicável",
    "Governmental Instrumentality": "Entidade Governamental",
    "Hazardous Materials": "Materiais Perigosos",
    "Site": "Obra",
    "Afungi Site": "Obra de Afungi",
    "Delivery Point": "Local de Entrega",

    # Abreviações e campos
    "NUIT": "NUIT",
    "TAX ID": "NUIT",
    "Tel. No.": "Tel.",
    "E-mail address": "E-mail",
    "Our reference": "Nossa referência",
    "Subject": "Assunto",
    "Job": "Projeto",
    "Requesting Center": "Centro Requisitante",
    "Proc. Dept.": "Dept. de Aquisições",
    "Procurem.Office": "Escritório de Aquisições",
    "Buyer": "Comprador",
    "For internal use": "Para uso interno",
    "PR Ref.": "Ref. RP",
    "Vendor code": "Código do Fornecedor",
    "MZN": "MZN",
    "DDP": "DDP",

    # Termos técnicos
    "Purchase Order": "Ordem de Compra",
    "PO": "Ordem de Compra",
    "Work Order": "Ordem de Serviço",
    "WO": "Ordem de Serviço",
    "General Terms and Conditions": "Condições Gerais",
    "GTC": "Condições Gerais",
    "Health, Safety, Environment": "Saúde, Segurança e Ambiente",
    "HSE": "Saúde, Segurança e Ambiente",
    "Value Added Tax": "IVA",
    "VAT": "IVA",
    "London Court of International Arbitration": "LCIA",
    "LCIA": "LCIA",
    "Exploration and Production Concession Contract": "Contrato de Concessão de Exploração e Produção",
    "EPCC": "Contrato de Concessão de Exploração e Produção",
    "Organization for Economic Co-operation and Development": "OCDE",
    "OECD": "OCDE",
    "Foreign Corrupt Practices Act": "FCPA",
    "FCPA": "FCPA",
    "Federal Aviation Administration": "FFA",
    "FFA": "FFA",

    # Entidades
    "CCS JV": "CCS JV",
    "TOTAL ENERGIES EP Mozambique Area 1, Limitada": "TOTAL ENERGIES EP Moçambique Área 1, Limitada",
    "Kerry Project Logistics (Mozambique) lda": "Kerry Project Logistics (Moçambique) Lda",
    "Pemba": "Pemba",
    "Maputo": "Maputo",

    # Expressões contratuais
    "shall be": "deverá ser",
    "in accordance with": "em conformidade com",
    "unless otherwise provided": "salvo disposição em contrário",
    "subject to": "sujeito a",
    "duly signed": "devidamente assinado",
    "binding on both Parties": "vinculante para ambas as Partes",
    "supersedes any previous agreement": "substitui qualquer acordo anterior",

    # Unidades de medida
    "UM": "UM",
    "Unit of Measure": "Unidade de Medida",
    "NR": "NR",
    "Number": "Número",
    "LS": "LS",
    "Lump Sum": "Valor Global",
    "BX": "CX",
    "Box": "Caixa",
    "DRM": "TMB",
    "Drum": "Tambor",
    "KT": "KT",
    "Kit": "Kit",

    # Documentos
    "Attachment": "Anexo",
    "Letter of Acceptance": "Carta de Aceitação",
    "Effective Date": "Data de Efeito",
    "Expiry Date": "Data de Expiração",
    "Maximum Amount": "Valor Máximo",
    "Base Amount": "Valor Base",
}


def import_glossary():
    """Importa glossário para o banco de dados"""
    print("=" * 80)
    print("IMPORTAÇÃO DE GLOSSÁRIO CCS JV - EN → PT (Moçambique)")
    print("=" * 80)

    # Conectar ao banco
    db = Database()

    if not db.connected:
        print("❌ ERRO: Banco de dados não conectado")
        print("   Configure as credenciais MySQL em config.json")
        return

    print(f"\n✓ Conectado ao banco de dados")
    print(f"  Total de termos a importar: {len(GLOSSARY)}")

    # Importar termos
    imported = 0
    updated = 0
    errors = 0

    for source_text, target_text in GLOSSARY.items():
        try:
            # Verificar se termo já existe
            existing = db.get_dictionary_entry("en", "pt", source_text)

            if existing:
                # Atualizar se diferente
                if existing != target_text:
                    db.add_dictionary_entry("en", "pt", source_text, target_text)
                    updated += 1
                    print(f"  ↻ Atualizado: '{source_text}' → '{target_text}'")
            else:
                # Adicionar novo
                db.add_dictionary_entry("en", "pt", source_text, target_text)
                imported += 1
                print(f"  + Adicionado: '{source_text}' → '{target_text}'")

        except Exception as e:
            errors += 1
            print(f"  ✗ Erro ao importar '{source_text}': {e}")

    print("\n" + "=" * 80)
    print("RESULTADO DA IMPORTAÇÃO")
    print("=" * 80)
    print(f"✓ Novos termos adicionados: {imported}")
    print(f"↻ Termos atualizados: {updated}")
    if errors > 0:
        print(f"✗ Erros: {errors}")
    print(f"\n✓ Total no glossário: {len(GLOSSARY)} termos")
    print("\nO glossário está pronto para ser usado nas traduções EN → PT!")


if __name__ == "__main__":
    import_glossary()
