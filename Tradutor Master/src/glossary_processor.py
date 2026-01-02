# -*- coding: utf-8 -*-
"""
Processador de Glossário - Aplica termos do glossário nas traduções
Funciona tanto com LibreTranslate quanto Claude.
"""
import re
from typing import Dict, List, Tuple


class GlossaryProcessor:
    """Processa traduções aplicando glossário de forma inteligente"""

    def __init__(self, dictionary: Dict[str, str]):
        """
        Args:
            dictionary: Dicionário {termo_origem: tradução}
        """
        self.dictionary = dictionary

        # Criar padrões regex para cada termo (ordenados por tamanho, maior primeiro)
        # Isso garante que frases completas sejam substituídas antes de palavras individuais
        sorted_terms = sorted(dictionary.keys(), key=len, reverse=True)

        self.patterns = []
        for term in sorted_terms:
            # Criar padrão que captura o termo com case-insensitive para melhor cobertura
            # Mas preserva o case original na substituição
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            self.patterns.append((term, pattern, dictionary[term]))

    def apply_to_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Aplica glossário a um texto, substituindo termos conhecidos.

        Args:
            text: Texto traduzido

        Returns:
            Tuple (texto_corrigido, lista_de_substituições_feitas)
        """
        # Validar tipo do texto
        if not isinstance(text, str):
            # Se for lista, converter primeiro elemento (caso comum de erro)
            if isinstance(text, list) and len(text) > 0:
                text = str(text[0])
            else:
                # Converter para string ou retornar vazio
                text = str(text) if text else ""

        if not text or not self.dictionary:
            return text, []

        substitutions = []
        result = text

        # Aplicar cada padrão
        for original_term, pattern, glossary_translation in self.patterns:
            matches = list(pattern.finditer(result))

            if matches:
                for match in matches:
                    matched_text = match.group(0)

                    # Preservar capitalização
                    if matched_text.isupper():
                        # TODO MAIÚSCULO
                        replacement = glossary_translation.upper()
                    elif matched_text[0].isupper():
                        # Primeira letra maiúscula
                        replacement = glossary_translation[0].upper() + glossary_translation[1:]
                    else:
                        # Minúsculo
                        replacement = glossary_translation

                    # Substituir
                    result = result[:match.start()] + replacement + result[match.end():]

                    # Registrar substituição
                    substitutions.append(f"{matched_text} → {replacement}")

        return result, substitutions

    def apply_to_batch(self, texts: List[str]) -> Tuple[List[str], Dict[int, List[str]]]:
        """
        Aplica glossário a um lote de textos.

        Args:
            texts: Lista de textos traduzidos

        Returns:
            Tuple (textos_corrigidos, dicionário_de_substituições_por_índice)
        """
        corrected_texts = []
        all_substitutions = {}

        for idx, text in enumerate(texts):
            # Garantir que text é string
            if not isinstance(text, str):
                if isinstance(text, list) and len(text) > 0:
                    text = str(text[0])
                else:
                    text = str(text) if text else ""

            corrected, subs = self.apply_to_text(text)
            corrected_texts.append(corrected)

            if subs:
                all_substitutions[idx] = subs

        return corrected_texts, all_substitutions

    def get_terms_in_text(self, text: str) -> List[str]:
        """
        Identifica quais termos do glossário aparecem no texto.

        Args:
            text: Texto a analisar

        Returns:
            Lista de termos encontrados
        """
        found_terms = []

        for original_term, pattern, _ in self.patterns:
            if pattern.search(text):
                found_terms.append(original_term)

        return found_terms


def create_glossary_from_db(db, source: str, target: str) -> GlossaryProcessor:
    """
    Cria processador de glossário a partir do banco de dados.

    Args:
        db: Instância de Database
        source: Código do idioma origem
        target: Código do idioma destino

    Returns:
        GlossaryProcessor configurado
    """
    dictionary = db.get_dictionary(source, target)
    return GlossaryProcessor(dictionary)


# Glossário embutido para caso o banco não esteja disponível
DEFAULT_CCS_GLOSSARY_EN_PT = {
    # Termos mais críticos do CCS JV
    "Purchase Order": "Ordem de Compra",
    "Work Order": "Ordem de Serviço",
    "TAX ID": "NUIT",
    "Tel. No.": "Tel.",
    "E-mail address": "E-mail",
    "Our reference": "Nossa referência",
    "Subject": "Assunto",
    "Vendor code": "Código do Fornecedor",
    "Purchaser": "Contratante",
    "Supplier": "Fornecedor",
    "Subcontractor": "Subcontratado",
    "Contractor": "Contratante",
    "Vendor": "Fornecedor",
    "Agreement No.": "Acordo n.º",
    "Base Amount": "Valor Base",
    "Maximum Amount": "Valor Máximo",
    "Scheduled Commencement Date": "Data de Início Agendada",
    "Scheduled Completion Date": "Data de Conclusão Agendada",
    "Technical office": "Gabinete técnico",
    "Requesting Center": "Centro Requisitante",
    "Job": "Projeto",
    "MOZAMBIQUE": "MOÇAMBIQUE",
    "Mozambique": "Moçambique",
    "dated": "datado de",
    "PROVISION OF MEDICAL SERVICES": "PROVISÃO DOS SERVIÇOS MÉDICOS",
    "OCCUPATIONAL HEALTH": "SAÚDE OCUPACIONAL",
    "AMBULANCE SERVICES": "SERVIÇOS DE AMBULÂNCIA",
    "FOR THE MONTH OF": "PELO MÊS DE",
    "Service Acceptance Paper": "Documento de Aceitação do Serviço",
    "Authorized Representatives": "Representantes Autorizados",
    "calendar days": "dias de calendário",
    "upon completion": "após a conclusão",
    "original invoice": "fatura original",
}


if __name__ == "__main__":
    # Teste
    print("Testando GlossaryProcessor...\n")

    # Criar processador com glossário de teste
    processor = GlossaryProcessor(DEFAULT_CCS_GLOSSARY_EN_PT)

    # Texto de exemplo
    test_texts = [
        "Purchase Order No. 31628809",
        "TAX ID: 401015418",
        "Tel. No.: +258843118753",
        "Vendor code: 172248",
        "Subject: PROVISION OF MEDICAL SERVICES",
        "Our reference: Work Order No. 31628809",
        "The Purchaser shall pay the Supplier",
        "MOZAMBIQUE BRANCH",
        "Technical office: Darain S.",
    ]

    print("Textos originais (simulando tradução do LibreTranslate):")
    print("-" * 70)
    for text in test_texts:
        print(f"  • {text}")

    print("\n\nAplicando glossário...")
    print("-" * 70)

    corrected, substitutions = processor.apply_to_batch(test_texts)

    for idx, (original, corrected_text) in enumerate(zip(test_texts, corrected)):
        print(f"\n[{idx+1}] Original:  {original}")
        print(f"    Corrigido: {corrected_text}")

        if idx in substitutions:
            print(f"    Substituições: {', '.join(substitutions[idx])}")

    print("\n✓ Teste concluído!")
