"""
Interface para visualizar tabela de tokens de tradução.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
from datetime import datetime

from api_client import APIClient, APIError


class TokenViewerWindow:
    """Janela para visualizar tokens de uma tradução."""

    def __init__(self, parent: tk.Tk, api_client: APIClient):
        """
        Inicializa a janela de visualização de tokens.

        Args:
            parent: Janela pai
            api_client: Cliente da API configurado
        """
        self.parent = parent
        self.api_client = api_client
        self.window = tk.Toplevel(parent)
        self.window.title("Visualizar Tokens de Tradução")
        self.window.geometry("1200x700")

        self._build_layout()
        self._load_recent_translations()

    def _build_layout(self):
        """Constrói o layout da janela."""

        # Frame superior - lista de traduções recentes
        top_frame = ttk.LabelFrame(self.window, text="Traduções Recentes", padding=10)
        top_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # Treeview para traduções
        columns = ("id", "data", "origem", "destino", "tokens_count", "chars_original", "chars_traduzido")
        self.translations_tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=6)

        self.translations_tree.heading("id", text="ID")
        self.translations_tree.heading("data", text="Data/Hora")
        self.translations_tree.heading("origem", text="Origem")
        self.translations_tree.heading("destino", text="Destino")
        self.translations_tree.heading("tokens_count", text="Nº Tokens")
        self.translations_tree.heading("chars_original", text="Chars Original")
        self.translations_tree.heading("chars_traduzido", text="Chars Traduzido")

        self.translations_tree.column("id", width=50, anchor=tk.CENTER)
        self.translations_tree.column("data", width=150)
        self.translations_tree.column("origem", width=80, anchor=tk.CENTER)
        self.translations_tree.column("destino", width=80, anchor=tk.CENTER)
        self.translations_tree.column("tokens_count", width=80, anchor=tk.CENTER)
        self.translations_tree.column("chars_original", width=120, anchor=tk.E)
        self.translations_tree.column("chars_traduzido", width=120, anchor=tk.E)

        self.translations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar para traduções
        trans_scroll = ttk.Scrollbar(top_frame, orient=tk.VERTICAL, command=self.translations_tree.yview)
        trans_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.translations_tree.configure(yscrollcommand=trans_scroll.set)

        # Bind para seleção
        self.translations_tree.bind("<<TreeviewSelect>>", self._on_translation_selected)

        # Botão de atualizar
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(btn_frame, text="Atualizar Lista", command=self._load_recent_translations).pack(side=tk.LEFT)

        # Estatísticas
        self.stats_label = ttk.Label(btn_frame, text="Selecione uma tradução para ver detalhes")
        self.stats_label.pack(side=tk.LEFT, padx=20)

        # Frame inferior - detalhes dos tokens
        bottom_frame = ttk.LabelFrame(self.window, text="Detalhes dos Tokens", padding=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Treeview para tokens
        token_columns = ("location", "original", "traduzido", "len_orig", "len_trad", "ratio", "truncado", "warnings")
        self.tokens_tree = ttk.Treeview(bottom_frame, columns=token_columns, show="headings")

        self.tokens_tree.heading("location", text="Localização")
        self.tokens_tree.heading("original", text="Texto Original")
        self.tokens_tree.heading("traduzido", text="Texto Traduzido")
        self.tokens_tree.heading("len_orig", text="Len Orig")
        self.tokens_tree.heading("len_trad", text="Len Trad")
        self.tokens_tree.heading("ratio", text="Ratio")
        self.tokens_tree.heading("truncado", text="Truncado")
        self.tokens_tree.heading("warnings", text="Avisos")

        self.tokens_tree.column("location", width=150)
        self.tokens_tree.column("original", width=250)
        self.tokens_tree.column("traduzido", width=250)
        self.tokens_tree.column("len_orig", width=70, anchor=tk.E)
        self.tokens_tree.column("len_trad", width=70, anchor=tk.E)
        self.tokens_tree.column("ratio", width=60, anchor=tk.E)
        self.tokens_tree.column("truncado", width=70, anchor=tk.CENTER)
        self.tokens_tree.column("warnings", width=200)

        self.tokens_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar para tokens
        tokens_scroll = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.tokens_tree.yview)
        tokens_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tokens_tree.configure(yscrollcommand=tokens_scroll.set)

        # Tag para destacar linhas truncadas
        self.tokens_tree.tag_configure("truncated", background="#fff3cd")
        self.tokens_tree.tag_configure("warning", background="#f8d7da")

    def _load_recent_translations(self):
        """Carrega traduções recentes da API."""
        try:
            # Limpa a lista atual
            for item in self.translations_tree.get_children():
                self.translations_tree.delete(item)

            # Busca traduções recentes
            translations = self.api_client.get_recent_translations(limit=20)

            for trans in translations:
                # Calcula totais
                total_orig = sum(t.get("original_length", 0) for t in trans.get("tokens", []))
                total_trad = sum(t.get("translated_length", 0) for t in trans.get("tokens", []))

                # Formata data
                created_at = trans.get("created_at", "")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass

                self.translations_tree.insert(
                    "",
                    tk.END,
                    values=(
                        trans.get("id", ""),
                        created_at,
                        trans.get("source", ""),
                        trans.get("target", ""),
                        len(trans.get("tokens", [])),
                        total_orig,
                        total_trad,
                    ),
                    tags=(str(trans.get("id", "")),)
                )

            if not translations:
                self.stats_label.config(text="Nenhuma tradução encontrada")
            else:
                self.stats_label.config(text=f"{len(translations)} traduções carregadas")

        except APIError as e:
            messagebox.showerror("Erro", f"Erro ao carregar traduções: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _on_translation_selected(self, event):
        """Chamado quando uma tradução é selecionada."""
        selection = self.translations_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.translations_tree.item(item, "values")
        if not values:
            return

        translation_id = values[0]
        self._load_tokens(translation_id)

    def _load_tokens(self, translation_id: str):
        """Carrega os tokens de uma tradução específica."""
        try:
            # Limpa a lista atual
            for item in self.tokens_tree.get_children():
                self.tokens_tree.delete(item)

            # Busca tokens da tradução
            tokens = self.api_client.get_translation_tokens(translation_id)

            truncated_count = 0
            warning_count = 0

            for token in tokens:
                warnings_text = ""
                warnings_list = token.get("warnings", [])
                if warnings_list:
                    warnings_text = "; ".join(warnings_list)
                    warning_count += 1

                was_truncated = token.get("was_truncated", False)
                if was_truncated:
                    truncated_count += 1

                # Trunca textos muito longos para exibição
                original = token.get("original_text", "")
                if len(original) > 100:
                    original = original[:97] + "..."

                translated = token.get("translated_text", "")
                if len(translated) > 100:
                    translated = translated[:97] + "..."

                # Determina tags
                tags = []
                if was_truncated:
                    tags.append("truncated")
                if warnings_list:
                    tags.append("warning")

                self.tokens_tree.insert(
                    "",
                    tk.END,
                    values=(
                        token.get("location", ""),
                        original,
                        translated,
                        token.get("original_length", 0),
                        token.get("translated_length", 0),
                        f"{token.get('size_ratio', 0):.2f}",
                        "Sim" if was_truncated else "Não",
                        warnings_text,
                    ),
                    tags=tuple(tags)
                )

            # Atualiza estatísticas
            stats_text = f"{len(tokens)} tokens | {truncated_count} truncados | {warning_count} com avisos"
            self.stats_label.config(text=stats_text)

        except APIError as e:
            messagebox.showerror("Erro", f"Erro ao carregar tokens: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")


class TokenStatisticsWindow:
    """Janela para visualizar estatísticas de tokens."""

    def __init__(self, parent: tk.Tk, api_client: APIClient):
        """
        Inicializa a janela de estatísticas.

        Args:
            parent: Janela pai
            api_client: Cliente da API configurado
        """
        self.parent = parent
        self.api_client = api_client
        self.window = tk.Toplevel(parent)
        self.window.title("Estatísticas de Tokens")
        self.window.geometry("600x400")

        self._build_layout()
        self._load_statistics()

    def _build_layout(self):
        """Constrói o layout da janela."""

        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        ttk.Label(
            main_frame,
            text="Estatísticas Gerais de Tradução",
            font=("TkDefaultFont", 14, "bold")
        ).pack(pady=(0, 20))

        # Frame para estatísticas
        self.stats_frame = ttk.Frame(main_frame)
        self.stats_frame.pack(fill=tk.BOTH, expand=True)

        # Labels para mostrar estatísticas
        self.stats_labels = {}
        stats_keys = [
            ("total_tokens", "Total de Tokens Traduzidos:"),
            ("total_original_chars", "Total de Caracteres Originais:"),
            ("total_translated_chars", "Total de Caracteres Traduzidos:"),
            ("average_size_ratio", "Razão Média de Tamanho:"),
            ("truncated_count", "Tokens Truncados:"),
        ]

        for i, (key, label) in enumerate(stats_keys):
            ttk.Label(self.stats_frame, text=label, font=("TkDefaultFont", 10)).grid(
                row=i, column=0, sticky=tk.W, pady=8
            )
            value_label = ttk.Label(self.stats_frame, text="-", font=("TkDefaultFont", 10, "bold"))
            value_label.grid(row=i, column=1, sticky=tk.W, padx=20, pady=8)
            self.stats_labels[key] = value_label

        # Botão para atualizar
        ttk.Button(
            main_frame,
            text="Atualizar Estatísticas",
            command=self._load_statistics
        ).pack(pady=20)

    def _load_statistics(self):
        """Carrega estatísticas da API."""
        try:
            stats = self.api_client.get_token_statistics()

            self.stats_labels["total_tokens"].config(
                text=f"{stats.get('total_tokens', 0):,}"
            )
            self.stats_labels["total_original_chars"].config(
                text=f"{stats.get('total_original_chars', 0):,}"
            )
            self.stats_labels["total_translated_chars"].config(
                text=f"{stats.get('total_translated_chars', 0):,}"
            )
            self.stats_labels["average_size_ratio"].config(
                text=f"{stats.get('average_size_ratio', 0):.2f}x"
            )
            self.stats_labels["truncated_count"].config(
                text=f"{stats.get('truncated_count', 0):,}"
            )

        except APIError as e:
            messagebox.showerror("Erro", f"Erro ao carregar estatísticas: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")
