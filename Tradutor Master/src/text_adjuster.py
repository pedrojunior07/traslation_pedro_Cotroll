"""
Módulo para ajustar texto traduzido e evitar extrapolação de limites.

Este módulo fornece funções para:
- Comparar tamanho de texto original vs traduzido
- Truncar texto de forma inteligente
- Ajustar tamanho de fonte em documentos
- Quebrar linhas de forma inteligente
"""

import re
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class TextAdjustmentResult:
    """Resultado do ajuste de texto."""
    adjusted_text: str
    original_length: int
    translated_length: int
    adjusted_length: int
    was_truncated: bool
    size_ratio: float
    warnings: List[str]


class TextAdjuster:
    """Classe para ajustar texto traduzido e evitar extrapolação."""

    def __init__(
        self,
        max_length_ratio: float = 1.5,
        enable_truncation: bool = True,
        truncation_suffix: str = "...",
        enable_warnings: bool = True,
    ):
        """
        Inicializa o ajustador de texto.

        Args:
            max_length_ratio: Razão máxima permitida (traduzido/original)
            enable_truncation: Se deve truncar texto que exceder o limite
            truncation_suffix: Sufixo para indicar truncamento
            enable_warnings: Se deve gerar avisos
        """
        self.max_length_ratio = max_length_ratio
        self.enable_truncation = enable_truncation
        self.truncation_suffix = truncation_suffix
        self.enable_warnings = enable_warnings

    def adjust_text(
        self,
        original_text: str,
        translated_text: str,
        max_length: Optional[int] = None,
    ) -> TextAdjustmentResult:
        """
        Ajusta texto traduzido para evitar extrapolação.

        Args:
            original_text: Texto original
            translated_text: Texto traduzido
            max_length: Comprimento máximo permitido (se None, usa ratio)

        Returns:
            TextAdjustmentResult com o texto ajustado e informações
        """
        original_len = len(original_text)
        translated_len = len(translated_text)
        size_ratio = translated_len / original_len if original_len > 0 else 1.0

        warnings = []
        adjusted_text = translated_text
        was_truncated = False

        # Determina o comprimento máximo permitido
        if max_length is None:
            max_length = int(original_len * self.max_length_ratio)

        # Verifica se precisa truncar
        if translated_len > max_length:
            if self.enable_warnings:
                warnings.append(
                    f"Texto traduzido ({translated_len} chars) excede limite "
                    f"({max_length} chars) em {translated_len - max_length} caracteres"
                )

            if self.enable_truncation:
                adjusted_text = self._smart_truncate(
                    translated_text,
                    max_length - len(self.truncation_suffix)
                )
                adjusted_text += self.truncation_suffix
                was_truncated = True

                if self.enable_warnings:
                    warnings.append(f"Texto truncado para {len(adjusted_text)} caracteres")

        elif size_ratio > 1.2:  # Aviso se cresceu mais de 20%
            if self.enable_warnings:
                warnings.append(
                    f"Texto traduzido cresceu {(size_ratio - 1) * 100:.1f}% "
                    "em relação ao original"
                )

        return TextAdjustmentResult(
            adjusted_text=adjusted_text,
            original_length=original_len,
            translated_length=translated_len,
            adjusted_length=len(adjusted_text),
            was_truncated=was_truncated,
            size_ratio=size_ratio,
            warnings=warnings,
        )

    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        Trunca texto de forma inteligente, tentando quebrar em espaços.

        Args:
            text: Texto a truncar
            max_length: Comprimento máximo

        Returns:
            Texto truncado
        """
        if len(text) <= max_length:
            return text

        # Tenta truncar em espaço mais próximo
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')

        # Se encontrou espaço nos últimos 20% do texto, usa ele
        if last_space > max_length * 0.8:
            return truncated[:last_space].rstrip()

        # Senão, trunca direto e remove pontuação final
        return truncated.rstrip('.,;:!?')

    def calculate_font_size_adjustment(
        self,
        original_text: str,
        translated_text: str,
        original_font_size: float,
    ) -> float:
        """
        Calcula ajuste de tamanho de fonte para manter mesmo espaço.

        Args:
            original_text: Texto original
            translated_text: Texto traduzido
            original_font_size: Tamanho de fonte original

        Returns:
            Novo tamanho de fonte sugerido
        """
        original_len = len(original_text)
        translated_len = len(translated_text)

        if translated_len <= original_len:
            return original_font_size

        # Calcula fator de redução
        size_ratio = original_len / translated_len
        new_size = original_font_size * size_ratio

        # Não reduz mais que 30% do tamanho original
        min_size = original_font_size * 0.7
        return max(new_size, min_size)


def split_text_smart(text: str, max_length: int) -> List[str]:
    """
    Divide texto em partes de forma inteligente.

    Args:
        text: Texto a dividir
        max_length: Comprimento máximo de cada parte

    Returns:
        Lista de partes do texto
    """
    if len(text) <= max_length:
        return [text]

    # Divide em sentenças
    sentences = re.split(r'([.!?]+\s+)', text)

    parts = []
    current_part = ""

    for sentence in sentences:
        if len(current_part) + len(sentence) <= max_length:
            current_part += sentence
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = sentence

    if current_part:
        parts.append(current_part.strip())

    return parts


def estimate_text_width(text: str, font_size: float = 12.0) -> float:
    """
    Estima largura aproximada do texto.

    Esta é uma estimativa grosseira assumindo fonte monospace.
    Para cálculo preciso, seria necessário usar bibliotecas de renderização.

    Args:
        text: Texto a estimar
        font_size: Tamanho da fonte

    Returns:
        Largura estimada em pontos
    """
    # Estimativa: cada caractere tem ~60% da largura do tamanho da fonte
    char_width = font_size * 0.6
    return len(text) * char_width
