# -*- coding: utf-8 -*-
"""
UI redesenhada do Tradutor Master - Sistema simplificado sem licenças.
Apenas LibreTranslate + Claude com definições integradas.
"""
import json
import os
import threading
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple

from extractor import extract_tokens
from token_guard import TokenGuard
from translator import export_translated_document
from utils import Token, merge_tokens

# Novos clientes diretos
from config_manager import ConfigManager
from libretranslate_client import LibreTranslateClient
from claude_client import ClaudeClient
from database import Database
from translation_cache import TranslationCache


class TranslatorUI:
    """UI principal com abas integradas para tradução e configurações"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tradutor Master - Claude + LibreTranslate")
        self.root.geometry("1200x800")

        # Estado da aplicação
        self.tokens: List[Token] = []
        self._selected_index: Optional[int] = None
        self._busy = False
        self.glossary: Dict[str, str] = {}
        self.folder_files: List[str] = []
        self.file_iid_map: Dict[str, str] = {}
        self._spinner_running = False

        # Clientes e configuração
        self.config = ConfigManager()
        self.libre_client: Optional[LibreTranslateClient] = None
        self.claude_client: Optional[ClaudeClient] = None
        self.db: Optional[Database] = None
        self.cache = TranslationCache()

        # Variáveis de estado
        self.source_var = tk.StringVar(value=self.config.get("default_source_lang", "en"))
        self.target_var = tk.StringVar(value=self.config.get("default_target_lang", "pt"))
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.skip_existing_var = tk.BooleanVar(value=True)
        self.use_ai_var = tk.BooleanVar(value=self.config.get("use_ai", True))
        self.use_dictionary_var = tk.BooleanVar(value=self.config.get("use_dictionary", True))
        self.status_var = tk.StringVar(value="Pronto")
        self.eta_var = tk.StringVar(value="")
        self.file_progress_var = tk.StringVar(value="")
        self.spinner_var = tk.StringVar(value="")

        # Inicializar clientes
        self._init_clients()

        # Aplicar tema e construir layout
        self._apply_theme()
        self._build_layout()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_clients(self) -> None:
        """Inicializa clientes LibreTranslate, Claude e Database"""
        try:
            # LibreTranslate
            libre_url = self.config.get("libretranslate_url", "http://102.211.186.44/translate")
            libre_timeout = self.config.get("libretranslate_timeout", 15.0)
            self.libre_client = LibreTranslateClient(base_url=libre_url, timeout=libre_timeout)
        except Exception as e:
            print(f"⚠ Erro ao inicializar LibreTranslate: {e}")

        try:
            # Claude (só se tiver API key)
            claude_api_key = self.config.get("claude_api_key", "")
            if claude_api_key:
                claude_model = self.config.get("claude_model", "claude-3-5-sonnet-20241022")
                self.claude_client = ClaudeClient(api_key=claude_api_key, model=claude_model)
        except Exception as e:
            print(f"⚠ Erro ao inicializar Claude: {e}")

        try:
            # Database
            self.db = Database(self.config)
        except Exception as e:
            print(f"⚠ Erro ao conectar ao MySQL: {e}")

    def _build_layout(self) -> None:
        """Constrói layout com abas integradas"""
        # Header
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill=tk.X, padx=10, pady=(10, 0))
        ttk.Label(header, text="Tradutor Master", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header, text="Claude + LibreTranslate", style="Subheader.TLabel").pack(
            side=tk.LEFT, padx=(8, 0)
        )

        # Status no canto direito
        status_frame = ttk.Frame(header)
        status_frame.pack(side=tk.RIGHT)
        ttk.Label(status_frame, textvariable=self.status_var).pack()

        # Notebook principal com abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Aba 1: Tradução
        self._create_translation_tab()

        # Aba 2: Configurações Claude
        self._create_claude_settings_tab()

        # Aba 3: Monitoramento
        self._create_monitoring_tab()

        # Aba 4: Dicionário
        self._create_dictionary_tab()

        # Aba 5: Preferências
        self._create_preferences_tab()

    def _create_translation_tab(self) -> None:
        """Aba principal de tradução"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📄 Tradução")

        # Seção: Idiomas e opções
        lang_frame = ttk.LabelFrame(tab, text="Idiomas e Opções", padding=10)
        lang_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(lang_frame, text="De:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        source_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.source_var,
            values=["en", "pt", "fr", "es", "de", "it", "nl", "pl", "ru", "ar", "zh", "ja"],
            width=10,
            state="readonly",
        )
        source_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(lang_frame, text="Para:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        target_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.target_var,
            values=["en", "pt", "fr", "es", "de", "it", "nl", "pl", "ru", "ar", "zh", "ja"],
            width=10,
            state="readonly",
        )
        target_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Checkbutton(lang_frame, text="Usar Claude IA", variable=self.use_ai_var).grid(
            row=0, column=4, sticky=tk.W, padx=(30, 5), pady=5
        )
        ttk.Checkbutton(lang_frame, text="Usar Dicionário", variable=self.use_dictionary_var).grid(
            row=0, column=5, sticky=tk.W, padx=5, pady=5
        )

        # Seção: Seleção de arquivos/pastas
        files_frame = ttk.LabelFrame(tab, text="Arquivos", padding=10)
        files_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(files_frame, text="Origem:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(files_frame, textvariable=self.input_dir_var, width=50).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )
        ttk.Button(files_frame, text="Selecionar Pasta", command=self.select_input_dir).grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )
        ttk.Button(files_frame, text="Selecionar Arquivo", command=self.select_single_file).grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(files_frame, text="Destino:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(files_frame, textvariable=self.output_dir_var, width=50).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )
        ttk.Button(files_frame, text="Selecionar", command=self.select_output_dir).grid(
            row=1, column=2, sticky=tk.W, padx=5, pady=5
        )
        ttk.Checkbutton(files_frame, text="Pular existentes", variable=self.skip_existing_var).grid(
            row=1, column=3, sticky=tk.W, padx=5, pady=5
        )

        # Seção: Lista de arquivos e progresso
        list_frame = ttk.LabelFrame(tab, text="Arquivos para Traduzir", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.files_tree = ttk.Treeview(
            list_frame,
            columns=("file", "status", "progress"),
            show="headings",
            height=8,
        )
        self.files_tree.heading("file", text="Arquivo")
        self.files_tree.heading("status", text="Status")
        self.files_tree.heading("progress", text="Progresso")
        self.files_tree.column("file", width=600, anchor=tk.W)
        self.files_tree.column("status", width=150, anchor=tk.W)
        self.files_tree.column("progress", width=100, anchor=tk.E)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.files_tree.bind("<<TreeviewSelect>>", self.on_file_select)

        files_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        files_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_tree.configure(yscrollcommand=files_scroll.set)

        # Botões de ação
        actions_frame = ttk.Frame(tab, padding=10)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(actions_frame, text="Carregar Pasta", command=self.load_folder).pack(
            side=tk.LEFT, padx=5
        )
        self.translate_btn = ttk.Button(
            actions_frame, text="Traduzir Selecionados", command=self.translate_selected_files
        )
        self.translate_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Traduzir Todos", command=self.translate_all_files).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(actions_frame, text="Limpar Lista", command=self.clear_file_list).pack(
            side=tk.LEFT, padx=5
        )

        # Progress bar
        progress_frame = ttk.Frame(tab, padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(progress_frame, textvariable=self.eta_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(progress_frame, textvariable=self.file_progress_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(progress_frame, textvariable=self.spinner_var).pack(side=tk.LEFT, padx=5)

    def _create_claude_settings_tab(self) -> None:
        """Aba de configurações do Claude"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🤖 Claude API")

        # Instruções
        info_frame = ttk.LabelFrame(tab, text="Configuração da API Anthropic", padding=15)
        info_frame.pack(fill=tk.X, padx=20, pady=20)

        info_text = """Para usar o Claude:
1. Acesse console.anthropic.com e crie uma conta
2. Gere uma API key (começa com sk-ant-api03-...)
3. Cole a API key abaixo e teste a conexão"""

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

        # API Key
        api_frame = ttk.LabelFrame(tab, text="API Key", padding=15)
        api_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.api_key_var = tk.StringVar(value=self.config.get("claude_api_key", ""))
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=70, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5)

        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            api_frame,
            text="Mostrar",
            variable=self.show_key_var,
            command=lambda: self.api_key_entry.config(show="" if self.show_key_var.get() else "*"),
        ).grid(row=0, column=2, padx=5)

        ttk.Label(api_frame, text="Modelo:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar(value=self.config.get("claude_model", "claude-3-5-sonnet-20241022"))
        model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            values=[
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307",
            ],
            width=40,
            state="readonly",
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Button(api_frame, text="Testar Conexão", command=self.test_claude_connection).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=10
        )

        self.api_status_label = ttk.Label(api_frame, text="")
        self.api_status_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Preços
        pricing_frame = ttk.LabelFrame(tab, text="Preços (por 1M tokens)", padding=15)
        pricing_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        pricing_text = """Sonnet 3.5 (Recomendado): $3.00 input / $15.00 output (Cache: $0.30 read)
Opus 3 (Mais Poderoso):   $15.00 input / $75.00 output (Cache: $1.50 read)
Haiku 3 (Mais Rápido):    $0.25 input / $1.25 output (Cache: $0.03 read)

Com cache, traduções seguintes economizam ~90% no input!"""

        ttk.Label(pricing_frame, text=pricing_text, justify=tk.LEFT, font=("Consolas", 9)).pack(
            anchor=tk.W
        )

        # Botão salvar
        save_frame = ttk.Frame(tab, padding=10)
        save_frame.pack(fill=tk.X, padx=20)

        ttk.Button(save_frame, text="Salvar Configurações", command=self.save_claude_settings).pack(
            side=tk.RIGHT, padx=5
        )

    def _create_monitoring_tab(self) -> None:
        """Aba de monitoramento de uso de tokens"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Monitoramento")

        # Resumo
        summary_frame = ttk.LabelFrame(tab, text="Resumo de Uso", padding=15)
        summary_frame.pack(fill=tk.X, padx=20, pady=20)

        self.today_label = ttk.Label(summary_frame, text="Hoje: Carregando...")
        self.today_label.pack(anchor=tk.W, pady=5)

        self.month_label = ttk.Label(summary_frame, text="Este Mês: Carregando...")
        self.month_label.pack(anchor=tk.W, pady=5)

        # Histórico
        history_frame = ttk.LabelFrame(tab, text="Histórico (últimos 30 dias)", padding=15)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.usage_tree = ttk.Treeview(
            history_frame,
            columns=("date", "input", "output", "cache_read", "cost", "calls"),
            show="headings",
            height=15,
        )
        self.usage_tree.heading("date", text="Data")
        self.usage_tree.heading("input", text="Input Tokens")
        self.usage_tree.heading("output", text="Output Tokens")
        self.usage_tree.heading("cache_read", text="Cache Read")
        self.usage_tree.heading("cost", text="Custo (USD)")
        self.usage_tree.heading("calls", text="Chamadas")
        for col in ("date", "input", "output", "cache_read", "cost", "calls"):
            self.usage_tree.column(col, width=120, anchor=tk.CENTER)
        self.usage_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        usage_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.usage_tree.yview)
        usage_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.usage_tree.configure(yscrollcommand=usage_scroll.set)

        # Botões
        btn_frame = ttk.Frame(tab, padding=10)
        btn_frame.pack(fill=tk.X, padx=20)

        ttk.Button(btn_frame, text="Atualizar Dados", command=self.refresh_monitoring).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Exportar CSV", command=self.export_usage_csv).pack(
            side=tk.LEFT, padx=5
        )

    def _create_dictionary_tab(self) -> None:
        """Aba de gestão do dicionário"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📚 Dicionário")

        # Controles superiores
        controls_frame = ttk.Frame(tab, padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(controls_frame, text="Categoria:").pack(side=tk.LEFT, padx=5)
        self.dict_category_var = tk.StringVar()
        category_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.dict_category_var,
            values=["Todos", "empresa", "tecnico", "sigla", "local", "banco", "unidade"],
            width=20,
            state="readonly",
        )
        category_combo.set("Todos")
        category_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(controls_frame, text="Filtrar", command=self.filter_dictionary).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(controls_frame, text="Adicionar Termo", command=self.add_dictionary_term).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(controls_frame, text="Importar CSV", command=self.import_dictionary).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(controls_frame, text="Exportar CSV", command=self.export_dictionary).pack(
            side=tk.LEFT, padx=5
        )

        # Tabela de termos
        dict_frame = ttk.Frame(tab)
        dict_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.dict_tree = ttk.Treeview(
            dict_frame,
            columns=("term", "translation", "langs", "category", "uses"),
            show="headings",
            height=25,
        )
        self.dict_tree.heading("term", text="Termo")
        self.dict_tree.heading("translation", text="Tradução")
        self.dict_tree.heading("langs", text="Idiomas")
        self.dict_tree.heading("category", text="Categoria")
        self.dict_tree.heading("uses", text="Usos")
        self.dict_tree.column("term", width=200, anchor=tk.W)
        self.dict_tree.column("translation", width=200, anchor=tk.W)
        self.dict_tree.column("langs", width=100, anchor=tk.CENTER)
        self.dict_tree.column("category", width=150, anchor=tk.W)
        self.dict_tree.column("uses", width=80, anchor=tk.CENTER)
        self.dict_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        dict_scroll = ttk.Scrollbar(dict_frame, orient=tk.VERTICAL, command=self.dict_tree.yview)
        dict_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.dict_tree.configure(yscrollcommand=dict_scroll.set)

        # Carregar dados iniciais
        self.load_dictionary()

    def _create_preferences_tab(self) -> None:
        """Aba de preferências gerais"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙ Preferências")

        # LibreTranslate
        libre_frame = ttk.LabelFrame(tab, text="LibreTranslate", padding=15)
        libre_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(libre_frame, text="URL do servidor:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.libre_url_var = tk.StringVar(
            value=self.config.get("libretranslate_url", "http://102.211.186.44/translate")
        )
        ttk.Entry(libre_frame, textvariable=self.libre_url_var, width=60).grid(
            row=0, column=1, padx=5, pady=5
        )

        ttk.Label(libre_frame, text="Timeout (segundos):").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.libre_timeout_var = tk.DoubleVar(value=self.config.get("libretranslate_timeout", 15.0))
        ttk.Spinbox(libre_frame, from_=5.0, to=60.0, textvariable=self.libre_timeout_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )

        # MySQL
        mysql_frame = ttk.LabelFrame(tab, text="Banco de Dados MySQL", padding=15)
        mysql_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(mysql_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.mysql_host_var = tk.StringVar(value=self.config.get("mysql_host", "102.211.186.44"))
        ttk.Entry(mysql_frame, textvariable=self.mysql_host_var, width=30).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(mysql_frame, text="Porta:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        self.mysql_port_var = tk.IntVar(value=self.config.get("mysql_port", 3306))
        ttk.Spinbox(mysql_frame, from_=1, to=65535, textvariable=self.mysql_port_var, width=10).grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(mysql_frame, text="Database:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.mysql_db_var = tk.StringVar(value=self.config.get("mysql_database", "tradutor_db"))
        ttk.Entry(mysql_frame, textvariable=self.mysql_db_var, width=30).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(mysql_frame, text="Usuário:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.mysql_user_var = tk.StringVar(value=self.config.get("mysql_user", "root"))
        ttk.Entry(mysql_frame, textvariable=self.mysql_user_var, width=30).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(mysql_frame, text="Senha:").grid(row=2, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        self.mysql_pass_var = tk.StringVar(value=self.config.get("mysql_password", ""))
        ttk.Entry(mysql_frame, textvariable=self.mysql_pass_var, width=20, show="*").grid(
            row=2, column=3, sticky=tk.W, padx=5, pady=5
        )

        # Botão salvar
        save_frame = ttk.Frame(tab, padding=10)
        save_frame.pack(fill=tk.X, padx=20)

        ttk.Button(save_frame, text="Salvar Preferências", command=self.save_preferences).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(save_frame, text="Testar Conexão MySQL", command=self.test_mysql_connection).pack(
            side=tk.RIGHT, padx=5
        )

    def _apply_theme(self) -> None:
        """Aplica tema visual"""
        self.root.configure(bg="#f5f7fb")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#f5f7fb")
        style.configure("TLabelframe", background="#f5f7fb", foreground="#0f172a")
        style.configure(
            "TLabelframe.Label",
            background="#f5f7fb",
            foreground="#0f172a",
            font=("Bahnschrift", 10, "bold"),
        )
        style.configure("TLabel", background="#f5f7fb", foreground="#0f172a")
        style.configure(
            "Header.TLabel",
            background="#f5f7fb",
            foreground="#0f172a",
            font=("Bahnschrift", 16, "bold"),
        )
        style.configure(
            "Subheader.TLabel",
            background="#f5f7fb",
            foreground="#64748b",
            font=("Bahnschrift", 10, "bold"),
        )
        style.configure("TButton", background="#1d4ed8", foreground="#ffffff", padding=6)
        style.configure("TNotebook", background="#f5f7fb")
        style.configure("TNotebook.Tab", padding=(12, 6))

    def _on_close(self) -> None:
        """Salva configurações ao fechar"""
        self.root.destroy()

    # ========== Métodos de Tradução ==========

    def select_input_dir(self) -> None:
        """Seleciona pasta de origem"""
        path = filedialog.askdirectory(title="Pasta de origem")
        if path:
            self.input_dir_var.set(path)

    def select_output_dir(self) -> None:
        """Seleciona pasta de destino"""
        path = filedialog.askdirectory(title="Pasta de destino")
        if path:
            self.output_dir_var.set(path)

    def select_single_file(self) -> None:
        """Seleciona um único arquivo"""
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=(
                ("Documentos", "*.docx *.pptx *.ppsx *.xlsx *.xlsm *.txt *.pdf"),
                ("Todos", "*.*"),
            ),
        )
        if not file_path:
            return

        self.input_dir_var.set(os.path.dirname(file_path))
        self.folder_files = [file_path]
        self.files_tree.delete(*self.files_tree.get_children())
        self.file_iid_map.clear()

        rel = os.path.basename(file_path)
        iid = "0"
        self.files_tree.insert("", tk.END, iid=iid, values=(rel, "PENDENTE", "0%"))
        self.file_iid_map[file_path] = iid
        self.status_var.set(f"Arquivo selecionado: {rel}")

    def load_folder(self) -> None:
        """Carrega arquivos da pasta de origem"""
        root_dir = self.input_dir_var.get().strip()
        if not root_dir:
            messagebox.showwarning("Aviso", "Selecione a pasta de origem.")
            return

        output_dir = self.output_dir_var.get().strip()
        files = self._iter_supported_files(root_dir)
        if not files:
            messagebox.showinfo("Aviso", "Nenhum arquivo suportado encontrado.")
            return

        # Filtrar se skip_existing ativado
        filtered: List[str] = []
        for path in files:
            if output_dir and self.skip_existing_var.get():
                output_path = self._output_path_for(path, root_dir, output_dir)
                if os.path.exists(output_path):
                    continue
            filtered.append(path)

        self.folder_files = filtered
        self.files_tree.delete(*self.files_tree.get_children())
        self.file_iid_map.clear()

        for idx, path in enumerate(self.folder_files):
            rel = os.path.relpath(path, root_dir)
            iid = str(idx)
            self.files_tree.insert("", tk.END, iid=iid, values=(rel, "PENDENTE", "0%"))
            self.file_iid_map[path] = iid

        self.status_var.set(f"{len(self.folder_files)} arquivos carregados")

    def on_file_select(self, event: tk.Event) -> None:
        """Quando arquivo é selecionado na lista"""
        selection = list(self.files_tree.selection())
        if not selection:
            return

        path = self.folder_files[int(selection[0])]
        try:
            self.tokens = extract_tokens(path)
            self.status_var.set(f"{len(self.tokens)} tokens extraídos de {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Erro", f"Erro ao extrair tokens:\n{exc}")

    def translate_selected_files(self) -> None:
        """Traduz arquivos selecionados"""
        selection = list(self.files_tree.selection())
        if not selection:
            messagebox.showwarning("Aviso", "Selecione arquivos para traduzir.")
            return

        selected_files = [self.folder_files[int(iid)] for iid in selection]
        self._translate_files(selected_files)

    def translate_all_files(self) -> None:
        """Traduz todos os arquivos da lista"""
        if not self.folder_files:
            messagebox.showwarning("Aviso", "Nenhum arquivo na lista.")
            return

        self._translate_files(self.folder_files)

    def _translate_files(self, files: List[str]) -> None:
        """Traduz lista de arquivos"""
        root_dir = self.input_dir_var.get().strip()
        output_dir = self.output_dir_var.get().strip()

        if not root_dir or not output_dir:
            messagebox.showwarning("Aviso", "Selecione pastas de origem e destino.")
            return

        source_lang = self.source_var.get()
        target_lang = self.target_var.get()
        use_ai = self.use_ai_var.get()
        use_dict = self.use_dictionary_var.get()

        # Verificar se Claude está disponível
        if use_ai and not self.claude_client:
            result = messagebox.askyesno(
                "Claude não configurado",
                "API key do Claude não está configurada.\n\n"
                "Deseja traduzir apenas com LibreTranslate?",
            )
            if not result:
                return
            use_ai = False

        self._set_busy(True)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(files)

        def task() -> List[str]:
            errors: List[str] = []
            start_time = time.time()

            for idx, file_path in enumerate(files, start=1):
                try:
                    # Extrair tokens
                    tokens = extract_tokens(file_path)

                    # Carregar dicionário
                    dictionary = {}
                    if use_dict and self.db:
                        dictionary = self.db.get_dictionary(source_lang, target_lang)

                    # Traduzir documento
                    if use_ai and self.claude_client:
                        # Usar Claude para tradução
                        tokens_data = [
                            {"location": t.location, "text": t.text}
                            for t in tokens
                            if not t.skip
                        ]

                        if tokens_data:
                            # Verificar cache primeiro
                            cache_key = f"{file_path}|{source_lang}|{target_lang}"
                            cached = self.cache.get(cache_key, source_lang, target_lang)

                            if cached:
                                # Usar cache
                                translations = json.loads(cached)
                                usage_stats = {"input_tokens": 0, "output_tokens": 0, "cost": 0}
                            else:
                                # Traduzir com Claude
                                translations, usage_stats = self.claude_client.translate_document(
                                    tokens_data, source_lang, target_lang, dictionary
                                )

                                # Salvar no cache
                                self.cache.set(
                                    cache_key,
                                    source_lang,
                                    target_lang,
                                    json.dumps(translations),
                                )

                                # Registrar uso de tokens
                                if self.db:
                                    self.db.log_token_usage(
                                        device_id=1,  # TODO: obter device_id real
                                        input_tokens=usage_stats.get("input_tokens", 0),
                                        output_tokens=usage_stats.get("output_tokens", 0),
                                        cache_creation_tokens=usage_stats.get("cache_creation_tokens", 0),
                                        cache_read_tokens=usage_stats.get("cache_read_tokens", 0),
                                        cost=usage_stats.get("cost", 0),
                                        model=self.model_var.get(),
                                        provider="claude",
                                    )

                            # Aplicar traduções
                            trans_map = {t["location"]: t["translation"] for t in translations}
                            for token in tokens:
                                if token.location in trans_map:
                                    token.translation = trans_map[token.location]

                    else:
                        # Usar LibreTranslate
                        texts_to_translate = [t.text for t in tokens if not t.skip]
                        if texts_to_translate and self.libre_client:
                            translations = self.libre_client.translate_batch(
                                texts_to_translate, source_lang, target_lang
                            )

                            # Aplicar traduções
                            trans_idx = 0
                            for token in tokens:
                                if not token.skip:
                                    token.translation = translations[trans_idx]
                                    trans_idx += 1

                    # Exportar documento traduzido
                    output_path = self._output_path_for(file_path, root_dir, output_dir)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    export_translated_document(file_path, tokens, output_path)

                    # Atualizar UI
                    elapsed = time.time() - start_time
                    avg = elapsed / idx
                    remaining = avg * (len(files) - idx)
                    eta_text = f"ETA: {int(remaining)}s"

                    self.root.after(0, self._update_file_progress, file_path, idx, eta_text)

                except Exception as exc:
                    errors.append(f"{os.path.basename(file_path)}: {exc}")

            return errors

        def on_success(errors: List[str]) -> None:
            self._set_busy(False)
            if errors:
                messagebox.showerror(
                    "Erros",
                    f"{len(errors)} arquivos falharam:\n\n" + "\n".join(errors[:5]),
                )
            else:
                messagebox.showinfo("Sucesso", f"{len(files)} arquivos traduzidos com sucesso!")

            # Atualizar monitoramento
            self.refresh_monitoring()

        def on_error(exc: Exception) -> None:
            self._set_busy(False)
            messagebox.showerror("Erro", f"Erro ao traduzir:\n{exc}")

        self._run_in_thread(task, on_success, on_error)

    def _update_file_progress(self, file_path: str, current: int, eta: str) -> None:
        """Atualiza progresso de tradução"""
        self.progress_bar["value"] = current
        iid = self.file_iid_map.get(file_path)
        if iid:
            self.files_tree.set(iid, column="status", value="OK")
            self.files_tree.set(iid, column="progress", value="100%")
        self.eta_var.set(eta)
        self.file_progress_var.set(f"Arquivo: {os.path.basename(file_path)}")

    def clear_file_list(self) -> None:
        """Limpa lista de arquivos"""
        self.folder_files.clear()
        self.file_iid_map.clear()
        self.files_tree.delete(*self.files_tree.get_children())
        self.status_var.set("Lista limpa")

    # ========== Métodos de Configuração ==========

    def test_claude_connection(self) -> None:
        """Testa conexão com Claude"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Aviso", "Insira a API key primeiro.")
            return

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=self.model_var.get(),
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )

            self.api_status_label.config(
                text="✓ Conexão bem-sucedida!", foreground="green"
            )
            messagebox.showinfo("Sucesso", "API Key válida e funcionando!")

        except Exception as e:
            self.api_status_label.config(text=f"✗ Erro: {str(e)[:50]}", foreground="red")
            messagebox.showerror("Erro", f"Falha ao conectar:\n{e}")

    def save_claude_settings(self) -> None:
        """Salva configurações do Claude"""
        self.config.set("claude_api_key", self.api_key_var.get().strip())
        self.config.set("claude_model", self.model_var.get())

        # Reinicializar cliente
        self._init_clients()

        messagebox.showinfo("Sucesso", "Configurações do Claude salvas!")

    def test_mysql_connection(self) -> None:
        """Testa conexão com MySQL"""
        # Salvar temporariamente as configurações
        self.config.set("mysql_host", self.mysql_host_var.get())
        self.config.set("mysql_port", self.mysql_port_var.get())
        self.config.set("mysql_database", self.mysql_db_var.get())
        self.config.set("mysql_user", self.mysql_user_var.get())
        self.config.set("mysql_password", self.mysql_pass_var.get())

        try:
            # Tentar conectar
            test_db = Database(self.config)
            test_db.close()
            messagebox.showinfo("Sucesso", "Conexão com MySQL estabelecida!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao conectar ao MySQL:\n{e}")

    def save_preferences(self) -> None:
        """Salva preferências gerais"""
        self.config.set("libretranslate_url", self.libre_url_var.get().strip())
        self.config.set("libretranslate_timeout", self.libre_timeout_var.get())
        self.config.set("mysql_host", self.mysql_host_var.get())
        self.config.set("mysql_port", self.mysql_port_var.get())
        self.config.set("mysql_database", self.mysql_db_var.get())
        self.config.set("mysql_user", self.mysql_user_var.get())
        self.config.set("mysql_password", self.mysql_pass_var.get())

        # Reinicializar clientes
        self._init_clients()

        messagebox.showinfo("Sucesso", "Preferências salvas!")

    # ========== Métodos de Monitoramento ==========

    def refresh_monitoring(self) -> None:
        """Atualiza dados de monitoramento"""
        if not self.db:
            messagebox.showwarning("Aviso", "Banco de dados não conectado.")
            return

        try:
            # Obter dados de uso
            summary, daily_breakdown = self.db.get_token_usage(device_id=1, days=30)

            # Atualizar resumo
            today_text = (
                f"Hoje: {summary.get('today_input', 0):,} input | "
                f"{summary.get('today_output', 0):,} output | "
                f"${summary.get('today_cost', 0):.4f}"
            )
            self.today_label.config(text=today_text)

            month_text = (
                f"Este Mês: {summary.get('total_input', 0):,} input | "
                f"{summary.get('total_output', 0):,} output | "
                f"${summary.get('total_cost', 0):.2f}"
            )
            self.month_label.config(text=month_text)

            # Atualizar tabela
            self.usage_tree.delete(*self.usage_tree.get_children())
            for entry in daily_breakdown:
                self.usage_tree.insert(
                    "",
                    tk.END,
                    values=(
                        entry["date"],
                        f"{entry['input_tokens']:,}",
                        f"{entry['output_tokens']:,}",
                        f"{entry['cache_read_tokens']:,}",
                        f"${entry['cost']:.4f}",
                        entry["calls"],
                    ),
                )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados:\n{e}")

    def export_usage_csv(self) -> None:
        """Exporta dados de uso para CSV"""
        # TODO: Implementar exportação
        messagebox.showinfo("Info", "Exportação de CSV será implementada")

    # ========== Métodos de Dicionário ==========

    def load_dictionary(self) -> None:
        """Carrega dicionário do banco de dados"""
        if not self.db:
            return

        try:
            # Carregar todos os termos
            terms = self.db.search_dictionary()

            self.dict_tree.delete(*self.dict_tree.get_children())
            for term in terms:
                self.dict_tree.insert(
                    "",
                    tk.END,
                    values=(
                        term["term"],
                        term["translation"],
                        f"{term['source_lang']} → {term['target_lang']}",
                        term["category"] or "-",
                        term["usage_count"],
                    ),
                )

        except Exception as e:
            print(f"Erro ao carregar dicionário: {e}")

    def filter_dictionary(self) -> None:
        """Filtra dicionário por categoria"""
        if not self.db:
            return

        category = self.dict_category_var.get()
        if category == "Todos":
            category = None

        try:
            terms = self.db.search_dictionary(category=category)

            self.dict_tree.delete(*self.dict_tree.get_children())
            for term in terms:
                self.dict_tree.insert(
                    "",
                    tk.END,
                    values=(
                        term["term"],
                        term["translation"],
                        f"{term['source_lang']} → {term['target_lang']}",
                        term["category"] or "-",
                        term["usage_count"],
                    ),
                )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao filtrar:\n{e}")

    def add_dictionary_term(self) -> None:
        """Adiciona novo termo ao dicionário"""
        # TODO: Implementar diálogo de adição
        messagebox.showinfo("Info", "Adição de termos será implementada")

    def import_dictionary(self) -> None:
        """Importa termos de CSV"""
        # TODO: Implementar importação
        messagebox.showinfo("Info", "Importação de CSV será implementada")

    def export_dictionary(self) -> None:
        """Exporta dicionário para CSV"""
        # TODO: Implementar exportação
        messagebox.showinfo("Info", "Exportação de CSV será implementada")

    # ========== Métodos Auxiliares ==========

    def _set_busy(self, busy: bool) -> None:
        """Define estado de ocupado"""
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.translate_btn.config(state=state)

        if busy:
            self._start_spinner()
        else:
            self._stop_spinner()

    def _start_spinner(self) -> None:
        """Inicia spinner de carregamento"""
        if self._spinner_running:
            return
        self._spinner_running = True
        self._spin_frame = 0
        self._spin_step()

    def _spin_step(self) -> None:
        """Passo do spinner"""
        if not self._spinner_running:
            self.spinner_var.set("")
            return
        frames = ["|", "/", "-", "\\"]
        self.spinner_var.set(f"{frames[self._spin_frame % len(frames)]}")
        self._spin_frame += 1
        self.root.after(120, self._spin_step)

    def _stop_spinner(self) -> None:
        """Para spinner"""
        self._spinner_running = False

    def _run_in_thread(self, func, on_success, on_error) -> None:
        """Executa função em thread separada"""

        def worker() -> None:
            try:
                result = func()
            except Exception as exc:
                self.root.after(0, on_error, exc)
                return
            self.root.after(0, on_success, result)

        threading.Thread(target=worker, daemon=True).start()

    def _iter_supported_files(self, root_dir: str) -> List[str]:
        """Itera arquivos suportados em diretório"""
        supported = {".docx", ".pptx", ".ppsx", ".xlsx", ".xlsm", ".txt", ".pdf"}
        files: List[str] = []
        for base, _, filenames in os.walk(root_dir):
            for name in filenames:
                ext = os.path.splitext(name)[1].lower()
                if ext in supported:
                    files.append(os.path.join(base, name))
        return files

    def _output_path_for(self, source_path: str, root_dir: str, output_dir: str) -> str:
        """Gera caminho de saída para arquivo traduzido"""
        rel = os.path.relpath(source_path, root_dir)
        base, ext = os.path.splitext(rel)
        if ext.lower() == ".pdf":
            out_rel = f"{base}_traduzido.docx"
        else:
            out_rel = f"{base}_traduzido{ext}"
        return os.path.join(output_dir, out_rel)
