# -*- coding: utf-8 -*-
"""
Ponto de entrada principal do Tradutor Master.
Sistema redesenhado sem licenças - apenas LibreTranslate + Claude.
"""
import tkinter as tk

try:
    from .ui import TranslatorUI
except ImportError:
    from ui import TranslatorUI


def main() -> None:
    """Inicia aplicação"""
    root = tk.Tk()
    app = TranslatorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
