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

try:
    from .extractor import extract_tokens
    from .token_guard import TokenGuard
    from .translator import export_translated_document
    from .utils import Token, merge_tokens
    from .config_manager import ConfigManager
    from .libretranslate_client import LibreTranslateClient
    from .claude_client import ClaudeClient
    from .openai_client import OpenAIClient
    from .database import Database
    from .translation_cache import TranslationCache
    from .progress_window import ProgressWindow
    from .review_window import ReviewWindow
    from .realtime_translation_window import RealTimeTranslationWindow
    from .batch_translation_window import BatchTranslationWindow
    from .pdf_conversion_window import PDFConversionWindow
    from .history_manager import HistoryManager
except ImportError:
    from extractor import extract_tokens
    from token_guard import TokenGuard
    from translator import export_translated_document
    from utils import Token, merge_tokens
    from config_manager import ConfigManager
    from libretranslate_client import LibreTranslateClient
    from claude_client import ClaudeClient
    from openai_client import OpenAIClient
    from database import Database
    from translation_cache import TranslationCache
    from progress_window import ProgressWindow
    from review_window import ReviewWindow
    from realtime_translation_window import RealTimeTranslationWindow
    from batch_translation_window import BatchTranslationWindow
    from pdf_conversion_window import PDFConversionWindow
    from history_manager import HistoryManager


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
        self.openai_client: Optional[OpenAIClient] = None
        self.db: Optional[Database] = None
        self.cache = TranslationCache()
        self.history_manager = HistoryManager()

        # Variáveis de estado
        self.source_var = tk.StringVar(value=self.config.get("default_source_lang", "en"))
        self.target_var = tk.StringVar(value=self.config.get("default_target_lang", "pt"))
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.skip_existing_var = tk.BooleanVar(value=True)
        self.use_ai_var = tk.BooleanVar(value=self.config.get("use_ai", False))
        self.ai_provider_var = tk.StringVar(value=self.config.get("ai_provider", "claude"))
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
        self.claude_client = None
        self.openai_client = None
        try:
            # LibreTranslate
            libre_url = self.config.get("libretranslate_url", "http://102.211.186.44:5000")
            libre_timeout = self.config.get("libretranslate_timeout", 30.0)
            self.libre_client = LibreTranslateClient(base_url=libre_url, timeout=libre_timeout)

            # Tentar carregar glossário do banco de dados para LibreTranslate
            try:
                if self.db:
                    source_lang = self.source_var.get() if hasattr(self, 'source_var') else "en"
                    target_lang = self.target_var.get() if hasattr(self, 'target_var') else "pt"
                    glossary = self.db.get_dictionary(source_lang, target_lang)

                    if glossary:
                        self.libre_client.set_glossary(glossary)
                        print(f"✓ Glossário carregado para LibreTranslate: {len(glossary)} termos")
            except Exception as e:
                print(f"⚠ Não foi possível carregar glossário do banco: {e}")
                print("  Continuando sem glossário...")

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
            # OpenAI (sÇü se tiver API key)
            openai_api_key = self.config.get("openai_api_key", "")
            if openai_api_key:
                openai_model = self.config.get("openai_model", "gpt-4o-mini")
                openai_base_url = self.config.get("openai_base_url", "https://api.openai.com/v1")
                openai_timeout = self.config.get("openai_timeout", 60.0)
                self.openai_client = OpenAIClient(
                    api_key=openai_api_key,
                    model=openai_model,
                    base_url=openai_base_url,
                    timeout=openai_timeout,
                )
        except Exception as e:
            print(f"ƒsÿ Erro ao inicializar OpenAI: {e}")

        try:
            # Database
            self.db = Database(self.config)

            # Atualizar glossário do LibreTranslate se banco foi conectado
            if self.libre_client and self.db:
                source_lang = self.source_var.get() if hasattr(self, 'source_var') else "en"
                target_lang = self.target_var.get() if hasattr(self, 'target_lang') else "pt"

                # Carregar glossário EN→PT
                glossary = self.db.get_dictionary(source_lang, target_lang)

                # IMPORTANTE: Também carregar correções PT→PT para pós-processamento
                # Isso corrige traduções mal feitas do LibreTranslate
                pt_corrections = self.db.get_dictionary("pt", "pt")
                if pt_corrections:
                    glossary.update(pt_corrections)
                    print(f"✓ Correções PT→PT adicionadas: {len(pt_corrections)} termos")

                if glossary:
                    self.libre_client.set_glossary(glossary)
                    print(f"✓ Glossário carregado para LibreTranslate: {len(glossary)} termos")

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
        self._create_openai_settings_tab()

        # Aba 3: Monitoramento
        self._create_monitoring_tab()

        # Aba 4: Histórico
        self._create_history_tab()

        # Aba 5: Dicionário
        self._create_dictionary_tab()

        # Aba 6: Preferências
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

        ttk.Checkbutton(lang_frame, text="Usar IA", variable=self.use_ai_var).grid(
            row=0, column=4, sticky=tk.W, padx=(30, 5), pady=5
        )
        ttk.Label(lang_frame, text="Provider:").grid(
            row=0, column=5, sticky=tk.W, padx=(10, 5), pady=5
        )
        provider_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.ai_provider_var,
            values=["claude", "openai"],
            width=12,
            state="readonly",
        )
        provider_combo.grid(row=0, column=6, sticky=tk.W, padx=(0, 5), pady=5)
        ttk.Checkbutton(lang_frame, text="Usar Dicionário", variable=self.use_dictionary_var).grid(
            row=1, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        # Checkbox de auto-save
        self.auto_save_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(lang_frame, text="💾 Salvar Automaticamente", variable=self.auto_save_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5
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
        ttk.Button(
            actions_frame,
            text="⚡ Carregar e Traduzir Pasta Completa",
            command=self.load_and_translate_folder,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
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
                "claude-sonnet-4-5-20250929",
                "claude-opus-4-5-20251101",
                "claude-haiku-4-5-20251001",
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-5-haiku-20241022",
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

        pricing_text = """Sonnet 3.5-20241022 (Recomendado): $3.00 input / $15.00 output
Sonnet 3.5-20240620:                $3.00 input / $15.00 output
Opus 3 (Mais Poderoso):             $15.00 input / $75.00 output
Sonnet 3 (Versão antiga):           $3.00 input / $15.00 output
Haiku 3 (Mais Rápido/Barato):       $0.25 input / $1.25 output

Com cache de prompts, traduções seguintes economizam ~90% no input!
Preços por 1 milhão de tokens."""

        ttk.Label(pricing_frame, text=pricing_text, justify=tk.LEFT, font=("Consolas", 9)).pack(
            anchor=tk.W
        )

        # Botão salvar
        save_frame = ttk.Frame(tab, padding=10)
        save_frame.pack(fill=tk.X, padx=20)

        ttk.Button(save_frame, text="Salvar Configurações", command=self.save_claude_settings).pack(
            side=tk.RIGHT, padx=5
        )

    def _create_openai_settings_tab(self) -> None:
        """Aba de configurações da OpenAI"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="OpenAI API")

        info_frame = ttk.LabelFrame(tab, text="Configuração da API OpenAI", padding=15)
        info_frame.pack(fill=tk.X, padx=20, pady=20)

        info_text = (
            "Para usar OpenAI:\n"
            "1. Acesse platform.openai.com e crie uma conta\n"
            "2. Gere uma API key\n"
            "3. Cole a API key abaixo e teste a conexão"
        )
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

        api_frame = ttk.LabelFrame(tab, text="API Key", padding=15)
        api_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.openai_api_key_var = tk.StringVar(value=self.config.get("openai_api_key", ""))
        self.openai_api_key_entry = ttk.Entry(api_frame, textvariable=self.openai_api_key_var, width=70, show="*")
        self.openai_api_key_entry.grid(row=0, column=1, padx=5, pady=5)

        self.openai_show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            api_frame,
            text="Mostrar",
            variable=self.openai_show_key_var,
            command=lambda: self.openai_api_key_entry.config(
                show="" if self.openai_show_key_var.get() else "*"
            ),
        ).grid(row=0, column=2, padx=5)

        ttk.Label(api_frame, text="Modelo:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.openai_model_var = tk.StringVar(value=self.config.get("openai_model", "gpt-4o-mini"))
        model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.openai_model_var,
            values=["gpt-4o-mini", "gpt-4o"],
            width=40,
            state="readonly",
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(api_frame, text="Base URL:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.openai_base_url_var = tk.StringVar(
            value=self.config.get("openai_base_url", "https://api.openai.com/v1")
        )
        ttk.Entry(api_frame, textvariable=self.openai_base_url_var, width=50).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(api_frame, text="Timeout (s):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.openai_timeout_var = tk.DoubleVar(value=self.config.get("openai_timeout", 60.0))
        ttk.Spinbox(
            api_frame,
            from_=5.0,
            to=120.0,
            textvariable=self.openai_timeout_var,
            width=10,
        ).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Button(api_frame, text="Testar Conexão", command=self.test_openai_connection).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=10
        )

        self.openai_status_label = ttk.Label(api_frame, text="")
        self.openai_status_label.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

        save_frame = ttk.Frame(tab, padding=10)
        save_frame.pack(fill=tk.X, padx=20)

        ttk.Button(save_frame, text="Salvar Configurações", command=self.save_openai_settings).pack(
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

    def _create_history_tab(self) -> None:
        """Aba de histórico de traduções"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📜 Histórico")

        # Estatísticas superiores
        stats_frame = ttk.LabelFrame(tab, text="Estatísticas", padding=15)
        stats_frame.pack(fill=tk.X, padx=20, pady=20)

        self.stats_label = ttk.Label(stats_frame, text="Carregando estatísticas...")
        self.stats_label.pack(anchor=tk.W, pady=5)

        # Filtros
        filter_frame = ttk.Frame(tab, padding=10)
        filter_frame.pack(fill=tk.X, padx=20)

        ttk.Label(filter_frame, text="Filtrar:").pack(side=tk.LEFT, padx=5)
        self.history_filter_var = tk.StringVar(value="Todos")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.history_filter_var,
            values=["Todos", "Em Andamento", "Concluídas", "Falhadas"],
            width=20,
            state="readonly",
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_history())

        ttk.Button(filter_frame, text="Atualizar", command=self.refresh_history).pack(
            side=tk.LEFT, padx=10
        )

        # Tabela de histórico
        history_list_frame = ttk.LabelFrame(tab, text="Traduções", padding=10)
        history_list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Treeview
        columns = ("timestamp", "status", "langs", "files", "progress", "output")
        self.history_tree = ttk.Treeview(
            history_list_frame,
            columns=columns,
            show="headings",
            height=15,
        )
        self.history_tree.heading("timestamp", text="Data/Hora")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("langs", text="Idiomas")
        self.history_tree.heading("files", text="Arquivos")
        self.history_tree.heading("progress", text="Progresso")
        self.history_tree.heading("output", text="Pasta Destino")

        self.history_tree.column("timestamp", width=150, anchor=tk.W)
        self.history_tree.column("status", width=120, anchor=tk.CENTER)
        self.history_tree.column("langs", width=100, anchor=tk.CENTER)
        self.history_tree.column("files", width=80, anchor=tk.CENTER)
        self.history_tree.column("progress", width=150, anchor=tk.E)
        self.history_tree.column("output", width=300, anchor=tk.W)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=scroll.set)

        # Botões de ação
        actions_frame = ttk.Frame(tab, padding=10)
        actions_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Button(
            actions_frame,
            text="▶️ Retomar Selecionada",
            command=self.resume_translation
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="📥 Baixar Arquivos",
            command=self.download_translation_files
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="🗑 Remover Selecionada",
            command=self.delete_selected_history
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="🧹 Limpar Concluídas",
            command=self.clear_completed_history
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="📊 Exportar Relatório",
            command=self.export_history_report
        ).pack(side=tk.LEFT, padx=5)

        # Carregar dados iniciais
        self.refresh_history()

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
            value=self.config.get("libretranslate_url", "http://102.211.186.44:5000")
        )
        ttk.Entry(libre_frame, textvariable=self.libre_url_var, width=60).grid(
            row=0, column=1, padx=5, pady=5
        )

        ttk.Label(libre_frame, text="Timeout (segundos):").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.libre_timeout_var = tk.DoubleVar(value=self.config.get("libretranslate_timeout", 30.0))
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

        # Nome da Empresa (NUNCA traduzir)
        company_frame = ttk.LabelFrame(tab, text="🏢 Proteção de Nome da Empresa", padding=15)
        company_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        info_label = ttk.Label(
            company_frame,
            text="⚠️ Configure o nome da sua empresa para NUNCA ser traduzido pelo Claude.\n"
                 "Isso garante que o nome apareça corretamente em todos os documentos traduzidos.",
            wraplength=700,
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W, pady=(0, 10))

        # Frame para label e entrada na mesma linha
        entry_frame = ttk.Frame(company_frame)
        entry_frame.pack(fill=tk.X, pady=5)

        ttk.Label(entry_frame, text="Nome da Empresa:").pack(side=tk.LEFT, padx=5)
        self.company_name_var = tk.StringVar(value=self.config.get("company_name", ""))
        company_entry = ttk.Entry(entry_frame, textvariable=self.company_name_var, width=60)
        company_entry.pack(side=tk.LEFT, padx=5)

        example_label = ttk.Label(
            company_frame,
            text="Exemplo: 'ACME Corporation', 'Minha Empresa Lda', etc.",
            foreground="#64748b",
            font=("Bahnschrift", 9)
        )
        example_label.pack(anchor=tk.W, padx=10, pady=(0, 10))

        # Checkbox para extrair nome do arquivo
        self.extract_company_from_filename_var = tk.BooleanVar(value=self.config.get("extract_company_from_filename", True))
        extract_check = ttk.Checkbutton(
            company_frame,
            text="📁 Extrair nome da empresa automaticamente do nome do arquivo",
            variable=self.extract_company_from_filename_var
        )
        extract_check.pack(anchor=tk.W, padx=10, pady=(0, 5))

        extract_help = ttk.Label(
            company_frame,
            text="Se ativado, o sistema extrai o nome da empresa do nome do arquivo\n"
                 "(ex: 'CONTACT MOÇAMBIQUE AGÊNCIA PRIVADA LDA - 0031629360_001.docx' → protege 'CONTACT MOÇAMBIQUE AGÊNCIA PRIVADA LDA')",
            foreground="#64748b",
            font=("Bahnschrift", 9),
            wraplength=700,
            justify=tk.LEFT
        )
        extract_help.pack(anchor=tk.W, padx=25, pady=(0, 5))

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
        style.configure("Accent.TButton", background="#059669", foreground="#ffffff", padding=8, font=("Bahnschrift", 9, "bold"))
        style.map("Accent.TButton", background=[("active", "#047857")])
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

    def _get_ai_context(self) -> Tuple[Optional[Any], str, str]:
        """Retorna (cliente, provider, modelo) conforme seleção atual."""
        provider = self.ai_provider_var.get()
        if provider == "openai":
            model = (
                self.openai_model_var.get()
                if hasattr(self, "openai_model_var")
                else self.config.get("openai_model", "gpt-4o-mini")
            )
            return self.openai_client, "openai", model

        model = (
            self.model_var.get()
            if hasattr(self, "model_var")
            else self.config.get("claude_model", "claude-3-5-sonnet-20241022")
        )
        return self.claude_client, "claude", model

    def _translate_files(self, files: List[str]) -> None:
        """
        Traduz lista de arquivos usando janelas apropriadas:
        - 1 arquivo: RealTimeTranslationWindow (tempo real com edição)
        - Múltiplos arquivos: BatchTranslationWindow (percentagem com pausa/retomada)
        """
        root_dir = self.input_dir_var.get().strip()
        output_dir = self.output_dir_var.get().strip()

        if not root_dir or not output_dir:
            messagebox.showwarning("Aviso", "Selecione pastas de origem e destino.")
            return

        source_lang = self.source_var.get()
        target_lang = self.target_var.get()
        use_ai = self.use_ai_var.get()
        use_dict = self.use_dictionary_var.get()

        ai_client, ai_provider, _ = self._get_ai_context()
        self.config.set("ai_provider", self.ai_provider_var.get())

        # Verificar se provider está disponível
        if use_ai and not ai_client:
            provider_name = "OpenAI" if ai_provider == "openai" else "Claude"
            result = messagebox.askyesno(
                f"{provider_name} não configurado",
                f"API key do {provider_name} não está configurada.\n\n"
                "Deseja traduzir apenas com LibreTranslate?",
            )
            if not result:
                return
            use_ai = False

        # Carregar dicionário se necessário
        dictionary = {}
        if use_dict and self.db:
            dictionary = self.db.get_dictionary(source_lang, target_lang)

        # Decidir qual janela usar
        if len(files) == 1:
            # Arquivo único - usar RealTimeTranslationWindow
            self._translate_single_file_realtime(
                files[0], source_lang, target_lang, use_ai, dictionary, output_dir, ai_client, ai_provider
            )
        else:
            # Múltiplos arquivos - usar BatchTranslationWindow
            self._translate_multiple_files_batch(
                files, source_lang, target_lang, use_ai, dictionary, root_dir, output_dir, ai_client, ai_provider
            )

    def _extract_company_name_from_filename(self, file_path: str) -> str:
        """
        Extrai o nome da empresa do nome do arquivo.

        Exemplos:
        - "CONTACT MOÇAMBIQUE AGÊNCIA PRIVADA DE EMPREGO LDA - 0031629360_001.docx"
          → "CONTACT MOÇAMBIQUE AGÊNCIA PRIVADA DE EMPREGO LDA"
        - "KERRY PROJECT LOGISTICS MOZAMBIQUE LDA - 0031620659_000.docx"
          → "KERRY PROJECT LOGISTICS MOZAMBIQUE LDA"
        """
        import re

        file_name = os.path.basename(file_path)
        # Remover extensão
        name_without_ext = os.path.splitext(file_name)[0]

        # Remover NUIT e código (padrão: - 0031629360_001 ou - 0031620659_000)
        name_clean = re.sub(r'\s*-\s*\d+_\d+\s*$', '', name_without_ext)
        name_clean = re.sub(r'\s*-\s*\d+\s+\d+\s*$', '', name_clean)

        # Substituir underscores por espaços
        name_clean = name_clean.replace('_', ' ')

        # Remover espaços múltiplos
        name_clean = ' '.join(name_clean.split())

        return name_clean.strip()

    def _translate_single_file_realtime(
        self,
        file_path: str,
        source_lang: str,
        target_lang: str,
        use_ai: bool,
        dictionary: Dict[str, str],
        output_dir: str,
        ai_client: Optional[Any],
        ai_provider: str
    ) -> None:
        """Traduz arquivo único com janela de tempo real"""
        try:
            # Extrair tokens
            tokens = extract_tokens(file_path)
            file_name = os.path.basename(file_path)

            # Função de tradução que será chamada pela janela
            def translate_func(texts: List[str]) -> List[str]:
                if use_ai and ai_client:
                    # Traduzir com Claude (usa configuração otimizada automaticamente)
                    tokens_data = [{"location": f"T{i}", "text": text} for i, text in enumerate(texts)]

                    # Extrair nome da empresa (se opção estiver ativada)
                    company_name = ""
                    if self.config.get("extract_company_from_filename", True):
                        company_name = self._extract_company_name_from_filename(file_path)
                        if company_name:
                            print(f"🏢 Nome da empresa (do arquivo): '{company_name}'")

                    # Se não extraiu do arquivo, usar configuração das preferências
                    if not company_name or not company_name.strip():
                        company_name = self.config.get("company_name", "")
                        if company_name:
                            print(f"🏢 Nome da empresa (das preferências): '{company_name}'")

                    # LOG para debug
                    if not company_name:
                        print("⚠️ Nenhum nome de empresa para proteger")

                    def on_progress(msg: str, percent: float):
                        self.root.after(
                            0,
                            lambda: self.status_var.set(
                                f"{ai_provider.upper()}: {percent:.0f}% - {msg}"
                            ),
                        )

                    ai_dictionary = {} if ai_provider != "openai" else None
                    translations, _ = ai_client.translate_document(
                        tokens_data,
                        source_lang,
                        target_lang,
                        ai_dictionary,
                        batch_size=None,  # Usa batch otimizado: 2000 segmentos para Haiku 3.5
                        progress_callback=on_progress,
                        use_parallel=(ai_provider == "openai"),
                        company_name=company_name  # Nome da empresa NUNCA traduzir
                    )

                    # CRÍTICO: Mapear traduções pela location para garantir ordem correta
                    # Claude pode dividir em batches e manter locations originais (T0, T14, T28, etc)
                    translation_map = {t["location"]: t["translation"] for t in translations}

                    # Garantir que TODAS as traduções estão presentes
                    result = []
                    missing_locations = []
                    for i, text in enumerate(texts):
                        location = f"T{i}"
                        if location in translation_map:
                            result.append(translation_map[location])
                        else:
                            # Tradução faltando - pode ser que batch foi cortado
                            missing_locations.append(location)
                            result.append(f"[ERRO: Tradução faltando para {location}]")

                    if missing_locations:
                        print(f"\n⚠️ AVISO: {len(missing_locations)} traduções faltando: {', '.join(missing_locations[:10])}")
                        if len(missing_locations) > 10:
                            print(f"   ... e mais {len(missing_locations) - 10} locations")

                    return result
                elif self.libre_client:
                    # Traduzir com LibreTranslate
                    return self.libre_client.translate_batch(texts, source_lang, target_lang)
                else:
                    raise Exception("Nenhum cliente de tradução disponível")

            # Callback quando tradução completa
            def on_complete(edited_tokens: List[Token]):
                try:
                    # Montar caminho de saída usando _output_path_for para garantir .docx
                    parent_dir = os.path.dirname(file_path)
                    output_path = self._output_path_for(file_path, parent_dir, output_dir)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # Exportar documento
                    export_translated_document(file_path, edited_tokens, output_path)

                    messagebox.showinfo(
                        "Sucesso",
                        f"✅ Arquivo traduzido e exportado:\n{output_path}"
                    )

                    self.refresh_monitoring()
                except Exception as e:
                    messagebox.showerror("Erro ao Exportar", str(e))

            # Mostrar janela de tradução em tempo real
            RealTimeTranslationWindow(
                self.root,
                tokens,
                translate_func,
                on_complete,
                file_name,
                history_manager=self.history_manager,
                source_lang=source_lang,
                target_lang=target_lang,
                output_dir=output_dir,
                file_path=file_path
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar arquivo:\n{e}")

    def _translate_multiple_files_batch(
        self,
        files: List[str],
        source_lang: str,
        target_lang: str,
        use_ai: bool,
        dictionary: Dict[str, str],
        root_dir: str,
        output_dir: str,
        ai_client: Optional[Any],
        ai_provider: str
    ) -> None:
        """Traduz múltiplos arquivos com janela de batch"""

        # Callback quando conversão de PDFs completa
        def on_conversion_complete(files_and_tokens: List[Tuple[str, List[Token]]]):
            if not files_and_tokens:
                messagebox.showwarning("Aviso", "Nenhum arquivo foi convertido com sucesso.")
                return

            # Continuar com tradução
            self._start_batch_translation(
                files_and_tokens,
                source_lang,
                target_lang,
                use_ai,
                dictionary,
                root_dir,
                output_dir,
                ai_client,
                ai_provider,
            )

        # Mostrar janela de conversão de PDFs
        PDFConversionWindow(
            self.root,
            files,
            extract_tokens,
            on_conversion_complete
        )

    def _start_batch_translation(
        self,
        files_and_tokens: List[Tuple[str, List[Token]]],
        source_lang: str,
        target_lang: str,
        use_ai: bool,
        dictionary: Dict[str, str],
        root_dir: str,
        output_dir: str,
        ai_client: Optional[Any],
        ai_provider: str
    ) -> None:
        """Inicia tradução em batch após conversão de PDFs"""
        try:

            # Função de tradução que será chamada pela janela
            def translate_func(file_path: str, texts: List[str]) -> List[str]:
                if use_ai and ai_client:
                    # Traduzir com Claude (usa configuração otimizada automaticamente)
                    tokens_data = [{"location": f"T{i}", "text": text} for i, text in enumerate(texts)]

                    # Extrair nome da empresa (se opção estiver ativada)
                    company_name = ""
                    if self.config.get("extract_company_from_filename", True):
                        company_name = self._extract_company_name_from_filename(file_path)
                        if company_name:
                            print(f"🏢 Nome da empresa (do arquivo): '{company_name}'")

                    # Se não extraiu do arquivo, usar configuração das preferências
                    if not company_name or not company_name.strip():
                        company_name = self.config.get("company_name", "")
                        if company_name:
                            print(f"🏢 Nome da empresa (das preferências): '{company_name}'")

                    # LOG para debug
                    if not company_name:
                        print("⚠️ Nenhum nome de empresa para proteger")

                    def on_progress(msg: str, percent: float):
                        self.root.after(
                            0,
                            lambda: self.status_var.set(
                                f"{ai_provider.upper()}: {percent:.0f}% - {msg}"
                            ),
                        )

                    ai_dictionary = {} if ai_provider != "openai" else None
                    translations, _ = ai_client.translate_document(
                        tokens_data,
                        source_lang,
                        target_lang,
                        ai_dictionary,
                        batch_size=None,  # Usa batch otimizado: 2000 segmentos para Haiku 3.5
                        progress_callback=on_progress,
                        use_parallel=(ai_provider == "openai"),
                        company_name=company_name  # Nome da empresa NUNCA traduzir
                    )

                    # CRÍTICO: Mapear traduções pela location para garantir ordem correta
                    # Claude pode dividir em batches e manter locations originais (T0, T14, T28, etc)
                    translation_map = {t["location"]: t["translation"] for t in translations}

                    # Garantir que TODAS as traduções estão presentes
                    result = []
                    missing_locations = []
                    for i, text in enumerate(texts):
                        location = f"T{i}"
                        if location in translation_map:
                            result.append(translation_map[location])
                        else:
                            # Tradução faltando - pode ser que batch foi cortado
                            missing_locations.append(location)
                            result.append(f"[ERRO: Tradução faltando para {location}]")

                    if missing_locations:
                        print(f"\n⚠️ AVISO: {len(missing_locations)} traduções faltando: {', '.join(missing_locations[:10])}")
                        if len(missing_locations) > 10:
                            print(f"   ... e mais {len(missing_locations) - 10} locations")

                    return result
                elif self.libre_client:
                    # Traduzir com LibreTranslate
                    return self.libre_client.translate_batch(texts, source_lang, target_lang)
                else:
                    raise Exception("Nenhum cliente de tradução disponível")

            # Callback quando tradução completa
            def on_complete(translated_files: List[Tuple[str, List[Token]]]):
                try:
                    exported_count = 0
                    export_errors = []

                    for file_path, tokens in translated_files:
                        try:
                            # Montar caminho de saída usando _output_path_for para garantir .docx
                            output_path = self._output_path_for(file_path, root_dir, output_dir)
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)

                            # Exportar documento
                            export_translated_document(file_path, tokens, output_path)
                            exported_count += 1

                        except Exception as e:
                            export_errors.append(f"{os.path.basename(file_path)}: {e}")

                    # Mostrar resultado
                    if export_errors:
                        messagebox.showerror(
                            "Erros na Exportação",
                            f"✅ {exported_count} arquivos exportados\n"
                            f"❌ {len(export_errors)} falharam:\n\n" + "\n".join(export_errors[:5])
                        )
                    else:
                        messagebox.showinfo(
                            "Sucesso",
                            f"✅ {exported_count} arquivos traduzidos e exportados!"
                        )

                    self.refresh_monitoring()

                except Exception as e:
                    messagebox.showerror("Erro ao Exportar", str(e))

            # Mostrar janela de tradução em batch
            BatchTranslationWindow(
                self.root,
                files_and_tokens,
                translate_func,
                on_complete,
                auto_save=self.auto_save_var.get(),
                history_manager=self.history_manager,
                source_lang=source_lang,
                target_lang=target_lang,
                output_dir=output_dir
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar arquivos:\n{e}")

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

    def load_and_translate_folder(self) -> None:
        """Carrega pasta e traduz todos os arquivos COM progresso detalhado"""
        root_dir = self.input_dir_var.get().strip()
        output_dir = self.output_dir_var.get().strip()

        if not root_dir or not output_dir:
            messagebox.showwarning("Aviso", "Selecione pastas de origem e destino.")
            return

        source_lang = self.source_var.get()
        target_lang = self.target_var.get()
        use_ai = self.use_ai_var.get()
        use_dict = self.use_dictionary_var.get()

        # Verificar provider se necessário
        if use_ai and not ai_client:
            provider_name = "OpenAI" if ai_provider == "openai" else "Claude"
            result = messagebox.askyesno(
                f"{provider_name} não configurado",
                f"API key do {provider_name} não está configurada.\n\n"
                "Deseja traduzir apenas com LibreTranslate?",
            )
            if not result:
                return
            use_ai = False

        # Criar janela de progresso
        progress_window = ProgressWindow(self.root, "Carregando e Traduzindo Pasta")
        progress_window.show_cancel_button()

        def task() -> Tuple[List[str], List[str]]:
            """Retorna (sucessos, erros)"""
            errors: List[str] = []
            successes: List[str] = []

            try:
                # Etapa 1: Descobrir arquivos
                self.root.after(0, lambda: progress_window.update(
                    5, "Escaneando pasta...", f"Procurando arquivos em: {root_dir}"
                ))

                files = self._iter_supported_files(root_dir)
                if not files:
                    return [], ["Nenhum arquivo suportado encontrado"]

                # Filtrar se skip_existing ativado
                filtered: List[str] = []
                for path in files:
                    if progress_window.is_cancelled():
                        return successes, ["Operação cancelada pelo usuário"]

                    if output_dir and self.skip_existing_var.get():
                        output_path = self._output_path_for(path, root_dir, output_dir)
                        if os.path.exists(output_path):
                            continue
                    filtered.append(path)

                files = filtered
                total_files = len(files)

                if total_files == 0:
                    return [], ["Todos os arquivos já foram traduzidos"]

                self.root.after(0, lambda: progress_window.update(
                    10, f"Encontrados {total_files} arquivos", "Iniciando tradução..."
                ))

                # Etapa 2: Traduzir cada arquivo
                start_time = time.time()

                for idx, file_path in enumerate(files, start=1):
                    if progress_window.is_cancelled():
                        return successes, errors + ["Operação cancelada pelo usuário"]

                    try:
                        rel_name = os.path.relpath(file_path, root_dir)

                        # Atualizar UI
                        base_progress = 10 + ((idx - 1) / total_files * 85)
                        file_step_weight = 85 / total_files

                        # Callback de progresso para extração
                        def on_extraction_progress(msg: str, percent: float):
                            current_progress = base_progress + (percent / 100 * file_step_weight * 0.3)
                            details = f"Arquivo {idx}/{total_files}: {rel_name} - {msg}"
                            self.root.after(0, lambda p=current_progress, d=details: progress_window.update(
                                p, f"Processando arquivo {idx}/{total_files}...", d
                            ))

                        # Extrair tokens
                        on_extraction_progress("Iniciando extração...", 0)
                        tokens = extract_tokens(file_path, on_extraction_progress)
                        on_extraction_progress("Extração concluída!", 100)

                        # Carregar dicionário
                        dictionary = {}
                        if use_dict and self.db:
                            dictionary = self.db.get_dictionary(source_lang, target_lang)

                        # Traduzir
                        current_progress = base_progress + (file_step_weight * 0.3)
                        self.root.after(0, lambda p=current_progress: progress_window.update(
                            p, f"Traduzindo arquivo {idx}/{total_files}...",
                            f"{rel_name} - {len(tokens)} textos para traduzir"
                        ))

                        if use_ai and ai_client:
                            # Usar Claude
                            tokens_data = [
                                {"location": t.location, "text": t.text}
                                for t in tokens
                                if not t.skip
                            ]

                            if tokens_data:
                                cache_key = f"{file_path}|{source_lang}|{target_lang}|{ai_provider}|{ai_model}"
                                cached = self.cache.get(cache_key, source_lang, target_lang)

                                if cached:
                                    translations = json.loads(cached)
                                    usage_stats = {"input_tokens": 0, "output_tokens": 0, "cost": 0}
                                else:
                                    # Callback de progresso para tradução Claude
                                    def on_translation_progress(msg: str, percent: float):
                                        details = f"Arquivo {idx}/{total_files}: {rel_name} - {msg}"
                                        print(f"{ai_provider.upper()}: {percent:.0f}% - {msg}")
                                        self.root.after(0, lambda d=details: progress_window.update(
                                            base_progress + (file_step_weight * 0.6),
                                            f"Traduzindo arquivo {idx}/{total_files}...",
                                            d
                                        ))

                                    # Extrair nome da empresa (se opção estiver ativada)
                                    company_name = ""
                                    if self.config.get("extract_company_from_filename", True):
                                        company_name = self._extract_company_name_from_filename(file_path)
                                        if company_name:
                                            print(f"🏢 Nome da empresa (do arquivo): '{company_name}'")

                                    # Se não extraiu do arquivo, usar configuração das preferências
                                    if not company_name or not company_name.strip():
                                        company_name = self.config.get("company_name", "")
                                        if company_name:
                                            print(f"🏢 Nome da empresa (das preferências): '{company_name}'")

                                    # LOG para debug
                                    if not company_name:
                                        print("⚠️ Nenhum nome de empresa para proteger")

                                    ai_dictionary = {} if ai_provider != "openai" else None
                                    translations, usage_stats = ai_client.translate_document(
                                        tokens_data,
                                        source_lang,
                                        target_lang,
                                        ai_dictionary,
                                        batch_size=None,  # Usa batch otimizado: 2000 segmentos para Haiku 3.5
                                        progress_callback=on_translation_progress,
                                        use_parallel=(ai_provider == "openai"),
                                        company_name=company_name  # Nome da empresa NUNCA traduzir
                                    )
                                    self.cache.set(
                                        cache_key, source_lang, target_lang, json.dumps(translations)
                                    )

                                    if self.db:
                                        self.db.log_token_usage(
                                            device_id=1,
                                            input_tokens=usage_stats.get("input_tokens", 0),
                                            output_tokens=usage_stats.get("output_tokens", 0),
                                            cache_creation_tokens=usage_stats.get("cache_creation_tokens", 0),
                                            cache_read_tokens=usage_stats.get("cache_read_tokens", 0),
                                            cost=usage_stats.get("cost", 0),
                                            model=ai_model,
                                            provider=ai_provider,
                                        )

                                trans_map = {t["location"]: t["translation"] for t in translations}
                                for token in tokens:
                                    if token.location in trans_map:
                                        token.translation = trans_map[token.location]

                        else:
                            # Usar LibreTranslate
                            texts_to_translate = [t.text for t in tokens if not t.skip]
                            if texts_to_translate and self.libre_client:
                                print(f"  LibreTranslate: traduzindo {len(texts_to_translate)} textos...")
                                self.root.after(0, lambda: progress_window.update(
                                    base_progress + (file_step_weight * 0.5),
                                    f"Traduzindo arquivo {idx}/{total_files}...",
                                    f"LibreTranslate: {len(texts_to_translate)} textos"
                                ))

                                translations = self.libre_client.translate_batch(
                                    texts_to_translate, source_lang, target_lang
                                )

                                print(f"  LibreTranslate: ✓ Recebeu {len(translations)} traduções")

                                trans_idx = 0
                                for token in tokens:
                                    if not token.skip:
                                        token.translation = translations[trans_idx]
                                        trans_idx += 1

                        # Exportar
                        current_progress = base_progress + (file_step_weight * 0.7)
                        self.root.after(0, lambda p=current_progress: progress_window.update(
                            p, f"Exportando arquivo {idx}/{total_files}...",
                            f"{rel_name} - Salvando documento traduzido"
                        ))

                        output_path = self._output_path_for(file_path, root_dir, output_dir)
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        export_translated_document(file_path, tokens, output_path)

                        successes.append(rel_name)

                        # Calcular ETA
                        elapsed = time.time() - start_time
                        avg = elapsed / idx
                        remaining = avg * (total_files - idx)
                        eta_text = f"ETA: {int(remaining)}s"

                        current_progress = base_progress + file_step_weight
                        self.root.after(0, lambda p=current_progress, e=eta_text: progress_window.update(
                            p, f"Arquivo {idx}/{total_files} concluído!", e
                        ))

                    except Exception as exc:
                        errors.append(f"{os.path.basename(file_path)}: {exc}")

                # Finalizar
                self.root.after(0, lambda: progress_window.update(
                    100, "Concluído!", f"{len(successes)} arquivos traduzidos com sucesso"
                ))

                return successes, errors

            except Exception as e:
                return successes, errors + [f"Erro geral: {str(e)}"]

        def on_success(result: Tuple[List[str], List[str]]) -> None:
            successes, errors = result
            progress_window.close()
            self._set_busy(False)

            # Recarregar lista
            self.load_folder()

            if errors:
                messagebox.showwarning(
                    "Concluído com Erros",
                    f"{len(successes)} arquivos traduzidos com sucesso\n"
                    f"{len(errors)} arquivos falharam:\n\n" + "\n".join(errors[:5]),
                )
            else:
                messagebox.showinfo(
                    "Sucesso!",
                    f"✓ {len(successes)} arquivos traduzidos com sucesso!"
                )

            self.refresh_monitoring()

        def on_error(exc: Exception) -> None:
            progress_window.close()
            self._set_busy(False)
            messagebox.showerror("Erro", f"Erro ao processar:\n{exc}")

        self._set_busy(True)
        self._run_in_thread(task, on_success, on_error)

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

    def test_openai_connection(self) -> None:
        """Testa conexão com OpenAI"""
        api_key = self.openai_api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Aviso", "Insira a API key primeiro.")
            return

        try:
            client = OpenAIClient(
                api_key=api_key,
                model=self.openai_model_var.get(),
                base_url=self.openai_base_url_var.get().strip(),
                timeout=self.openai_timeout_var.get(),
            )

            if client.test_connection():
                self.openai_status_label.config(text="✓ Conexão bem-sucedida!", foreground="green")
                messagebox.showinfo("Sucesso", "API Key válida e funcionando!")
            else:
                raise Exception("Falha ao obter resposta da OpenAI.")

        except Exception as e:
            self.openai_status_label.config(text=f"✗ Erro: {str(e)[:50]}", foreground="red")
            messagebox.showerror("Erro", f"Falha ao conectar:\n{e}")

    def save_openai_settings(self) -> None:
        """Salva configurações da OpenAI"""
        self.config.set("openai_api_key", self.openai_api_key_var.get().strip())
        self.config.set("openai_model", self.openai_model_var.get())
        self.config.set("openai_base_url", self.openai_base_url_var.get().strip())
        self.config.set("openai_timeout", self.openai_timeout_var.get())

        # Reinicializar cliente
        self._init_clients()

        messagebox.showinfo("Sucesso", "Configurações da OpenAI salvas!")

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
        self.config.set("company_name", self.company_name_var.get().strip())
        self.config.set("extract_company_from_filename", self.extract_company_from_filename_var.get())

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
        """
        Gera caminho de saída para arquivo traduzido.
        SEMPRE exporta como .docx, independente do formato de entrada.
        """
        rel = os.path.relpath(source_path, root_dir)
        base, ext = os.path.splitext(rel)
        # SEMPRE exportar como .docx
        out_rel = f"{base}_traduzido.docx"
        return os.path.join(output_dir, out_rel)

    # ========== Métodos de Histórico ==========

    def refresh_history(self) -> None:
        """Atualiza lista de histórico"""
        try:
            # Obter filtro
            filter_value = self.history_filter_var.get()

            # Carregar traduções
            if filter_value == "Em Andamento":
                translations = self.history_manager.get_in_progress_translations()
            elif filter_value == "Concluídas":
                translations = self.history_manager.get_completed_translations()
            elif filter_value == "Falhadas":
                all_trans = self.history_manager.get_all_translations()
                translations = [t for t in all_trans if t.get("status") == "failed"]
            else:
                translations = self.history_manager.get_all_translations()

            # Atualizar estatísticas
            stats = self.history_manager.get_statistics()
            stats_text = (
                f"Total: {stats['total']} traduções | "
                f"Em Andamento: {stats['in_progress']} | "
                f"Concluídas: {stats['completed']} | "
                f"Falhadas: {stats['failed']}\n"
                f"Total de Arquivos Traduzidos: {stats['total_files_completed']:,} | "
                f"Total de Tokens: {stats['total_tokens_translated']:,}"
            )
            self.stats_label.config(text=stats_text)

            # Limpar e popular tabela
            self.history_tree.delete(*self.history_tree.get_children())

            for trans in translations:
                # Formatar timestamp
                timestamp = trans.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp_str = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        timestamp_str = timestamp[:16]
                else:
                    timestamp_str = "N/A"

                # Status com emoji
                status = trans.get("status", "unknown")
                status_icons = {
                    "in_progress": "🔄 Em Andamento",
                    "completed": "✅ Concluída",
                    "failed": "❌ Falhada"
                }
                status_str = status_icons.get(status, status)

                # Idiomas
                langs = f"{trans.get('source_lang', '?')} → {trans.get('target_lang', '?')}"

                # Arquivos
                total_files = trans.get("total_files", 0)

                # Progresso
                total_tokens = trans.get("total_tokens", 0)
                translated_tokens = trans.get("translated_tokens", 0)
                if total_tokens > 0:
                    percent = int((translated_tokens / total_tokens) * 100)
                    progress_str = f"{translated_tokens}/{total_tokens} ({percent}%)"
                else:
                    progress_str = "N/A"

                # Output
                output_dir = trans.get("output_dir", "N/A")

                # Inserir na árvore com ID da tradução
                self.history_tree.insert(
                    "",
                    tk.END,
                    iid=trans.get("id"),
                    values=(timestamp_str, status_str, langs, total_files, progress_str, output_dir)
                )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar histórico:\n{e}")

    def resume_translation(self) -> None:
        """Retoma tradução selecionada"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma tradução para retomar.")
            return

        translation_id = selection[0]
        translation = self.history_manager.get_translation(translation_id)

        if not translation:
            messagebox.showerror("Erro", "Tradução não encontrada.")
            return

        if translation.get("status") != "in_progress":
            result = messagebox.askyesno(
                "Tradução já finalizada",
                "Esta tradução já foi finalizada. Deseja reprocessá-la?"
            )
            if not result:
                return

        try:
            # Extrair dados da tradução
            files_data = translation.get("files", [])
            source_lang = translation.get("source_lang")
            target_lang = translation.get("target_lang")
            output_dir = translation.get("output_dir")

            # Reconstruir lista de arquivos
            files = [f.get("path") for f in files_data if f.get("path")]

            if not files:
                messagebox.showerror("Erro", "Nenhum arquivo encontrado nesta tradução.")
                return

            # Configurar variáveis de tradução
            self.source_var.set(source_lang)
            self.target_var.set(target_lang)
            self.output_dir_var.set(output_dir)

            # Iniciar tradução
            messagebox.showinfo(
                "Retomando Tradução",
                f"Retomando tradução de {len(files)} arquivo(s).\n"
                f"Idiomas: {source_lang} → {target_lang}"
            )

            self._translate_files(files)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao retomar tradução:\n{e}")

    def download_translation_files(self) -> None:
        """Baixa arquivos de tradução concluída"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma tradução para baixar.")
            return

        translation_id = selection[0]
        translation = self.history_manager.get_translation(translation_id)

        if not translation:
            messagebox.showerror("Erro", "Tradução não encontrada.")
            return

        if translation.get("status") != "completed":
            messagebox.showwarning(
                "Aviso",
                "Esta tradução ainda não foi concluída."
            )
            return

        try:
            # Obter arquivos de saída
            output_files = self.history_manager.export_completed_files(translation_id)

            if not output_files:
                messagebox.showwarning(
                    "Aviso",
                    "Nenhum arquivo de saída encontrado.\n"
                    "Os arquivos podem ter sido movidos ou deletados."
                )
                return

            # Perguntar onde salvar
            save_dir = filedialog.askdirectory(
                title="Selecione pasta para salvar arquivos traduzidos"
            )

            if not save_dir:
                return

            # Copiar arquivos
            import shutil
            copied = 0

            for file_path in output_files:
                if os.path.exists(file_path):
                    dest_path = os.path.join(save_dir, os.path.basename(file_path))
                    shutil.copy2(file_path, dest_path)
                    copied += 1

            messagebox.showinfo(
                "Sucesso",
                f"✅ {copied} arquivo(s) copiado(s) para:\n{save_dir}"
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao baixar arquivos:\n{e}")

    def delete_selected_history(self) -> None:
        """Remove tradução selecionada do histórico"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma tradução para remover.")
            return

        result = messagebox.askyesno(
            "Confirmar Remoção",
            "Tem certeza que deseja remover esta tradução do histórico?\n\n"
            "ATENÇÃO: Isso NÃO deletará os arquivos traduzidos."
        )

        if not result:
            return

        translation_id = selection[0]
        if self.history_manager.delete_translation(translation_id):
            messagebox.showinfo("Sucesso", "Tradução removida do histórico.")
            self.refresh_history()
        else:
            messagebox.showerror("Erro", "Não foi possível remover a tradução.")

    def clear_completed_history(self) -> None:
        """Limpa traduções concluídas do histórico"""
        result = messagebox.askyesno(
            "Confirmar Limpeza",
            "Tem certeza que deseja remover TODAS as traduções concluídas do histórico?\n\n"
            "ATENÇÃO: Isso NÃO deletará os arquivos traduzidos."
        )

        if not result:
            return

        self.history_manager.clear_completed_translations()
        messagebox.showinfo("Sucesso", "Traduções concluídas removidas do histórico.")
        self.refresh_history()

    def export_history_report(self) -> None:
        """Exporta relatório de histórico"""
        try:
            import csv

            # Selecionar local para salvar
            file_path = filedialog.asksaveasfilename(
                title="Exportar Relatório",
                defaultextension=".csv",
                filetypes=(("CSV", "*.csv"), ("Todos", "*.*"))
            )

            if not file_path:
                return

            # Obter todas as traduções
            translations = self.history_manager.get_all_translations()

            # Escrever CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Cabeçalho
                writer.writerow([
                    "Data/Hora",
                    "Status",
                    "Idioma Origem",
                    "Idioma Destino",
                    "Total Arquivos",
                    "Total Tokens",
                    "Tokens Traduzidos",
                    "Progresso (%)",
                    "Pasta Saída",
                    "Erro"
                ])

                # Dados
                for trans in translations:
                    timestamp = trans.get("timestamp", "")
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            timestamp_str = timestamp
                    else:
                        timestamp_str = "N/A"

                    total_tokens = trans.get("total_tokens", 0)
                    translated_tokens = trans.get("translated_tokens", 0)
                    progress = int((translated_tokens / total_tokens) * 100) if total_tokens > 0 else 0

                    writer.writerow([
                        timestamp_str,
                        trans.get("status", ""),
                        trans.get("source_lang", ""),
                        trans.get("target_lang", ""),
                        trans.get("total_files", 0),
                        total_tokens,
                        translated_tokens,
                        progress,
                        trans.get("output_dir", ""),
                        trans.get("error_message", "")
                    ])

            messagebox.showinfo("Sucesso", f"Relatório exportado para:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar relatório:\n{e}")
