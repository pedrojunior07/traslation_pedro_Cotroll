# -*- coding: utf-8 -*-
"""
Janela de tradução em batch (múltiplos arquivos).
Mostra apenas percentagem com possibilidade de pausar/retomar.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable, Dict, Tuple
import threading
import json
import os

try:
    from .utils import Token
except ImportError:
    from utils import Token


class BatchTranslationWindow:
    """Janela para tradução em batch com controle de pausa/retomada"""

    def __init__(
        self,
        parent,
        files_and_tokens: List[Tuple[str, List[Token]]],
        translate_func: Callable[[str, List[str]], List[str]],
        on_complete: Callable[[List[Tuple[str, List[Token]]]], None],
        progress_file: str = "translation_progress.json"
    ):
        """
        Args:
            parent: Janela pai
            files_and_tokens: Lista de (file_path, tokens) a traduzir
            translate_func: Função (file_path, textos) -> traduções
            on_complete: Callback quando completo (recebe lista de (file_path, tokens))
            progress_file: Arquivo para salvar progresso
        """
        self.files_and_tokens = files_and_tokens
        self.translate_func = translate_func
        self.on_complete = on_complete
        self.progress_file = progress_file
        self.completed = False
        self.translation_running = False
        self.translation_paused = False

        # Estado do progresso
        self.current_file_idx = 0
        self.current_token_idx = 0
        self.total_tokens = sum(len(tokens) for _, tokens in files_and_tokens)
        self.translated_tokens = 0

        # Tentar carregar progresso anterior
        self._load_progress()

        # Criar janela
        self.window = tk.Toplevel(parent)
        self.window.title(f"Tradução em Batch - {len(files_and_tokens)} arquivos")
        self.window.geometry("900x600")

        # Centralizar
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"900x600+{x}+{y}")

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
        # Frame superior - informações
        info_frame = ttk.Frame(self.window, padding=20)
        info_frame.pack(fill=tk.X)

        ttk.Label(
            info_frame,
            text=f"📦 Tradução em Batch",
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        ttk.Label(
            info_frame,
            text=f"{len(self.files_and_tokens)} arquivos • {self.total_tokens} segmentos",
            font=("Arial", 10),
            foreground="#666666"
        ).pack(anchor=tk.W)

        # Frame central - progresso geral
        progress_frame = ttk.LabelFrame(self.window, text="Progresso Geral", padding=20)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Progresso geral
        self.overall_label = ttk.Label(
            progress_frame,
            text=f"0 / {self.total_tokens} segmentos (0%)",
            font=("Arial", 12, "bold")
        )
        self.overall_label.pack(pady=(0, 10))

        self.overall_progress = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            length=600
        )
        self.overall_progress.pack(pady=(0, 20))
        self.overall_progress["maximum"] = self.total_tokens
        self.overall_progress["value"] = self.translated_tokens

        # Arquivo atual
        self.current_file_label = ttk.Label(
            progress_frame,
            text="Aguardando início...",
            font=("Arial", 10),
            foreground="#0066cc"
        )
        self.current_file_label.pack(pady=(0, 10))

        # Progresso do arquivo atual
        self.file_progress_label = ttk.Label(
            progress_frame,
            text="",
            font=("Arial", 9),
            foreground="#666666"
        )
        self.file_progress_label.pack(pady=(0, 5))

        self.file_progress = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            length=600
        )
        self.file_progress.pack()

        # Lista de arquivos
        files_frame = ttk.LabelFrame(self.window, text="Arquivos", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Treeview de arquivos
        columns = ("status", "file", "tokens")
        self.files_tree = ttk.Treeview(
            files_frame,
            columns=columns,
            show="headings",
            height=8
        )

        self.files_tree.heading("status", text="Status")
        self.files_tree.heading("file", text="Arquivo")
        self.files_tree.heading("tokens", text="Segmentos")

        self.files_tree.column("status", width=120)
        self.files_tree.column("file", width=500)
        self.files_tree.column("tokens", width=100)

        vsb = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=vsb.set)

        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Popular lista de arquivos
        self.file_items = {}
        for idx, (file_path, tokens) in enumerate(self.files_and_tokens):
            file_name = os.path.basename(file_path)
            status = "✅ Concluído" if idx < self.current_file_idx else "⏳ Aguardando..."
            if idx == self.current_file_idx and self.translated_tokens > 0:
                status = "🔄 Em progresso..."

            iid = self.files_tree.insert(
                "",
                "end",
                values=(status, file_name, len(tokens))
            )
            self.file_items[idx] = iid

        # Frame inferior - botões
        btn_frame = ttk.Frame(self.window, padding=20)
        btn_frame.pack(fill=tk.X)

        self.pause_btn = ttk.Button(
            btn_frame,
            text="⏸ Pausar",
            command=self._toggle_pause
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=self._on_cancel
        ).pack(side=tk.LEFT, padx=5)

        self.complete_btn = ttk.Button(
            btn_frame,
            text="✅ Concluir",
            command=self._on_complete,
            state=tk.DISABLED
        )
        self.complete_btn.pack(side=tk.RIGHT, padx=5)

    def _load_progress(self):
        """Carrega progresso anterior se existir"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.current_file_idx = data.get("current_file_idx", 0)
                self.current_token_idx = data.get("current_token_idx", 0)
                self.translated_tokens = data.get("translated_tokens", 0)

                # Restaurar traduções parciais
                saved_translations = data.get("translations", {})
                for file_idx_str, token_translations in saved_translations.items():
                    file_idx = int(file_idx_str)
                    if file_idx < len(self.files_and_tokens):
                        _, tokens = self.files_and_tokens[file_idx]
                        for token_idx_str, translation in token_translations.items():
                            token_idx = int(token_idx_str)
                            if token_idx < len(tokens):
                                tokens[token_idx].translation = translation

                print(f"📂 Progresso carregado: arquivo {self.current_file_idx+1}, token {self.current_token_idx}")
            except Exception as e:
                print(f"⚠ Erro ao carregar progresso: {e}")

    def _save_progress(self):
        """Salva progresso atual"""
        try:
            # Coletar todas as traduções feitas
            translations = {}
            for file_idx, (_, tokens) in enumerate(self.files_and_tokens):
                token_translations = {}
                for token_idx, token in enumerate(tokens):
                    if token.translation:
                        token_translations[str(token_idx)] = token.translation

                if token_translations:
                    translations[str(file_idx)] = token_translations

            data = {
                "current_file_idx": self.current_file_idx,
                "current_token_idx": self.current_token_idx,
                "translated_tokens": self.translated_tokens,
                "translations": translations
            }

            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"💾 Progresso salvo: arquivo {self.current_file_idx+1}, token {self.current_token_idx}")
        except Exception as e:
            print(f"⚠ Erro ao salvar progresso: {e}")

    def _start_translation(self):
        """Inicia tradução em thread separada"""
        self.translation_running = True
        self.translation_paused = False

        def task():
            try:
                # Continuar de onde parou
                for file_idx in range(self.current_file_idx, len(self.files_and_tokens)):
                    if not self.translation_running:
                        break

                    file_path, tokens = self.files_and_tokens[file_idx]
                    file_name = os.path.basename(file_path)

                    # Atualizar status do arquivo
                    self._update_file_status(file_idx, "🔄 Traduzindo...")
                    self._update_current_file(file_name, len(tokens))

                    # Inicializar progresso do arquivo
                    self.file_progress["maximum"] = len(tokens)
                    self.file_progress["value"] = self.current_token_idx if file_idx == self.current_file_idx else 0

                    # Traduzir tokens um por um
                    start_idx = self.current_token_idx if file_idx == self.current_file_idx else 0
                    for token_idx in range(start_idx, len(tokens)):
                        # Verificar pausa
                        while self.translation_paused and self.translation_running:
                            threading.Event().wait(0.1)

                        if not self.translation_running:
                            break

                        token = tokens[token_idx]

                        if not token.skip and token.text.strip():
                            # Traduzir
                            translation = self.translate_func(file_path, [token.text])[0]
                            token.translation = translation

                            # Atualizar progresso
                            self.current_token_idx = token_idx + 1
                            self.translated_tokens += 1

                            self._update_overall_progress()
                            self._update_file_progress(token_idx + 1, len(tokens))

                            # Salvar progresso a cada 10 tokens
                            if self.translated_tokens % 10 == 0:
                                self._save_progress()

                    # Arquivo concluído
                    if self.translation_running:
                        self._update_file_status(file_idx, "✅ Concluído")
                        self.current_file_idx = file_idx + 1
                        self.current_token_idx = 0
                        self._save_progress()

                # Tradução completa
                if self.translation_running:
                    self._finish_translation()

            except Exception as e:
                self._show_error(str(e))

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

    def _toggle_pause(self):
        """Alterna entre pausar e retomar"""
        self.translation_paused = not self.translation_paused

        if self.translation_paused:
            self.pause_btn.config(text="▶️ Retomar")
            self._save_progress()
            messagebox.showinfo(
                "Tradução Pausada",
                "A tradução foi pausada.\n\n"
                "O progresso foi salvo. Clique em 'Retomar' para continuar."
            )
        else:
            self.pause_btn.config(text="⏸ Pausar")

    def _update_file_status(self, file_idx: int, status: str):
        """Atualiza status de um arquivo (thread-safe)"""
        def update():
            if file_idx in self.file_items:
                iid = self.file_items[file_idx]
                values = self.files_tree.item(iid, "values")
                self.files_tree.item(iid, values=(status, values[1], values[2]))
                self.files_tree.see(iid)

        self.window.after(0, update)

    def _update_current_file(self, file_name: str, total_tokens: int):
        """Atualiza informação do arquivo atual (thread-safe)"""
        def update():
            self.current_file_label.config(
                text=f"📄 {file_name} ({total_tokens} segmentos)"
            )

        self.window.after(0, update)

    def _update_overall_progress(self):
        """Atualiza barra de progresso geral (thread-safe)"""
        def update():
            self.overall_progress["value"] = self.translated_tokens
            percent = int((self.translated_tokens / self.total_tokens) * 100)
            self.overall_label.config(
                text=f"{self.translated_tokens} / {self.total_tokens} segmentos ({percent}%)"
            )

        self.window.after(0, update)

    def _update_file_progress(self, current: int, total: int):
        """Atualiza barra de progresso do arquivo atual (thread-safe)"""
        def update():
            self.file_progress["value"] = current
            percent = int((current / total) * 100) if total > 0 else 0
            self.file_progress_label.config(
                text=f"{current} / {total} segmentos ({percent}%)"
            )

        self.window.after(0, update)

    def _finish_translation(self):
        """Finaliza tradução (thread-safe)"""
        def update():
            self.translation_running = False
            self.pause_btn.config(state=tk.DISABLED)
            self.complete_btn.config(state=tk.NORMAL)

            # Deletar arquivo de progresso
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)

            messagebox.showinfo(
                "Tradução Completa",
                f"✅ {len(self.files_and_tokens)} arquivos traduzidos!\n"
                f"Total: {self.total_tokens} segmentos\n\n"
                "Clique em 'Concluir' para exportar."
            )

        self.window.after(0, update)

    def _show_error(self, error_msg: str):
        """Mostra erro (thread-safe)"""
        def update():
            self.translation_running = False
            self._save_progress()
            messagebox.showerror(
                "Erro na Tradução",
                f"{error_msg}\n\n"
                "O progresso foi salvo. Você pode tentar novamente mais tarde."
            )
            self.window.grab_release()
            self.window.destroy()

        self.window.after(0, update)

    def _on_complete(self):
        """Concluir e exportar"""
        self.completed = True

        # Deletar arquivo de progresso
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

        self.window.grab_release()
        self.window.destroy()
        self.on_complete(self.files_and_tokens)

    def _on_cancel(self):
        """Cancelar tradução"""
        if self.translation_running:
            result = messagebox.askyesnocancel(
                "Cancelar Tradução?",
                "A tradução ainda está em andamento.\n\n"
                "Deseja:\n"
                "• SIM: Cancelar e DESCARTAR progresso\n"
                "• NÃO: Cancelar mas SALVAR progresso\n"
                "• CANCELAR: Continuar traduzindo"
            )

            if result is True:  # SIM - descartar
                self.translation_running = False
                if os.path.exists(self.progress_file):
                    os.remove(self.progress_file)
                self.window.grab_release()
                self.window.destroy()
            elif result is False:  # NÃO - salvar
                self.translation_running = False
                self._save_progress()
                messagebox.showinfo(
                    "Progresso Salvo",
                    "O progresso foi salvo.\n\n"
                    "Você pode continuar mais tarde reiniciando a tradução."
                )
                self.window.grab_release()
                self.window.destroy()
            # None - continuar traduzindo (não fazer nada)
        else:
            self._on_close()

    def _on_close(self):
        """Fechar sem concluir"""
        if not self.completed:
            result = messagebox.askyesnocancel(
                "Fechar Janela?",
                "Deseja:\n"
                "• SIM: Fechar e DESCARTAR progresso\n"
                "• NÃO: Fechar mas SALVAR progresso\n"
                "• CANCELAR: Continuar na janela"
            )

            if result is True:  # SIM - descartar
                if os.path.exists(self.progress_file):
                    os.remove(self.progress_file)
                self.window.grab_release()
                self.window.destroy()
            elif result is False:  # NÃO - salvar
                self._save_progress()
                messagebox.showinfo(
                    "Progresso Salvo",
                    "O progresso foi salvo.\n\n"
                    "Você pode continuar mais tarde reiniciando a tradução."
                )
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

    # Criar arquivos e tokens de teste
    files_and_tokens = [
        ("file1.docx", [
            Token("file1.docx", "P1", "Hello world"),
            Token("file1.docx", "P2", "Good morning"),
        ]),
        ("file2.docx", [
            Token("file2.docx", "P1", "Thank you"),
            Token("file2.docx", "P2", "See you later"),
        ]),
        ("file3.docx", [
            Token("file3.docx", "P1", "How are you?"),
            Token("file3.docx", "P2", "I'm fine, thank you"),
        ]),
    ]

    # Função de tradução simulada
    def fake_translate(file_path, texts):
        time.sleep(0.5)  # Simular delay
        return [f"[TRAD] {text}" for text in texts]

    def on_complete(files_and_tokens):
        print("\n✅ Tradução em batch completa!")
        for file_path, tokens in files_and_tokens:
            print(f"\n{file_path}:")
            for t in tokens:
                print(f"  [{t.location}] {t.text} → {t.translation}")

    BatchTranslationWindow(root, files_and_tokens, fake_translate, on_complete)
    root.mainloop()
