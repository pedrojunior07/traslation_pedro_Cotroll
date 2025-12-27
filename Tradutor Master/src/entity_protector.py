"""
Sistema de proteção de entidades moçambicanas durante tradução.
Identifica e preserva endereços, siglas, nomes próprios, emails, telefones, etc.
"""
import re
from typing import Dict, List, Tuple


class MozambicanEntityProtector:
    """Protege entidades moçambicanas durante tradução."""

    # Siglas e acrônimos moçambicanos comuns
    MOZAMBICAN_ACRONYMS = {
        # Universidades
        'UEM', 'UP', 'UCM', 'ISDB', 'ISCTEM', 'ISPU', 'A Politécnica',
        # Ministérios
        'MITESS', 'MISAU', 'MINEDH', 'MTC', 'MAE', 'MOPHRH', 'MIREME',
        # Empresas Estatais
        'EDM', 'TDM', 'FIPAG', 'CFM', 'LAM', 'AdM', 'HCM', 'HCB',
        # Bancos
        'BCI', 'BIM', 'Standard Bank', 'Absa', 'Moza Banco', 'FNB',
        # Telecomunicações
        'Vodacom', 'Movitel', 'Tmcel',
        # Outras Instituições
        'INE', 'INSS', 'BAU', 'INGC', 'SETSAN', 'IGEPE', 'CTA',
        'CMCM', 'CMM', 'FUNAE', 'INAV', 'INAE', 'AR', 'PRM'
    }

    # Padrões regex para detecção
    PATTERNS = {
        # Endereços (Avenida, Rua, etc.)
        'address': re.compile(
            r'(?:Av\.|Avenida|Rua|R\.|Travessa|Alameda|Praça|Estrada)\s+'
            r'[A-ZÀ-Ú][a-zà-úA-ZÀ-Ú\s\d/,-]+?'
            r'(?:,?\s*(?:n\.?º?|nº|número|No\.?|N\.?)?\s*\d+)?'
        ),

        # Bairros
        'neighborhood': re.compile(
            r'(?:Bairro|B\.)\s+(?:d[aeo]\s+)?[A-ZÀ-Ú][a-zà-úA-ZÀ-Ú\s\d]+?(?=\s*[,.\n]|$)'
        ),

        # Caixas Postais
        'po_box': re.compile(
            r'(?:C\.?P\.?|Caixa\s+Postal|P\.?O\.?\s*Box)\s*:?\s*\d+'
        ),

        # Telefones Moçambicanos (+258 84 123 4567)
        'phone': re.compile(
            r'(?:\+258\s*)?(?:8[2-7]|21|2[3-6])\s*[-.\s]?\d{3}\s*[-.\s]?\d{3,4}'
        ),

        # Emails
        'email': re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        ),

        # URLs
        'url': re.compile(
            r'https?://[^\s<>"\']+'
        ),

        # NUIT (Número Único de Identificação Tributária)
        'nuit': re.compile(
            r'NUIT\s*:?\s*\d{9}'
        ),

        # NIB (Número de Identificação Bancária)
        'nib': re.compile(
            r'NIB\s*:?\s*\d{4}\s*\d{4}\s*\d{11}\s*\d{2}'
        ),

        # Datas em nomes (25 de Junho, 24 de Julho, etc.)
        'historic_date': re.compile(
            r'\b\d{1,2}\s+de\s+(?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|'
            r'Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\b'
        ),

        # Cidades e Províncias
        'location': re.compile(
            r'\b(?:Maputo|Matola|Beira|Nampula|Quelimane|Tete|Chimoio|Nacala|'
            r'Pemba|Inhambane|Xai-Xai|Maxixe|Lichinga|Cuamba|Dondo|Angoche|'
            r'Cidade de Maputo|Província de Maputo|Gaza|Inhambane|Sofala|'
            r'Manica|Tete|Zambézia|Nampula|Cabo Delgado|Niassa)\b'
        ),
    }

    def __init__(self):
        """Inicializa o protetor de entidades."""
        self.placeholder_counter = 0
        self.entity_map: Dict[str, str] = {}

    def protect_text(self, text: str) -> str:
        """
        Substitui entidades por placeholders antes da tradução.

        Args:
            text: Texto original

        Returns:
            Texto com placeholders no lugar das entidades
        """
        self.entity_map = {}
        self.placeholder_counter = 0
        protected_text = text

        # 1. Proteger URLs (primeiro para evitar conflitos)
        protected_text = self._protect_pattern(protected_text, 'url')

        # 2. Proteger emails
        protected_text = self._protect_pattern(protected_text, 'email')

        # 3. Proteger telefones
        protected_text = self._protect_pattern(protected_text, 'phone')

        # 4. Proteger NUIT e NIB
        protected_text = self._protect_pattern(protected_text, 'nuit')
        protected_text = self._protect_pattern(protected_text, 'nib')

        # 5. Proteger endereços completos
        protected_text = self._protect_pattern(protected_text, 'address')

        # 6. Proteger bairros
        protected_text = self._protect_pattern(protected_text, 'neighborhood')

        # 7. Proteger caixas postais
        protected_text = self._protect_pattern(protected_text, 'po_box')

        # 8. Proteger datas históricas em nomes
        protected_text = self._protect_pattern(protected_text, 'historic_date')

        # 9. Proteger cidades e províncias
        protected_text = self._protect_pattern(protected_text, 'location')

        # 10. Proteger siglas moçambicanas
        protected_text = self._protect_acronyms(protected_text)

        return protected_text

    def restore_entities(self, translated_text: str) -> str:
        """
        Restaura entidades originais substituindo placeholders.

        Args:
            translated_text: Texto traduzido com placeholders

        Returns:
            Texto com entidades originais restauradas
        """
        restored_text = translated_text

        # Restaurar em ordem reversa (últimos placeholders primeiro)
        for placeholder in sorted(self.entity_map.keys(), reverse=True):
            original = self.entity_map[placeholder]
            restored_text = restored_text.replace(placeholder, original)

        return restored_text

    def _protect_pattern(self, text: str, pattern_name: str) -> str:
        """Protege entidades que correspondem a um padrão."""
        pattern = self.PATTERNS[pattern_name]

        def replace_with_placeholder(match):
            entity = match.group(0)
            placeholder = f"___ENTITY{self.placeholder_counter}___"
            self.entity_map[placeholder] = entity
            self.placeholder_counter += 1
            return placeholder

        return pattern.sub(replace_with_placeholder, text)

    def _protect_acronyms(self, text: str) -> str:
        """Protege siglas e acrônimos moçambicanos."""
        protected_text = text

        for acronym in self.MOZAMBICAN_ACRONYMS:
            # Criar padrão que captura a sigla como palavra completa
            pattern = re.compile(r'\b' + re.escape(acronym) + r'\b')

            def replace_with_placeholder(match):
                entity = match.group(0)
                placeholder = f"___ENTITY{self.placeholder_counter}___"
                self.entity_map[placeholder] = entity
                self.placeholder_counter += 1
                return placeholder

            protected_text = pattern.sub(replace_with_placeholder, protected_text)

        return protected_text

    def get_protected_entities(self) -> Dict[str, str]:
        """
        Retorna mapa de entidades protegidas.

        Returns:
            Dicionário {placeholder: entidade_original}
        """
        return self.entity_map.copy()


def protect_and_translate(
    text: str,
    translate_func,
    *translate_args,
    **translate_kwargs
) -> str:
    """
    Wrapper que protege entidades, traduz, e restaura.

    Args:
        text: Texto original
        translate_func: Função de tradução a usar
        *translate_args: Argumentos posicionais para translate_func
        **translate_kwargs: Argumentos nomeados para translate_func

    Returns:
        Texto traduzido com entidades preservadas

    Example:
        >>> translated = protect_and_translate(
        ...     "Visite a Av. 24 de Julho, 123",
        ...     api.translate,
        ...     source="pt",
        ...     target="en"
        ... )
        >>> # Resultado: "Visit Av. 24 de Julho, 123"
    """
    protector = MozambicanEntityProtector()

    # 1. Proteger entidades
    protected_text = protector.protect_text(text)

    # 2. Traduzir texto protegido
    translated_protected = translate_func(protected_text, *translate_args, **translate_kwargs)

    # 3. Restaurar entidades originais
    final_text = protector.restore_entities(translated_protected)

    return final_text
