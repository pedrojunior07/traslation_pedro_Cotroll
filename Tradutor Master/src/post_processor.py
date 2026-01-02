# -*- coding: utf-8 -*-
"""
Pós-processador de documentos CCS JV
Aplica regras de formatação e correções específicas independente da tradução
"""
import re
from typing import List, Tuple


class DocumentPostProcessor:
    """Pós-processa documentos aplicando regras de formatação CCS JV"""

    # Regras de substituição (regex pattern -> replacement)
    FORMATTING_RULES = [
        # 1. TAX ID / IDENTIFICAÇÃO FISCAL → NUIT
        (r'(?i)TAX\s*ID\s*[:：]', 'NUIT:'),
        (r'(?i)IDENTIFICAÇÃO\s+FISCAL\s*[:：]', 'NUIT:'),
        (r'(?i)QID\s+FISCAL\s*[:：]', 'NUIT:'),
        (r'(?i)ID\s+FISCAL\s*[:：]', 'NUIT:'),

        # 2. Tel. No. / Tel. Não. → Tel.
        (r'Tel\.\s*N[oã]o?\.\s*[:：]', 'Tel.:'),
        (r'Tel\.\s*N[oã]o?\s*[:：]', 'Tel.:'),
        (r'Tel\s+N[oã]o?\.\s*[:：]', 'Tel.:'),

        # 3. E-mail address → E-mail
        (r'(?i)Endere[çc]o\s+de\s+e-?mail\s*[:：]', 'E-mail:'),
        (r'(?i)Endere[çc]o\s+de\s+correio\s+electr[óo]nico\s*[:：]', 'E-mail:'),
        (r'(?i)E-?mail\s+address\s*[:：]', 'E-mail:'),

        # 4. Work Order No. → Ordem de Serviço n.º
        (r'(?i)Work\s+Order\s+No\.\s*', 'Ordem de Serviço n.º '),
        (r'(?i)Número\s+de\s+ordem\s+de\s+trabalho\s+', 'Ordem de Serviço n.º '),

        # 5. Purchase Order No. → Ordem de Compra n.º
        (r'(?i)Purchase\s+Order\s+No\.\s*', 'Ordem de Compra n.º '),
        (r'(?i)Ordem\s+de\s+Compra\s+Não?\.\s*', 'Ordem de Compra n.º '),

        # 6. Agreement No. / Acordo n.o → Acordo n.º
        (r'(?i)Agreement\s+No\.\s*', 'Acordo n.º '),
        (r'Acordo\s+n\.o\s*', 'Acordo n.º '),

        # 7. Vendor code → Código do Fornecedor
        (r'(?i)Vendor\s+code\s*[:：]', 'Código do Fornecedor:'),
        (r'(?i)C[óo]digo\s+de?\s+fornecedor\s*[:：]', 'Código do Fornecedor:'),

        # 8. Our reference → Nossa referência
        (r'(?i)Our\s+reference\s*[:：]', 'Nossa referência:'),
        (r'(?i)A\s+nossa\s+refer[eê]ncia\s*[:：]', 'Nossa referência:'),

        # 9. Subject → Assunto
        (r'(?i)Subject\s*[:：]', 'Assunto:'),

        # 10. Technical office → Gabinete técnico
        (r'(?i)Technical\s+office\s*[:：]', 'Gabinete técnico:'),
        (r'(?i)Escrit[óo]rio\s+t[ée]cnico\s*[:：]', 'Gabinete técnico:'),

        # 11. Moçambico → Moçambique
        (r'MO[ÇC]AMBICO', 'MOÇAMBIQUE'),
        (r'Mo[çc]ambico', 'Moçambique'),

        # 12. GNL → LNG (em contextos técnicos)
        (r'AMA1\s+GNL\s+EPC', 'AMA1 LNG EPC'),

        # 13. Scheduled Commencement/Completion Date
        (r'(?i)Scheduled\s+Commencement\s+Date\s*[:：]', 'Data de Início Agendada:'),
        (r'(?i)Scheduled\s+Completion\s+Date\s*[:：]', 'Data de Conclusão Agendada:'),
        (r'(?i)Data\s+de\s+in[íi]cio\s+programada\s*[:：]', 'Data de Início Agendada:'),

        # 14. Montante → Valor
        (r'Montante\s+de\s+base', 'Valor Base'),
        (r'Montante\s+m[áa]ximo', 'Valor Máximo'),

        # 15. Fabricante → Fornecedor (no contexto de vendor)
        (r'^\s*Fabricante\s*$', 'Fornecedor', re.MULTILINE),

        # 16. Centro de Solicitação → Centro Requisitante
        (r'Centro\s+de\s+Solicita[çc][ãa]o', 'Centro Requisitante'),
        (r'(?i)Requesting\s+Center', 'Centro Requisitante'),

        # 17. Correções de formatação de números
        (r'n\.o\s+', 'n.º '),  # n.o → n.º
        (r'No\.\s+(\d)', r'n.º \1'),  # No. 123 → n.º 123

        # 18. Espaços extras entre palavras
        (r'\s{2,}', ' '),  # Múltiplos espaços → espaço único

        # 19. Pontuação consistente
        (r'\s+[:：]', ':'),  # Espaço antes de dois pontos
        (r'[:：]\s*([A-Za-z0-9])', r': \1'),  # Garantir espaço após dois pontos
    ]

    def __init__(self):
        """Inicializa pós-processador"""
        # Compilar regras regex (cada rule é uma tupla de 2 elementos: pattern, replacement)
        self.compiled_rules = []
        for pattern, replacement in self.FORMATTING_RULES:
            try:
                compiled_pattern = re.compile(pattern)
                self.compiled_rules.append((compiled_pattern, replacement))
            except Exception as e:
                print(f"⚠ Erro ao compilar regex '{pattern}': {e}")

    def process_text(self, text: str) -> Tuple[str, int]:
        """
        Processa texto aplicando regras de formatação.

        Args:
            text: Texto a processar

        Returns:
            Tuple (texto_processado, número_de_correções)
        """
        if not text:
            return text, 0

        result = text
        corrections = 0

        # Aplicar cada regra
        for pattern, replacement in self.compiled_rules:
            new_result, count = pattern.subn(replacement, result)
            if count > 0:
                corrections += count
                result = new_result

        return result, corrections

    def process_batch(self, texts: List[str]) -> Tuple[List[str], int]:
        """
        Processa lote de textos.

        Args:
            texts: Lista de textos

        Returns:
            Tuple (textos_processados, total_de_correções)
        """
        processed = []
        total_corrections = 0

        for text in texts:
            proc_text, count = self.process_text(text)
            processed.append(proc_text)
            total_corrections += count

        return processed, total_corrections


