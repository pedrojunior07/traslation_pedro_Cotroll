# -*- coding: utf-8 -*-
"""
Janela de progresso moderna para operações longas.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional


class ProgressWindow:
    """Janela de progresso com barra, mensagem e possibilidade de cancelar"""

    def __init__(self, parent, title: str = "Processando..."):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("500x200")
        self.window.resizable(False, False)

        # Centralizar na tela
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (200 // 2)
        self.window.geometry(f"500x200+{x}+{y}")

        # Tornar modal
        self.window.transient(parent)
        self.window.grab_set()

        # Desabilitar botão de fechar
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)

        self.cancelled = False

        # Frame principal
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        self.title_label = ttk.Label(
            main_frame,
            text=title,
            font=("Arial", 12, "bold")
        )
        self.title_label.pack(pady=(0, 10))

        # Mensagem de status
        self.status_var = tk.StringVar(value="Preparando...")
        self.status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Arial", 10)
        )
        self.status_label.pack(pady=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            length=460
        )
        self.progress.pack(pady=(0, 10))

        # Label de porcentagem
        self.percent_var = tk.StringVar(value="0%")
        self.percent_label = ttk.Label(
            main_frame,
            textvariable=self.percent_var,
            font=("Arial", 9)
        )
        self.percent_label.pack(pady=(0, 10))

        # Detalhes técnicos (menor)
        self.details_var = tk.StringVar(value="")
        self.details_label = ttk.Label(
            main_frame,
            textvariable=self.details_var,
            font=("Arial", 8),
            foreground="#666666"
        )
        self.details_label.pack(pady=(0, 10))

        # Botão cancelar (opcional)
        self.cancel_btn = ttk.Button(
            main_frame,
            text="Cancelar",
            command=self._on_cancel
        )
        # Não mostrar por padrão

    def update(
        self,
        progress: float,
        status: str = "",
        details: str = ""
    ):
        """
        Atualiza a janela de progresso.

        Args:
            progress: Progresso de 0 a 100
            status: Mensagem principal
            details: Detalhes técnicos (opcional)
        """
        self.progress_var.set(progress)
        self.percent_var.set(f"{int(progress)}%")

        if status:
            self.status_var.set(status)

        if details:
            self.details_var.set(details)

        self.window.update()

    def set_indeterminate(self):
        """Muda para modo indeterminado (animação contínua)"""
        self.progress.config(mode="indeterminate")
        self.progress.start(10)

    def set_determinate(self):
        """Muda para modo determinado (porcentagem)"""
        self.progress.stop()
        self.progress.config(mode="determinate")

    def show_cancel_button(self):
        """Mostra botão de cancelar"""
        self.cancel_btn.pack()

    def hide_cancel_button(self):
        """Esconde botão de cancelar"""
        self.cancel_btn.pack_forget()

    def _on_cancel(self):
        """Callback quando usuário cancela"""
        self.cancelled = True
        self.status_var.set("Cancelando...")
        self.cancel_btn.config(state=tk.DISABLED)

    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado"""
        return self.cancelled

    def close(self):
        """Fecha a janela"""
        try:
            self.window.grab_release()
            self.window.destroy()
        except:
            pass


class MultiStepProgress:
    """
    Progress window para operações com múltiplas etapas.
    Exemplo: Extração PDF (4 etapas), Tradução (N arquivos), etc.
    """

    def __init__(self, parent, title: str, total_steps: int):
        self.progress_window = ProgressWindow(parent, title)
        self.total_steps = total_steps
        self.current_step = 0

    def next_step(self, step_name: str, details: str = ""):
        """Avança para próxima etapa"""
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100

        status = f"[{self.current_step}/{self.total_steps}] {step_name}"
        self.progress_window.update(progress, status, details)

    def update_current_step(self, sub_progress: float, details: str = ""):
        """
        Atualiza progresso dentro da etapa atual.

        Args:
            sub_progress: Progresso de 0 a 100 dentro da etapa
            details: Detalhes
        """
        # Calcular progresso total
        step_weight = 100 / self.total_steps
        base_progress = (self.current_step - 1) * step_weight
        current_progress = base_progress + (sub_progress * step_weight / 100)

        status = f"[{self.current_step}/{self.total_steps}] Em progresso..."
        self.progress_window.update(current_progress, status, details)

    def close(self):
        """Fecha janela"""
        self.progress_window.close()

    def is_cancelled(self) -> bool:
        """Verifica se foi cancelado"""
        return self.progress_window.is_cancelled()


if __name__ == "__main__":
    # Teste
    import time

    root = tk.Tk()
    root.withdraw()

    # Teste 1: Progress simples
    print("Teste 1: Progress simples")
    pw = ProgressWindow(root, "Testando Progress")

    for i in range(101):
        pw.update(
            progress=i,
            status=f"Processando item {i}/100",
            details=f"Arquivo: teste_{i}.txt"
        )
        time.sleep(0.02)

    pw.close()

    # Teste 2: Multi-step
    print("\nTeste 2: Multi-step progress")
    mp = MultiStepProgress(root, "Processando PDF", total_steps=4)

    # Etapa 1
    mp.next_step("Abrindo documento")
    time.sleep(0.5)

    # Etapa 2
    mp.next_step("Analisando estrutura")
    time.sleep(0.5)

    # Etapa 3
    mp.next_step("Extraindo páginas", "42 páginas encontradas")
    for page in range(1, 43):
        mp.update_current_step(
            sub_progress=(page / 42) * 100,
            details=f"Página {page}/42"
        )
        time.sleep(0.05)

    # Etapa 4
    mp.next_step("Finalizando")
    time.sleep(0.5)

    mp.close()

    print("\n✓ Testes concluídos")
