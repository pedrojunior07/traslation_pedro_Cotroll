# -*- coding: utf-8 -*-
"""
Janela de progresso para conversão de PDFs em tokens.
Mostra progresso da conversão de múltiplos arquivos PDF.
"""
import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Callable
import threading
import os

try:
    from .utils import Token
except ImportError:
    from utils import Token


class PDFConversionWindow:
    """Janela para mostrar progresso da conversão de PDFs"""

    def __init__(
        self,
        parent,
        files: List[str],
        extract_func: Callable[[str], List[Token]],
        on_complete: Callable[[List[Tuple[str, List[Token]]]], None]
    ):
        """
        Args:
            parent: Janela pai
            files: Lista de caminhos de arquivos PDF
            extract_func: Função (file_path) -> tokens
            on_complete: Callback quando completo (recebe lista de (file_path, tokens))
        """
        self.files = files
        self.extract_func = extract_func
        self.on_complete = on_complete
        self.conversion_running = True
        self.results: List[Tuple[str, List[Token]]] = []
        self.current_idx = 0

        # Criar janela
        self.window = tk.Toplevel(parent)
        self.window.title(f"Convertendo PDFs - {len(files)} arquivos")
        self.window.geometry("700x400")

        # Centralizar
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"700x400+{x}+{y}")

        # Tornar modal
        self.window.transient(parent)
        self.window.grab_set()

        # Impedir fechar durante conversão
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

        # Iniciar conversão automaticamente
        self._start_conversion()

    def _build_ui(self):
        """Constrói interface"""
        # Frame superior - informações
        info_frame = ttk.Frame(self.window, padding=20)
        info_frame.pack(fill=tk.X)

        ttk.Label(
            info_frame,
            text=f"📄 Convertendo PDFs para Tokens",
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        ttk.Label(
            info_frame,
            text=f"{len(self.files)} arquivos PDF",
            font=("Arial", 10),
            foreground="#666666"
        ).pack(anchor=tk.W)

        # Frame central - progresso
        progress_frame = ttk.LabelFrame(self.window, text="Progresso", padding=20)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Progresso geral
        self.overall_label = ttk.Label(
            progress_frame,
            text=f"0 / {len(self.files)} arquivos (0%)",
            font=("Arial", 12, "bold")
        )
        self.overall_label.pack(pady=(0, 10))

        self.overall_progress = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            length=600
        )
        self.overall_progress.pack(pady=(0, 20))
        self.overall_progress["maximum"] = len(self.files)
        self.overall_progress["value"] = 0

        # Arquivo atual
        self.current_file_label = ttk.Label(
            progress_frame,
            text="Aguardando início...",
            font=("Arial", 10),
            foreground="#0066cc",
            wraplength=600
        )
        self.current_file_label.pack(pady=(0, 20))

        # Log de conversão
        log_label = ttk.Label(progress_frame, text="Log de conversão:", font=("Arial", 9, "bold"))
        log_label.pack(anchor=tk.W, pady=(0, 5))

        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 8),
            bg="#f5f5f5",
            relief=tk.SOLID,
            borderwidth=1
        )
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text.config(state=tk.DISABLED)

        # Frame inferior - botão cancelar
        btn_frame = ttk.Frame(self.window, padding=20)
        btn_frame.pack(fill=tk.X)

        self.cancel_btn = ttk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

    def _start_conversion(self):
        """Inicia conversão em thread separada"""
        def task():
            try:
                for idx, file_path in enumerate(self.files):
                    if not self.conversion_running:
                        break

                    file_name = os.path.basename(file_path)
                    self.current_idx = idx

                    # Atualizar UI
                    self._update_current_file(file_name)
                    self._log(f"[{idx+1}/{len(self.files)}] Convertendo: {file_name}")

                    try:
                        # Extrair tokens
                        tokens = self.extract_func(file_path)
                        self.results.append((file_path, tokens))

                        self._log(f"  ✓ {len(tokens)} segmentos extraídos")

                    except Exception as e:
                        self._log(f"  ✗ Erro: {str(e)}")
                        # Continuar com próximo arquivo mesmo se houver erro

                    # Atualizar progresso
                    self._update_progress(idx + 1)

                # Conversão completa
                if self.conversion_running:
                    self._finish_conversion()

            except Exception as e:
                self._show_error(str(e))

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

    def _update_current_file(self, file_name: str):
        """Atualiza arquivo atual (thread-safe)"""
        def update():
            self.current_file_label.config(text=f"📄 {file_name}")

        self.window.after(0, update)

    def _update_progress(self, current: int):
        """Atualiza barra de progresso (thread-safe)"""
        def update():
            self.overall_progress["value"] = current
            percent = int((current / len(self.files)) * 100)
            self.overall_label.config(
                text=f"{current} / {len(self.files)} arquivos ({percent}%)"
            )

        self.window.after(0, update)

    def _log(self, message: str):
        """Adiciona mensagem ao log (thread-safe)"""
        def update():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        self.window.after(0, update)

    def _finish_conversion(self):
        """Finaliza conversão (thread-safe)"""
        def update():
            self.conversion_running = False
            self.cancel_btn.config(state=tk.DISABLED)

            self._log(f"\n✅ Conversão completa! {len(self.results)} arquivos convertidos.")

            # Chamar callback com resultados
            self.window.after(500, lambda: self._complete_and_close())

        self.window.after(0, update)

    def _complete_and_close(self):
        """Completa e fecha janela"""
        try:
            self.on_complete(self.results)
            self.window.grab_release()
            self.window.destroy()
        except Exception as e:
            self._show_error(f"Erro ao processar resultados:\n{e}")

    def _show_error(self, error_msg: str):
        """Mostra erro (thread-safe)"""
        def update():
            self.conversion_running = False
            self._log(f"\n❌ ERRO: {error_msg}")
            self.cancel_btn.config(text="Fechar")

        self.window.after(0, update)

    def _on_cancel(self):
        """Cancelar conversão"""
        self.conversion_running = False
        self.window.grab_release()
        self.window.destroy()

    def _on_close(self):
        """Fechar sem concluir"""
        if self.conversion_running:
            # Ainda convertendo - cancelar
            self._on_cancel()
        else:
            # Já terminou - pode fechar
            self.window.grab_release()
            self.window.destroy()


if __name__ == "__main__":
    # Teste
    import time
    from utils import Token

    root = tk.Tk()
    root.withdraw()

    # Arquivos de teste
    test_files = [
        "file1.pdf",
        "file2.pdf",
        "file3.pdf",
    ]

    # Função simulada de extração
    def fake_extract(file_path):
        time.sleep(2)  # Simular delay
        return [
            Token(file_path, "P1", f"Text from {file_path}"),
            Token(file_path, "P2", f"More text from {file_path}"),
        ]

    def on_complete(results):
        print("\n✅ Conversão completa!")
        for file_path, tokens in results:
            print(f"\n{file_path}: {len(tokens)} tokens")

    PDFConversionWindow(root, test_files, fake_extract, on_complete)
    root.mainloop()