if __name__ == "__main__":
    # Teste
    processor = DocumentPostProcessor()

    test_texts = [
        "TAX ID: 401015418",
        "IDENTIFICAÇÃO FISCAL : 401015418",
        "Tel. No.: +258843118753",
        "Tel. Não.: +258843118753",
        "Endereço de correio electrónico: test@example.com",
        "Work Order No. 31628809",
        "Número de ordem de trabalho 31628809",
        "Agreement No. 5000048433",
        "Acordo n.o 5000048433",
        "Vendor code: 172248",
        "Our reference: Work Order No. 31628809",
        "Subject: PROVISION OF MEDICAL SERVICES",
        "Technical office: Darain S.",
        "Escritório técnico : Binu Sadasivan",
        "MOZAMBICO",
        "Moçambico",
        "AMA1 GNL EPC IN COUNTRY",
        "Scheduled Commencement Date: 01.09.2024",
        "Data de início programada: 01.09.2024",
        "Montante de base: 33.490,00 MZN",
        "Montante máximo: 33.490,00 MZN",
        "Centro de Solicitação: SAIM241199",
    ]

    print("Testando pós-processador...\n")
    print("="*70)

    for text in test_texts:
        processed, count = processor.process_text(text)
        if count > 0:
            print(f"✓ [{count}] {text}")
            print(f"     → {processed}")
            print()

    print("="*70)
    print("\nTeste completo!")
