import os
from typing import Dict, Iterable, List

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

from utils import Token


def export_translated_document(source_path: str, tokens: Iterable[Token], output_path: str) -> None:
    translation_map = _build_translation_map(tokens)
    ext = os.path.splitext(source_path)[1].lower()
    if ext == ".docx":
        _export_docx(source_path, translation_map, output_path)
    elif ext in (".pptx", ".ppsx"):
        _export_pptx(source_path, translation_map, output_path)
    elif ext in (".xlsx", ".xlsm"):
        _export_xlsx(source_path, translation_map, output_path, keep_vba=ext == ".xlsm")
    elif ext in (".txt",):
        _export_txt(source_path, translation_map, output_path)
    else:
        raise ValueError(f"Extensao nao suportada para exportar: {ext}")


def _build_translation_map(tokens: Iterable[Token]) -> Dict[str, str]:
    translation_map: Dict[str, str] = {}
    for token in tokens:
        translation = token.translation
        if translation.strip():
            translation_map[token.location] = translation
    return translation_map


def _distribute_text(text: str, weights: Iterable[int]) -> List[str]:
    weights_list = list(weights)
    if not weights_list:
        return []
    total = sum(weights_list)
    if total <= 0:
        return [text] + [""] * (len(weights_list) - 1)
    target_len = len(text)
    lengths = [int(target_len * w / total) for w in weights_list]
    delta = target_len - sum(lengths)
    for idx in range(abs(delta)):
        pos = idx % len(lengths)
        lengths[pos] += 1 if delta > 0 else -1
    parts: List[str] = []
    cursor = 0
    for length in lengths:
        if length <= 0:
            parts.append("")
            continue
        parts.append(text[cursor : cursor + length])
        cursor += length
    if cursor < len(text) and parts:
        parts[-1] += text[cursor:]
    return parts


def _replace_docx_paragraph_text(paragraph, new_text: str) -> None:  # noqa: ANN001
    runs = paragraph.runs
    if not runs:
        paragraph.text = new_text
        return
    parts = _distribute_text(new_text, [len(run.text) for run in runs])
    if not parts:
        paragraph.text = new_text
        return
    for run, part in zip(runs, parts):
        run.text = part


def _replace_pptx_paragraph_text(paragraph, new_text: str) -> None:  # noqa: ANN001
    runs = paragraph.runs
    if not runs:
        paragraph.text = new_text
        return
    parts = _distribute_text(new_text, [len(run.text) for run in runs])
    if not parts:
        paragraph.text = new_text
        return
    for run, part in zip(runs, parts):
        run.text = part


def _split_for_paragraphs(paragraph_texts: Iterable[str], text: str) -> List[str]:
    texts = list(paragraph_texts)
    count = len(texts)
    if count <= 1:
        return [text]
    parts = text.split("\n")
    if len(parts) == count:
        return parts
    weights = [len(value) for value in texts]
    return _distribute_text(text, weights)


def _export_docx(source_path: str, translation_map: Dict[str, str], output_path: str) -> None:
    doc = Document(source_path)
    for idx, para in enumerate(doc.paragraphs, start=1):
        location = f"Paragrafo {idx}"
        translation = translation_map.get(location)
        if translation:
            _replace_docx_paragraph_text(para, translation)

    for t_idx, table in enumerate(doc.tables, start=1):
        for r_idx, row in enumerate(table.rows, start=1):
            for c_idx, cell in enumerate(row.cells, start=1):
                location = f"Tabela {t_idx} L{r_idx}C{c_idx}"
                translation = translation_map.get(location)
                if translation:
                    parts = _split_for_paragraphs((para.text for para in cell.paragraphs), translation)
                    for para, part in zip(cell.paragraphs, parts):
                        _replace_docx_paragraph_text(para, part)

    doc.save(output_path)


def _export_pptx(source_path: str, translation_map: Dict[str, str], output_path: str) -> None:
    pres = Presentation(source_path)
    for s_idx, slide in enumerate(pres.slides, start=1):
        for shape_idx, shape in enumerate(slide.shapes, start=1):
            if not getattr(shape, "has_text_frame", False):
                continue
            location = f"Slide {s_idx} Forma {shape_idx}"
            translation = translation_map.get(location)
            if translation:
                text_frame = shape.text_frame
                parts = _split_for_paragraphs((para.text for para in text_frame.paragraphs), translation)
                for para, part in zip(text_frame.paragraphs, parts):
                    _replace_pptx_paragraph_text(para, part)
    pres.save(output_path)


def _export_xlsx(source_path: str, translation_map: Dict[str, str], output_path: str, keep_vba: bool = False) -> None:
    wb = load_workbook(source_path, keep_vba=keep_vba)
    for sheet in wb:
        for row_idx, row in enumerate(sheet.iter_rows(), start=1):
            for col_idx, cell in enumerate(row, start=1):
                location = f"{sheet.title}!R{row_idx}C{col_idx}"
                translation = translation_map.get(location)
                if translation:
                    cell.value = translation
    wb.save(output_path)
    wb.close()


def _export_txt(source_path: str, translation_map: Dict[str, str], output_path: str) -> None:
    with open(source_path, "r", encoding="utf-8") as src_file:
        lines = src_file.readlines()

    new_lines = []
    for idx, line in enumerate(lines, start=1):
        location = f"Linha {idx}"
        translation = translation_map.get(location)
        if translation:
            ending = ""
            if line.endswith("\r\n"):
                ending = "\r\n"
            elif line.endswith("\n"):
                ending = "\n"
            new_lines.append(f"{translation}{ending}")
        else:
            new_lines.append(line)

    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.writelines(new_lines)

