"""
Manipulação direta de XML do DOCX para preservação RIGOROSA de formatação.
Substitui texto SEM usar python-docx para evitar qualquer alteração de estrutura.
"""
import os
import shutil
import tempfile
import zipfile
from typing import Dict, List, Tuple
from lxml import etree as ET

from utils import Token


class DocxXMLHandler:
    """Manipula DOCX no nível XML para preservação completa de formatação."""

    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }

    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self.temp_dir = None
        self.tree = None
        self.root = None

    def extract(self) -> str:
        """Extrai DOCX para diretório temporário."""
        self.temp_dir = tempfile.mkdtemp(prefix='docx_')
        with zipfile.ZipFile(self.docx_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

        # Carregar document.xml
        doc_path = os.path.join(self.temp_dir, 'word', 'document.xml')
        parser = ET.XMLParser(remove_blank_text=False)  # Preserva TUDO
        self.tree = ET.parse(doc_path, parser)
        self.root = self.tree.getroot()
        return self.temp_dir

    def extract_tokens(self) -> List[Token]:
        """
        Extrai tokens do XML preservando localização EXATA.
        Cada <w:t> vira um token separado.
        """
        tokens = []

        # Encontrar todos os elementos <w:t> no documento
        for idx, t_elem in enumerate(self.root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')):
            text = t_elem.text
            if text and text.strip():
                # Criar identificador único baseado no índice do elemento
                location = f"WT{idx}"
                tokens.append(Token(self.docx_path, location, text))

        return tokens

    def apply_translations(self, translation_map: Dict[str, str], reduce_font_size: bool = True) -> None:
        """
        Aplica traduções substituindo texto dos elementos <w:t>.
        Preserva ABSOLUTAMENTE TODA a estrutura XML.
        Opcionalmente reduz tamanho da fonte em 1pt para garantir layout.

        Args:
            translation_map: {location: translated_text}
            reduce_font_size: Se deve reduzir fonte em 1pt (padrão: True)
        """
        # Iterar sobre todos os elementos <w:t>
        for idx, t_elem in enumerate(self.root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')):
            location = f"WT{idx}"

            if location in translation_map:
                original_text = t_elem.text or ''
                translated_text = translation_map[location]

                # Substituir texto
                t_elem.text = translated_text

                # Preservar atributo xml:space se necessário
                if translated_text.startswith(' ') or translated_text.endswith(' ') or '  ' in translated_text:
                    t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

                # REDUZIR tamanho da fonte em 1pt para garantir layout
                if reduce_font_size:
                    self._reduce_font_size(t_elem)

    def _reduce_font_size(self, t_elem: ET.Element) -> None:
        """
        Reduz tamanho da fonte do elemento <w:t> em 1pt.
        Busca o elemento <w:rPr> (run properties) que contém <w:sz> (font size).
        """
        # Encontrar o elemento <w:r> (run) pai do <w:t>
        run = t_elem.getparent()
        if run is None:
            return

        # Procurar ou criar <w:rPr> (run properties)
        rPr = run.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')

        if rPr is None:
            # Criar <w:rPr> se não existir
            rPr = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
            run.insert(0, rPr)  # Inserir no início do <w:r>

        # Procurar <w:sz> (font size) e <w:szCs> (complex script font size)
        sz = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
        szCs = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}szCs')

        # Processar <w:sz>
        if sz is not None:
            current_size = sz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
            if current_size:
                # Tamanho em half-points (1pt = 2 half-points)
                # Reduzir 1pt = subtrair 2 half-points
                new_size = max(2, int(current_size) - 2)  # Mínimo 1pt (2 half-points)
                sz.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', str(new_size))
        else:
            # Se não tem <w:sz>, criar com valor padrão reduzido
            # Padrão Word: 22 half-points (11pt) → Reduzir para 20 (10pt)
            sz = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
            sz.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '20')  # 10pt
            rPr.append(sz)

        # Processar <w:szCs> (complex script - idiomas como árabe, hebraico)
        if szCs is not None:
            current_size_cs = szCs.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
            if current_size_cs:
                new_size_cs = max(2, int(current_size_cs) - 2)
                szCs.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', str(new_size_cs))
        else:
            # Criar <w:szCs> com mesmo valor de <w:sz>
            szCs = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}szCs')
            szCs.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '20')  # 10pt
            rPr.append(szCs)

    def save(self, output_path: str) -> None:
        """Salva documento modificado preservando TODA a estrutura."""
        # Salvar XML modificado
        doc_path = os.path.join(self.temp_dir, 'word', 'document.xml')

        # Salvar com declaração XML original
        self.tree.write(
            doc_path,
            xml_declaration=True,
            encoding='UTF-8',
            standalone=True,
            pretty_print=False  # NÃO reformatar - preserva estrutura original
        )

        # Recriar DOCX mantendo TODOS os arquivos originais
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.temp_dir):
                # Garantir ordem consistente
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, self.temp_dir)

                    # Usar compressão para arquivos de texto, store para binários
                    if file.endswith(('.xml', '.rels')):
                        compress_type = zipfile.ZIP_DEFLATED
                    else:
                        compress_type = zipfile.ZIP_STORED

                    zipf.write(file_path, arc_name, compress_type=compress_type)

    def cleanup(self) -> None:
        """Remove diretório temporário."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


def extract_tokens_from_docx_xml(file_path: str) -> List[Token]:
    """
    Extrai tokens de um DOCX usando manipulação XML direta.

    Args:
        file_path: Caminho para o arquivo DOCX

    Returns:
        Lista de tokens extraídos
    """
    handler = DocxXMLHandler(file_path)
    handler.extract()
    tokens = handler.extract_tokens()
    handler.cleanup()
    return tokens


def export_docx_with_xml(
    source_path: str,
    tokens: List[Token],
    output_path: str
) -> None:
    """
    Exporta DOCX traduzido usando manipulação XML direta.
    Preserva ABSOLUTAMENTE TODA a formatação, imagens, tabelas, quebras de página.

    Args:
        source_path: Caminho do arquivo original
        tokens: Lista de tokens com traduções
        output_path: Caminho para salvar arquivo traduzido
    """
    # Construir mapa de traduções
    translation_map = {}
    for token in tokens:
        if token.translation and token.translation.strip():
            translation_map[token.location] = token.translation

    # Aplicar traduções
    handler = DocxXMLHandler(source_path)
    handler.extract()
    handler.apply_translations(translation_map)
    handler.save(output_path)
    handler.cleanup()
