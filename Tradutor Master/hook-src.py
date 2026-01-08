# -*- coding: utf-8 -*-
"""
Hook do PyInstaller para incluir todos os módulos da pasta src
"""
from PyInstaller.utils.hooks import collect_all

# Coletar todos os dados e binários dos módulos principais
datas = []
binaries = []
hiddenimports = [
    'docx',
    'docx.shared',
    'docx.oxml',
    'docx.oxml.ns',
    'docx.oxml.text',
    'docx.text',
    'docx.text.paragraph',
    'docx.enum',
    'docx.enum.text',
    'pdf2docx',
    'fitz',
    'PyMuPDF',
    'anthropic',
    'mysql.connector',
    'PIL',
    'PIL.Image',
]

# Coletar tudo de python-docx
tmp_ret = collect_all('docx')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Coletar tudo de pdf2docx
tmp_ret = collect_all('pdf2docx')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Coletar tudo de PyMuPDF/fitz
try:
    tmp_ret = collect_all('fitz')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except:
    pass
