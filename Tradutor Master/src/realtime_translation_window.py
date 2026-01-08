# -*- coding: utf-8 -*-
"""
Janela de tradução em tempo real.
Mostra tokens sendo traduzidos em tempo real com capacidade de edição inline.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable, Dict
import threading

try:
    from .utils import Token
except ImportError:
    from utils import Token


class RealTimeTranslationWindow:
    """Janela para mostrar traduções em tempo real com edição inline"""

    def __init__(
        self,
        parent,
        tokens: List[Token],
        translate_func: Callable[[List[str]], List[str]],
        on_complete: Callable[[List[Token]], None],
        file_name: str = "Documento",
        history_manager=None,
        translation_id: str = None,
        source_lang: str = "en",
        target_lang: str = "pt",
        output_dir: str = "",
        file_path: str = ""
    ):
        """
        Args:
            parent: Janela pai
            tokens: Lista de tokens a traduzir
            translate_func: Função (textos) -> traduções que traduz lista de textos
            on_complete: Callback chamado quando tradução completa (recebe tokens editados)
            file_name: Nome do arquivo sendo traduzido
            history_manager: Gerenciador de histórico (opcional)
            translation_id: ID da tradução no histórico (opcional)
            source_lang: Idioma de origem
            target_lang: Idioma de destino
            output_dir: Diretório de saída
            file_path: Caminho completo do arquivo
        """
        self.tokens = tokens
        self.translate_func = translate_func
        self.on_complete = on_complete
        self.file_name = file_name
        self.completed = False
        self.translation_running = False

        # Histórico
        self.history_manager = history_manager
        self.translation_id = translation_id
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.output_dir = output_dir
        self.file_path = file_path
        self.total_tokens = len(tokens)
        self.translated_tokens = 0

        # Mapa de iid -> token para facilitar atualização
        self.item_map: Dict[str, Token] = {}

        # Criar janela
        self.window = tk.Toplevel(parent)
        self.window.title(f"Traduzindo em Tempo Real - {file_name}")
        self.window.geometry("1400x800")

        # Centralizar
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (800 // 2)
        self.window.geometry(f"1400x800+{x}+{y}")

        # Tornar modal
        self.window.transient(parent)
        self.window.grab_set()

        # Ao fechar, perguntar se quer cancelar
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

        # Iniciar tradução automaticamente
        self._start_translation()

    def _build_ui(self):
        """Constrói interface"""
        # Frame superior - informações e progresso
        info_frame = ttk.Frame(self.window, padding=10)
        info_frame.pack(fill=tk.X)

        ttk.Label(
            info_frame,
            text=f"📄 {self.file_name}",
            font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            info_frame,
            text=f"{len(self.tokens)} segmentos",
            foreground="#666666"
        ).pack(side=tk.LEFT, padx=5)

        # Barra de progresso
        progress_frame = ttk.Frame(info_frame)
        progress_frame.pack(side=tk.RIGHT, padx=10)

        self.progress_label = ttk.Label(progress_frame, text="0%", font=("Arial", 9))
        self.progress_label.pack(side=tk.LEFT, padx=5)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            length=200
        )
        self.progress_bar.pack(side=tk.LEFT)
        self.progress_bar["maximum"] = len(self.tokens)
        self.progress_bar["value"] = 0

        # Frame principal - tabela
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview com 4 colunas: Status, Original, Tradução, Localização
        columns = ("status", "original", "translation", "location")
        self.tree = ttk.Treeview(
            main_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Cabeçalhos
        self.tree.heading("status", text="Status")
        self.tree.heading("original", text="Texto Original")
        self.tree.heading("translation", text="Tradução")
        self.tree.heading("location", text="Localização")

        # Larguras
        self.tree.column("status", width=100)
        self.tree.column("original", width=450)
        self.tree.column("translation", width=450)
        self.tree.column("location", width=150)

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

        # Popular tabela com status "Aguardando..."
        for token in self.tokens:
            original = token.text[:80] + "..." if len(token.text) > 80 else token.text

            iid = self.tree.insert(
                "",
                "end",
                values=("⏳ Aguardando...", original, "", token.location)
            )
            self.item_map[iid] = token

        # Bind duplo clique para editar
        self.tree.bind("<Double-1>", self._on_double_click)

        # Criar entrada no histórico se não existir
        if self.history_manager and not self.translation_id:
            self.translation_id = self.history_manager.create_translation(
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                files=[self.file_path] if self.file_path else [self.file_name],
                total_tokens=self.total_tokens,
                output_dir=self.output_dir
            )

        # Frame inferior - botões
        btn_frame = ttk.Frame(self.window, padding=10)
        btn_frame.pack(fill=tk.X)

        self.cancel_btn = ttk.Button(
            btn_frame,
            text="❌ Cancelar Tradução",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="✏️ Editar Selecionado",
            command=self._edit_selected
        ).pack(side=tk.LEFT, padx=5)

        self.complete_btn = ttk.Button(
            btn_frame,
            text="✅ Concluir e Exportar",
            command=self._on_complete,
            state=tk.DISABLED  # Desabilitado até terminar tradução
        )
        self.complete_btn.pack(side=tk.RIGHT, padx=5)

    def _start_translation(self):
        """Inicia tradução em thread separada"""
        self.translation_running = True

        def task():
            try:
                # Extrair apenas textos não vazios
                texts_to_translate = []
                token_indices = []

                for idx, token in enumerate(self.tokens):
                    if not token.skip and token.text.strip():
                        texts_to_translate.append(token.text)
                        token_indices.append(idx)

                if not texts_to_translate:
                    self._finish_translation()
                    return

                # TRADUZIR TODOS DE UMA VEZ (batches massivos)
                # A função translate_func já cuida de dividir em batches otimizados internamente
                print(f"\n🚀 Traduzindo {len(texts_to_translate)} segmentos em batches massivos...")

                # Marcar todos como "Traduzindo..."
                for i, token_idx in enumerate(token_indices):
                    token = self.tokens[token_idx]
                    self._update_token_status(token, "🔄 Traduzindo...")

                # Traduzir TODOS de uma vez (Claude divide em batches internamente)
                translations = self.translate_func(texts_to_translate)

                # Processar resultados e atualizar interface
                for i, translation in enumerate(translations):
                    if not self.translation_running:
                        break  # Usuário cancelou

                    token_idx = token_indices[i]
                    token = self.tokens[token_idx]

                    # Garantir que translation é string
                    if isinstance(translation, list):
                        translation = translation[0] if translation else ""
                    elif not isinstance(translation, str):
                        translation = str(translation) if translation else ""

                    token.translation = translation

                    # Atualizar na interface
                    self._update_token_translation(token, translation)

                    # Atualizar progresso
                    progress = i + 1
                    self.translated_tokens = progress
                    self._update_progress(progress, len(texts_to_translate))

                    # Atualizar histórico a cada 100 traduções (reduzido de 10 para evitar overhead)
                    if self.history_manager and self.translation_id and progress % 100 == 0:
                        self.history_manager.update_translation(
                            self.translation_id,
                            translated_tokens=self.translated_tokens
                        )

                # Terminar
                if self.translation_running:
                    self._finish_translation()

            except Exception as e:
                self._show_error(str(e))

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

    def _update_token_status(self, token: Token, status: str):
        """Atualiza status de um token na interface (thread-safe)"""
        def update():
            try:
                for iid, t in self.item_map.items():
                    if t is token:
                        values = self.tree.item(iid, "values")
                        self.tree.item(iid, values=(status, values[1], values[2], values[3]))
                        # Auto-scroll para o item atual
                        self.tree.see(iid)
                        break
            except:
                pass  # Janela foi fechada

        try:
            self.window.after(0, update)
        except:
            pass  # Janela foi fechada

    def _update_token_translation(self, token: Token, translation: str):
        """Atualiza tradução de um token na interface (thread-safe)"""
        def update():
            try:
                for iid, t in self.item_map.items():
                    if t is token:
                        values = self.tree.item(iid, "values")
                        trans_display = translation[:80] + "..." if len(translation) > 80 else translation
                        self.tree.item(iid, values=("✅ Concluído", values[1], trans_display, values[3]))
                        break
            except:
                pass  # Janela foi fechada

        try:
            self.window.after(0, update)
        except:
            pass  # Janela foi fechada

    def _update_progress(self, current: int, total: int):
        """Atualiza barra de progresso (thread-safe)"""
        def update():
            try:
                self.progress_bar["value"] = current
                percent = int((current / total) * 100)
                self.progress_label.config(text=f"{percent}%")
            except:
                pass  # Janela foi fechada

        try:
            self.window.after(0, update)
        except:
            pass  # Janela foi fechada

    def _finish_translation(self):
        """Finaliza tradução e habilita botão de concluir (thread-safe)"""
        self.translation_running = False

        # Marcar como completa no histórico
        if self.history_manager and self.translation_id:
            self.history_manager.complete_translation(self.translation_id)

        def update():
            try:
                self.cancel_btn.config(state=tk.DISABLED)
                self.complete_btn.config(state=tk.NORMAL)

                # Perguntar se quer revisar ou exportar direto
                result = messagebox.askyesno(
                    "Tradução Completa",
                    f"✅ {len(self.tokens)} segmentos traduzidos!\n\n"
                    "Deseja revisar as traduções antes de exportar?\n\n"
                    "• SIM: Revisar e editar traduções\n"
                    "• NÃO: Exportar diretamente"
                )

                if not result:
                    # Exportar diretamente
                    self._on_complete()

            except:
                # Janela foi fechada - não fazer nada
                pass

        try:
            self.window.after(0, update)
        except:
            # Janela foi fechada - exportar automaticamente
            print("✓ Tradução concluída - exportando automaticamente...")
            self.on_complete(self.tokens)

    def _show_error(self, error_msg: str):
        """Mostra erro (thread-safe)"""
        def update():
            self.translation_running = False

            # Marcar como falha no histórico
            if self.history_manager and self.translation_id:
                self.history_manager.fail_translation(self.translation_id, error_msg)

            messagebox.showerror("Erro na Tradução", error_msg)
            self.window.grab_release()
            self.window.destroy()

        self.window.after(0, update)

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
        translation_text.insert("1.0", token.translation if token.translation else "")
        translation_text.focus_set()

        # Botões
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)

        def save():
            new_translation = translation_text.get("1.0", "end-1c")
            token.translation = new_translation

            # Atualizar na árvore
            values = self.tree.item(iid, "values")
            new_trans_display = new_translation[:80] + "..." if len(new_translation) > 80 else new_translation
            self.tree.item(iid, values=(values[0], values[1], new_trans_display, values[3]))

            edit_win.destroy()

        ttk.Button(btn_frame, text="Cancelar", command=edit_win.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Salvar", command=save).pack(side=tk.RIGHT, padx=5)

    def _on_complete(self):
        """Concluir e exportar"""
        self.completed = True
        self.window.grab_release()
        self.window.destroy()
        self.on_complete(self.tokens)

    def _on_cancel(self):
        """Cancelar tradução"""
        if self.translation_running:
            result = messagebox.askyesno(
                "Cancelar Tradução?",
                "A tradução ainda está em andamento.\n\n"
                "Deseja cancelar e descartar o progresso?"
            )
            if result:
                self.translation_running = False
                self.window.grab_release()
                self.window.destroy()
        else:
            self._on_close()

    def _on_close(self):
        """Fechar sem concluir"""
        # Se ainda está traduzindo, não permitir fechar
        if self.translation_running:
            messagebox.showwarning(
                "Tradução em Andamento",
                "A tradução ainda está em progresso.\n\n"
                "Aguarde a conclusão ou clique em 'Cancelar Tradução'."
            )
            return

        if not self.completed:
            result = messagebox.askyesno(
                "Descartar tradução?",
                "Você tem certeza que deseja descartar esta tradução?\n\n"
                "O documento NÃO será exportado."
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
    import time

    root = tk.Tk()
    root.withdraw()

    # Criar tokens de teste
    tokens = [
        Token("test.docx", "P1", "Hello world"),
        Token("test.docx", "P2", "Good morning"),
        Token("test.docx", "P3", "Thank you very much for your help"),
        Token("test.docx", "P4", "The weather is nice today"),
    ]

    # Função de tradução simulada
    def fake_translate(texts):
        time.sleep(1)  # Simular delay
        return [f"[TRADUZIDO] {text}" for text in texts]

    def on_complete(edited_tokens):
        print("\n✅ Tradução completa! Tokens:")
        for t in edited_tokens:
            print(f"  [{t.location}] {t.text} → {t.translation}")

    RealTimeTranslationWindow(root, tokens, fake_translate, on_complete, "test.docx")
    root.mainloop()
