# -*- coding: utf-8 -*-
"""
Janela de revisão de traduções antes de exportar.
Permite editar cada tradução individualmente.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable

try:
    from .utils import Token
except ImportError:
    from utils import Token


class ReviewWindow:
    """Janela para revisar e editar traduções antes de exportar"""

    def __init__(self, parent, tokens: List[Token], on_approve: Callable[[List[Token]], None]):
        """
        Args:
            parent: Janela pai
            tokens: Lista de tokens traduzidos
            on_approve: Callback chamado quando usuário aprovar (recebe tokens editados)
        """
        self.tokens = tokens
        self.on_approve = on_approve
        self.approved = False

        # Criar janela
        self.window = tk.Toplevel(parent)
        self.window.title(f"Revisar Tradução - {len(tokens)} segmentos")
        self.window.geometry("1200x700")

        # Centralizar
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"1200x700+{x}+{y}")

        # Tornar modal
        self.window.transient(parent)
        self.window.grab_set()

        # Ao fechar, perguntar se quer descartar
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    def _build_ui(self):
        """Constrói interface"""
        # Frame superior - informações
        info_frame = ttk.Frame(self.window, padding=10)
        info_frame.pack(fill=tk.X)

        ttk.Label(
            info_frame,
            text=f"📝 {len(self.tokens)} segmentos traduzidos",
            font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            info_frame,
            text="Revise e edite as traduções antes de exportar",
            foreground="#666666"
        ).pack(side=tk.LEFT, padx=20)

        # Frame principal - tabela
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview com 3 colunas: Original, Tradução, Localização
        columns = ("original", "translation", "location")
        self.tree = ttk.Treeview(
            main_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Cabeçalhos
        self.tree.heading("original", text="Texto Original")
        self.tree.heading("translation", text="Tradução")
        self.tree.heading("location", text="Localização")

        # Larguras
        self.tree.column("original", width=400)
        self.tree.column("translation", width=400)
        self.tree.column("location", width=200)

        # Scrollbars
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Popular tabela
        self.item_map = {}  # iid -> token
        for idx, token in enumerate(self.tokens):
            original = token.text[:100] + "..." if len(token.text) > 100 else token.text
            translation = token.translation[:100] + "..." if len(token.translation) > 100 else token.translation

            iid = self.tree.insert(
                "",
                "end",
                values=(original, translation, token.location)
            )
            self.item_map[iid] = token

        # Bind duplo clique para editar
        self.tree.bind("<Double-1>", self._on_double_click)

        # Frame inferior - botões
        btn_frame = ttk.Frame(self.window, padding=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=self._on_close
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="✏️ Editar Selecionado",
            command=self._edit_selected
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="✅ Aprovar e Exportar",
            command=self._on_approve,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)

        # Configurar estilo para botão de aprovar
        style = ttk.Style()
        style.configure("Accent.TButton", background="#059669", foreground="#ffffff", font=("Arial", 10, "bold"))

    def _on_double_click(self, event):
        """Duplo clique para editar"""
        self._edit_selected()

    def _edit_selected(self):
        """Edita tradução selecionada"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Selecione um segmento para editar.")
            return

        iid = selection[0]
        token = self.item_map[iid]

        # Criar janela de edição
        edit_win = tk.Toplevel(self.window)
        edit_win.title(f"Editar Tradução - {token.location}")
        edit_win.geometry("800x400")

        # Centralizar
        edit_win.update_idletasks()
        x = (edit_win.winfo_screenwidth() // 2) - (800 // 2)
        y = (edit_win.winfo_screenheight() // 2) - (400 // 2)
        edit_win.geometry(f"800x400+{x}+{y}")

        edit_win.transient(self.window)
        edit_win.grab_set()

        # Frame principal
        main = ttk.Frame(edit_win, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Original (readonly)
        ttk.Label(main, text="Original:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        original_text = tk.Text(main, height=6, wrap=tk.WORD, bg="#f5f5f5", state=tk.DISABLED)
        original_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        original_text.config(state=tk.NORMAL)
        original_text.insert("1.0", token.text)
        original_text.config(state=tk.DISABLED)

        # Tradução (editável)
        ttk.Label(main, text="Tradução:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        translation_text = tk.Text(main, height=6, wrap=tk.WORD)
        translation_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        translation_text.insert("1.0", token.translation)
        translation_text.focus_set()

        # Botões
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)

        def save():
            new_translation = translation_text.get("1.0", "end-1c")
            token.translation = new_translation

            # Atualizar na árvore
            values = self.tree.item(iid, "values")
            new_trans_display = new_translation[:100] + "..." if len(new_translation) > 100 else new_translation
            self.tree.item(iid, values=(values[0], new_trans_display, values[2]))

            edit_win.destroy()

        ttk.Button(btn_frame, text="Cancelar", command=edit_win.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Salvar", command=save).pack(side=tk.RIGHT, padx=5)

    def _on_approve(self):
        """Aprovar e exportar"""
        self.approved = True
        self.window.grab_release()
        self.window.destroy()
        self.on_approve(self.tokens)

    def _on_close(self):
        """Fechar sem aprovar"""
        if not self.approved:
            result = messagebox.askyesno(
                "Descartar alterações?",
                "Você tem certeza que deseja descartar as traduções?\n\n"
                "As traduções NÃO serão exportadas."
            )
            if result:
                self.window.grab_release()
                self.window.destroy()
        else:
            self.window.grab_release()
            self.window.destroy()


if __name__ == "__main__":
    # Teste
    from utils import Token

    root = tk.Tk()
    root.withdraw()

    # Criar tokens de teste
    tokens = [
        Token("test.docx", "P1", "Hello world", translation="Olá mundo"),
        Token("test.docx", "P2", "Good morning", translation="Bom dia"),
        Token("test.docx", "P3", "Thank you very much for your help", translation="Muito obrigado pela sua ajuda"),
    ]

    def on_approve(edited_tokens):
        print("\n✅ Aprovado! Traduções:")
        for t in edited_tokens:
            print(f"  [{t.location}] {t.text} → {t.translation}")

    ReviewWindow(root, tokens, on_approve)
    root.mainloop()
