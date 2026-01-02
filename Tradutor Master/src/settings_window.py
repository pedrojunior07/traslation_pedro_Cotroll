# -*- coding: utf-8 -*-
"""
Janela de Definições completa com 4 abas:
1. API Claude - Configuração da API key e modelo
2. Monitoramento - Dashboard de uso de tokens
3. Dicionário - Gestão de termos
4. Preferências - Configurações gerais
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from typing import Optional
from config_manager import ConfigManager
from database import Database


class SettingsWindow:
    """Janela de definições completa"""

    def __init__(self, parent, device_id: Optional[int] = None):
        """
        Inicializa janela de definições.

        Args:
            parent: Janela pai (Tkinter root)
            device_id: ID do dispositivo para monitoramento
        """
        self.parent = parent
        self.device_id = device_id or 1
        self.config = ConfigManager()

        # Tentar conectar ao MySQL
        try:
            self.db = Database(self.config)
        except Exception as e:
            self.db = None
            print(f"Aviso: Não foi possível conectar ao MySQL: {e}")

        # Criar janela
        self.window = tk.Toplevel(parent)
        self.window.title("Definições - Tradutor Master")
        self.window.geometry("900x700")

        # Ícone e configurações da janela
        try:
            self.window.iconbitmap(default='icon.ico')
        except:
            pass

        # Notebook com abas
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Criar abas
        self.create_api_tab()
        self.create_monitoring_tab()
        self.create_dictionary_tab()
        self.create_preferences_tab()

        # Botões inferiores
        self.create_bottom_buttons()

        # Carregar dados iniciais
        self.load_monitoring_data()
        self.load_dictionary()

    # ========== ABA 1: API CLAUDE ==========

    def create_api_tab(self):
        """Aba de configuração da API Claude"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  API Claude  ")

        # Container principal
        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # API Key
        ttk.Label(container, text="API Key Anthropic:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        key_frame = ttk.Frame(container)
        key_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 15))

        self.api_key_var = tk.StringVar(value=self.config.get("claude_api_key", ""))
        self.api_entry = ttk.Entry(key_frame, textvariable=self.api_key_var, width=70, show="●")
        self.api_entry.pack(side="left", fill="x", expand=True)

        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            key_frame, text="Mostrar", variable=self.show_key_var,
            command=lambda: self.api_entry.config(show="" if self.show_key_var.get() else "●")
        ).pack(side="left", padx=(5, 0))

        # Modelo Claude
        ttk.Label(container, text="Modelo Claude:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )

        self.model_var = tk.StringVar(value=self.config.get("claude_model", "claude-3-5-sonnet-20241022"))
        model_combo = ttk.Combobox(container, textvariable=self.model_var, width=40, state="readonly", values=[
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        ])
        model_combo.grid(row=3, column=0, sticky="w", pady=(0, 15))

        # Botão testar conexão
        test_frame = ttk.Frame(container)
        test_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        ttk.Button(test_frame, text="Testar Conexão", command=self.test_api_connection).pack(side="left")

        self.api_status_label = ttk.Label(test_frame, text="")
        self.api_status_label.pack(side="left", padx=(10, 0))

        # Separador
        ttk.Separator(container, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=20
        )

        # Informações de preços
        price_frame = ttk.LabelFrame(container, text="Preços por 1M Tokens (USD)")
        price_frame.grid(row=6, column=0, columnspan=3, sticky="ew")

        prices_text = """
Claude 3.5 Sonnet (Recomendado):
  • Input: $3.00    • Output: $15.00
  • Cache Write: $3.75    • Cache Read: $0.30

Claude 3 Opus (Mais Poderoso):
  • Input: $15.00    • Output: $75.00
  • Cache Write: $18.75    • Cache Read: $1.50

Claude 3 Haiku (Mais Rápido/Barato):
  • Input: $0.25    • Output: $1.25
  • Cache Write: $0.30    • Cache Read: $0.03
        """

        ttk.Label(price_frame, text=prices_text, justify="left", font=("Courier", 9)).pack(
            anchor="w", padx=15, pady=10
        )

        # Link para documentação
        doc_frame = ttk.Frame(container)
        doc_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(15, 0))

        ttk.Label(doc_frame, text="💡 Obtenha sua API key em:", font=("Arial", 9)).pack(side="left")
        link_label = ttk.Label(doc_frame, text="console.anthropic.com",
                              foreground="blue", cursor="hand2", font=("Arial", 9, "underline"))
        link_label.pack(side="left", padx=(5, 0))
        link_label.bind("<Button-1>", lambda e: self.open_url("https://console.anthropic.com"))

    def test_api_connection(self):
        """Testa conexão com Anthropic Claude"""
        api_key = self.api_key_var.get().strip()

        if not api_key:
            messagebox.showwarning("Aviso", "Insira a API key primeiro")
            return

        self.api_status_label.config(text="Testando...", foreground="orange")
        self.window.update()

        try:
            from claude_client import ClaudeClient

            client = ClaudeClient(api_key=api_key, model=self.model_var.get())

            if client.test_connection():
                self.api_status_label.config(text="✓ Conexão bem-sucedida!", foreground="green")
                messagebox.showinfo("Sucesso", "API Key válida!\nConexão com Claude funcionando perfeitamente.")
            else:
                raise Exception("Teste de conexão falhou")

        except Exception as e:
            error_msg = str(e)
            self.api_status_label.config(text=f"✗ Erro", foreground="red")
            messagebox.showerror("Erro", f"Falha ao conectar com Claude:\n\n{error_msg}")

    # ========== ABA 2: MONITORAMENTO ==========

    def create_monitoring_tab(self):
        """Aba de monitoramento de tokens/uso"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Monitoramento  ")

        # Container
        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Resumo atual
        summary_frame = ttk.LabelFrame(container, text="Resumo de Uso (últimos 30 dias)")
        summary_frame.pack(fill="x", pady=(0, 15))

        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(padx=15, pady=15)

        # Labels de estatísticas
        row = 0
        self.stat_labels = {}

        stats = [
            ("total_input", "Tokens de Entrada:"),
            ("total_output", "Tokens de Saída:"),
            ("total_cache_creation", "Cache Criado:"),
            ("total_cache_read", "Cache Lido:"),
            ("total_cost", "Custo Total:"),
            ("total_calls", "Chamadas API:"),
        ]

        for key, label_text in stats:
            ttk.Label(summary_grid, text=label_text, font=("Arial", 9, "bold")).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=3
            )
            value_label = ttk.Label(summary_grid, text="0", font=("Arial", 9))
            value_label.grid(row=row, column=1, sticky="w", pady=3)
            self.stat_labels[key] = value_label
            row += 1

        # Tabela de histórico diário
        table_frame = ttk.LabelFrame(container, text="Histórico Diário")
        table_frame.pack(fill="both", expand=True)

        # Controles superiores
        controls = ttk.Frame(table_frame)
        controls.pack(fill="x", padx=10, pady=10)

        ttk.Label(controls, text="Período:").pack(side="left", padx=(0, 5))
        self.days_var = tk.StringVar(value="30")
        days_combo = ttk.Combobox(controls, textvariable=self.days_var, width=10,
                                 state="readonly", values=["7", "30", "60", "90"])
        days_combo.pack(side="left", padx=(0, 10))

        ttk.Button(controls, text="Atualizar", command=self.load_monitoring_data).pack(side="left")
        ttk.Button(controls, text="Exportar CSV", command=self.export_monitoring_csv).pack(side="left", padx=(5, 0))

        # TreeView
        tree_frame = ttk.Frame(table_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("Data", "Input", "Output", "Cache Criado", "Cache Lido", "Custo", "Chamadas")
        self.usage_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.usage_tree.heading(col, text=col)
            width = 100 if col != "Data" else 120
            self.usage_tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.usage_tree.yview)
        self.usage_tree.configure(yscrollcommand=scrollbar.set)

        self.usage_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_monitoring_data(self):
        """Carrega dados de monitoramento do MySQL"""
        if not self.db:
            messagebox.showwarning("Aviso", "Base de dados não conectada")
            return

        try:
            days = int(self.days_var.get())
            summary, daily_data = self.db.get_token_usage(self.device_id, days=days)

            # Atualizar labels de resumo
            self.stat_labels["total_input"].config(text=f"{summary['total_input_tokens']:,}")
            self.stat_labels["total_output"].config(text=f"{summary['total_output_tokens']:,}")
            self.stat_labels["total_cache_creation"].config(text=f"{summary['total_cache_creation_tokens']:,}")
            self.stat_labels["total_cache_read"].config(text=f"{summary['total_cache_read_tokens']:,}")
            self.stat_labels["total_cost"].config(text=f"${summary['total_cost']:.4f}")
            self.stat_labels["total_calls"].config(text=f"{summary['total_calls']:,}")

            # Limpar e preencher tabela
            for item in self.usage_tree.get_children():
                self.usage_tree.delete(item)

            for row in daily_data:
                self.usage_tree.insert("", "end", values=(
                    row["date"],
                    f"{row['input_tokens']:,}",
                    f"{row['output_tokens']:,}",
                    f"{row.get('cache_creation_tokens', 0):,}",
                    f"{row.get('cache_read_tokens', 0):,}",
                    f"${row['total_cost']:.4f}",
                    row['api_calls']
                ))

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados:\n{str(e)}")

    def export_monitoring_csv(self):
        """Exporta dados de monitoramento para CSV"""
        if not self.db:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            days = int(self.days_var.get())
            _, daily_data = self.db.get_token_usage(self.device_id, days=days)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Data", "Input Tokens", "Output Tokens", "Cache Criado",
                               "Cache Lido", "Custo (USD)", "Chamadas API", "Modelo", "Provider"])

                for row in daily_data:
                    writer.writerow([
                        row["date"],
                        row["input_tokens"],
                        row["output_tokens"],
                        row.get("cache_creation_tokens", 0),
                        row.get("cache_read_tokens", 0),
                        f"{row['total_cost']:.4f}",
                        row["api_calls"],
                        row.get("model_used", ""),
                        row.get("provider", "")
                    ])

            messagebox.showinfo("Sucesso", f"Dados exportados para:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar:\n{str(e)}")

    # ========== ABA 3: DICIONÁRIO ==========

    def create_dictionary_tab(self):
        """Aba de configuração do dicionário"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Dicionário  ")

        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Controles superiores
        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="Categoria:").pack(side="left", padx=(0, 5))
        self.dict_category_var = tk.StringVar(value="Todos")
        category_combo = ttk.Combobox(controls, textvariable=self.dict_category_var, width=20, values=[
            "Todos", "empresa_petroleo", "empresa_tecnologia", "empresa_consultoria",
            "banco", "sigla_mocambique", "sigla_tecnica", "termo_tecnico",
            "local_mocambique", "area_petroleo", "unidade", "moeda", "cargo", "documento", "tempo"
        ])
        category_combo.pack(side="left", padx=(0, 5))

        ttk.Button(controls, text="Filtrar", command=self.filter_dictionary).pack(side="left", padx=5)
        ttk.Button(controls, text="+ Adicionar", command=self.add_dictionary_term).pack(side="left")
        ttk.Button(controls, text="Importar CSV", command=self.import_dictionary).pack(side="left", padx=5)

        # Tabela de termos
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("ID", "Termo", "Tradução", "Idiomas", "Categoria", "Usos")
        self.dict_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        self.dict_tree.heading("ID", text="ID")
        self.dict_tree.heading("Termo", text="Termo")
        self.dict_tree.heading("Tradução", text="Tradução")
        self.dict_tree.heading("Idiomas", text="Idiomas")
        self.dict_tree.heading("Categoria", text="Categoria")
        self.dict_tree.heading("Usos", text="Usos")

        self.dict_tree.column("ID", width=50, anchor="center")
        self.dict_tree.column("Termo", width=150)
        self.dict_tree.column("Tradução", width=150)
        self.dict_tree.column("Idiomas", width=80, anchor="center")
        self.dict_tree.column("Categoria", width=120)
        self.dict_tree.column("Usos", width=60, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.dict_tree.yview)
        self.dict_tree.configure(yscrollcommand=scrollbar.set)

        self.dict_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botões de ação
        action_frame = ttk.Frame(container)
        action_frame.pack(fill="x")

        ttk.Button(action_frame, text="Editar", command=self.edit_dictionary_term).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Remover", command=self.remove_dictionary_term).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Exportar CSV", command=self.export_dictionary).pack(side="left", padx=5)

    def load_dictionary(self):
        """Carrega termos do dicionário"""
        if not self.db:
            return

        try:
            category = self.dict_category_var.get()
            category_filter = None if category == "Todos" else category

            terms = self.db.search_dictionary(category=category_filter)

            # Limpar tabela
            for item in self.dict_tree.get_children():
                self.dict_tree.delete(item)

            # Preencher
            for term in terms:
                self.dict_tree.insert("", "end", values=(
                    term["id"],
                    term["term"],
                    term["translation"],
                    f"{term['source_lang']}→{term['target_lang']}",
                    term.get("category", ""),
                    term.get("usage_count", 0)
                ))

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dicionário:\n{str(e)}")

    def filter_dictionary(self):
        """Aplica filtro de categoria"""
        self.load_dictionary()

    def add_dictionary_term(self):
        """Adiciona novo termo ao dicionário"""
        if not self.db:
            return

        # Criar janela de diálogo
        dialog = tk.Toplevel(self.window)
        dialog.title("Adicionar Termo")
        dialog.geometry("400x250")
        dialog.transient(self.window)
        dialog.grab_set()

        # Campos
        ttk.Label(dialog, text="Termo:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        term_entry = ttk.Entry(dialog, width=40)
        term_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Tradução:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        translation_entry = ttk.Entry(dialog, width=40)
        translation_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Idioma Origem:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        source_entry = ttk.Entry(dialog, width=40)
        source_entry.insert(0, "en")
        source_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Idioma Destino:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        target_entry = ttk.Entry(dialog, width=40)
        target_entry.insert(0, "pt")
        target_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Categoria:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        category_entry = ttk.Entry(dialog, width=40)
        category_entry.grid(row=4, column=1, padx=10, pady=5)

        def save():
            term = term_entry.get().strip()
            translation = translation_entry.get().strip()
            source = source_entry.get().strip()
            target = target_entry.get().strip()
            category = category_entry.get().strip() or None

            if not all([term, translation, source, target]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios")
                return

            if self.db.add_dictionary_term(term, translation, source, target, category):
                messagebox.showinfo("Sucesso", "Termo adicionado com sucesso!")
                dialog.destroy()
                self.load_dictionary()
            else:
                messagebox.showerror("Erro", "Erro ao adicionar termo")

        # Botões
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15)

        ttk.Button(btn_frame, text="Salvar", command=save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side="left", padx=5)

    def edit_dictionary_term(self):
        """Edita termo selecionado"""
        selection = self.dict_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um termo para editar")
            return

        # Implementação similar a add_dictionary_term mas com update
        messagebox.showinfo("Info", "Funcionalidade de edição em desenvolvimento")

    def remove_dictionary_term(self):
        """Remove termo selecionado"""
        if not self.db:
            return

        selection = self.dict_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um termo para remover")
            return

        item = self.dict_tree.item(selection[0])
        term_id = item["values"][0]
        term = item["values"][1]

        if messagebox.askyesno("Confirmar", f"Remover o termo '{term}'?"):
            if self.db.delete_dictionary_term(term_id):
                messagebox.showinfo("Sucesso", "Termo removido!")
                self.load_dictionary()
            else:
                messagebox.showerror("Erro", "Erro ao remover termo")

    def import_dictionary(self):
        """Importa termos de CSV"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path or not self.db:
            return

        try:
            added = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if self.db.add_dictionary_term(
                        row.get("term", ""),
                        row.get("translation", ""),
                        row.get("source_lang", "en"),
                        row.get("target_lang", "pt"),
                        row.get("category")
                    ):
                        added += 1

            messagebox.showinfo("Sucesso", f"{added} termos importados!")
            self.load_dictionary()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao importar:\n{str(e)}")

    def export_dictionary(self):
        """Exporta dicionário para CSV"""
        if not self.db:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            category = self.dict_category_var.get()
            category_filter = None if category == "Todos" else category
            terms = self.db.search_dictionary(category=category_filter)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["id", "term", "translation", "source_lang", "target_lang", "category", "usage_count"])

                for term in terms:
                    writer.writerow([
                        term["id"],
                        term["term"],
                        term["translation"],
                        term["source_lang"],
                        term["target_lang"],
                        term.get("category", ""),
                        term.get("usage_count", 0)
                    ])

            messagebox.showinfo("Sucesso", f"Dicionário exportado para:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar:\n{str(e)}")

    # ========== ABA 4: PREFERÊNCIAS ==========

    def create_preferences_tab(self):
        """Aba de preferências gerais"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Preferências  ")

        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Idiomas padrão
        lang_frame = ttk.LabelFrame(container, text="Idiomas Padrão")
        lang_frame.pack(fill="x", pady=(0, 15))

        lang_grid = ttk.Frame(lang_frame)
        lang_grid.pack(padx=15, pady=15)

        ttk.Label(lang_grid, text="Idioma Origem:").grid(row=0, column=0, sticky="w", pady=5)
        self.default_source_var = tk.StringVar(value=self.config.get("default_source_lang", "en"))
        ttk.Combobox(lang_grid, textvariable=self.default_source_var, width=30, values=[
            "en", "pt", "fr", "es", "de", "it", "nl", "pl", "ru", "zh"
        ]).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(lang_grid, text="Idioma Destino:").grid(row=1, column=0, sticky="w", pady=5)
        self.default_target_var = tk.StringVar(value=self.config.get("default_target_lang", "pt"))
        ttk.Combobox(lang_grid, textvariable=self.default_target_var, width=30, values=[
            "en", "pt", "fr", "es", "de", "it", "nl", "pl", "ru", "zh"
        ]).grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Comportamento
        behavior_frame = ttk.LabelFrame(container, text="Comportamento de Tradução")
        behavior_frame.pack(fill="x", pady=(0, 15))

        behavior_grid = ttk.Frame(behavior_frame)
        behavior_grid.pack(padx=15, pady=15, anchor="w")

        self.use_dictionary_var = tk.BooleanVar(value=self.config.get("use_dictionary", True))
        ttk.Checkbutton(
            behavior_grid,
            text="Usar dicionário automaticamente (economiza tokens)",
            variable=self.use_dictionary_var
        ).pack(anchor="w", pady=3)

        self.use_ai_var = tk.BooleanVar(value=self.config.get("use_ai", True))
        ttk.Checkbutton(
            behavior_grid,
            text="Usar IA (Claude) por padrão para traduções",
            variable=self.use_ai_var
        ).pack(anchor="w", pady=3)

        self.auto_glossary_var = tk.BooleanVar(value=self.config.get("auto_glossary", False))
        ttk.Checkbutton(
            behavior_grid,
            text="Criar glossário automaticamente",
            variable=self.auto_glossary_var
        ).pack(anchor="w", pady=3)

        # LibreTranslate
        libre_frame = ttk.LabelFrame(container, text="LibreTranslate")
        libre_frame.pack(fill="x", pady=(0, 15))

        libre_grid = ttk.Frame(libre_frame)
        libre_grid.pack(padx=15, pady=15)

        ttk.Label(libre_grid, text="URL:").grid(row=0, column=0, sticky="w", pady=5)
        self.libre_url_var = tk.StringVar(value=self.config.get("libretranslate_url", "http://102.211.186.44/translate"))
        ttk.Entry(libre_grid, textvariable=self.libre_url_var, width=50).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(libre_grid, text="Timeout (s):").grid(row=1, column=0, sticky="w", pady=5)
        self.libre_timeout_var = tk.StringVar(value=str(self.config.get("libretranslate_timeout", 15.0)))
        ttk.Entry(libre_grid, textvariable=self.libre_timeout_var, width=10).grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # ========== BOTÕES INFERIORES ==========

    def create_bottom_buttons(self):
        """Botões salvar/cancelar"""
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Salvar", command=self.save_settings).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.window.destroy).pack(side="right", padx=5)

    def save_settings(self):
        """Salva todas as configurações"""
        try:
            # Salvar configurações
            self.config.update({
                "claude_api_key": self.api_key_var.get().strip(),
                "claude_model": self.model_var.get(),
                "default_source_lang": self.default_source_var.get(),
                "default_target_lang": self.default_target_var.get(),
                "use_dictionary": self.use_dictionary_var.get(),
                "use_ai": self.use_ai_var.get(),
                "auto_glossary": self.auto_glossary_var.get(),
                "libretranslate_url": self.libre_url_var.get().strip(),
                "libretranslate_timeout": float(self.libre_timeout_var.get()),
            })

            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações:\n{str(e)}")

    # ========== HELPERS ==========

    def open_url(self, url):
        """Abre URL no navegador"""
        import webbrowser
        webbrowser.open(url)


if __name__ == "__main__":
    # Teste standalone
    root = tk.Tk()
    root.withdraw()

    SettingsWindow(root, device_id=1)

    root.mainloop()
