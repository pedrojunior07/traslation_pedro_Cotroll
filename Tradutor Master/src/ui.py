import json
import os
import platform
import threading
import time
from datetime import datetime
from math import ceil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

from api_client import (
    APIError,
    ai_build_glossary,
    ai_evaluate_texts,
    ai_translate_text,
    get_languages,
    get_usage,
    register_device,
    translate_batch,
    translate_nllb,
    translate_nllb_batch,
    translate_text,
)
from extractor import extract_tokens
from token_guard import TokenGuard
from translator import export_translated_document
from utils import Token, merge_tokens


class TranslatorUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tradutor de Documentos")
        self.tokens: List[Token] = []
        self._selected_index: Optional[int] = None
        self.languages: List[dict] = []
        self._busy = False
        self.device_token: Optional[str] = None
        self.usage_snapshot: Dict[str, Any] = {}
        self.usage_status_var = tk.StringVar(value="-")
        self.days_status_var = tk.StringVar(value="-")
        self.license_status_var = tk.StringVar(value="-")
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.skip_existing_var = tk.BooleanVar(value=True)
        self.single_file_var = tk.BooleanVar(value=False)
        self.ai_translate_var = tk.BooleanVar(value=False)
        self.ai_evaluate_var = tk.BooleanVar(value=True)
        self.ai_glossary_var = tk.BooleanVar(value=False)
        self.batch_translate_var = tk.BooleanVar(value=True)
        self.translation_provider_var = tk.StringVar(value="libretranslate")  # libretranslate, nllb, both
        self.glossary: Dict[str, str] = {}
        self.eta_var = tk.StringVar(value="ETA: -")
        self.translation_time_var = tk.StringVar(value="Tempo: -")
        self.file_progress_var = tk.StringVar(value="Arquivo: -")
        self.files_count_var = tk.StringVar(value="Arquivos: -")
        self.folder_files: List[str] = []
        self.batch_files_order: List[str] = []
        self.batch_files_done: set[str] = set()
        self.file_iid_map: Dict[str, str] = {}
        self.spinner_var = tk.StringVar(value="")
        self._spinner_running = False
        self._apply_theme()
        self._build_layout()
        self._load_local_config()
        self.root.after(150, self._auto_start)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill=tk.X, padx=10, pady=(10, 0))
        ttk.Label(header, text="Tradutor Master", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header, text="Desktop", style="Subheader.TLabel").pack(side=tk.LEFT, padx=(8, 0))

        api_frame = ttk.LabelFrame(self.root, text="API e Licenca", padding=10)
        api_frame.pack(fill=tk.X, padx=10, pady=(6, 5))

        self.base_url_var = tk.StringVar(value="http://127.0.0.1:8000")
        ttk.Label(api_frame, text="Base URL:").grid(row=0, column=0, sticky=tk.W)
        self.base_url_entry = ttk.Entry(api_frame, textvariable=self.base_url_var, width=48)
        self.base_url_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 10))

        ttk.Label(api_frame, text="Licenca:").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self.license_key_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.license_key_var, width=32).grid(
            row=1, column=1, sticky=tk.W, padx=(5, 10), pady=(8, 0)
        )

        ttk.Label(api_frame, text="Device ID:").grid(row=1, column=2, sticky=tk.W, pady=(8, 0))
        self.device_id_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.device_id_var, width=24).grid(
            row=1, column=3, sticky=tk.W, pady=(8, 0)
        )

        ttk.Label(api_frame, text="Nome dispositivo:").grid(row=2, column=0, sticky=tk.W, pady=(8, 0))
        self.device_name_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.device_name_var, width=32).grid(
            row=2, column=1, sticky=tk.W, padx=(5, 10), pady=(8, 0)
        )

        default_device = os.environ.get("COMPUTERNAME") or platform.node()
        if default_device:
            if not self.device_id_var.get():
                self.device_id_var.set(default_device)
            if not self.device_name_var.get():
                self.device_name_var.set(default_device)

        self.register_device_btn = ttk.Button(api_frame, text="Registrar dispositivo", command=self.register_device)
        self.register_device_btn.grid(row=2, column=2, sticky=tk.W, pady=(8, 0))

        self.refresh_usage_btn = ttk.Button(api_frame, text="Atualizar status", command=self.refresh_usage)
        self.refresh_usage_btn.grid(row=2, column=3, sticky=tk.W, pady=(8, 0))

        ttk.Label(api_frame, text="De:").grid(row=3, column=0, sticky=tk.W, pady=(8, 0))
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(api_frame, textvariable=self.source_var, state="readonly", width=22)
        self.source_combo.grid(row=3, column=1, sticky=tk.W, padx=(5, 10), pady=(8, 0))
        self.source_combo.bind("<<ComboboxSelected>>", self.on_source_change)

        ttk.Label(api_frame, text="Para:").grid(row=3, column=2, sticky=tk.W, pady=(8, 0))
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(api_frame, textvariable=self.target_var, state="readonly", width=22)
        self.target_combo.grid(row=3, column=3, sticky=tk.W, pady=(8, 0))

        self.overwrite_var = tk.BooleanVar(value=False)
        self.overwrite_check = ttk.Checkbutton(
            api_frame, text="Sobrescrever traducoes existentes", variable=self.overwrite_var
        )
        self.overwrite_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        ttk.Label(api_frame, text="Quota:").grid(row=5, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Label(api_frame, textvariable=self.usage_status_var).grid(
            row=5, column=1, sticky=tk.W, padx=(5, 10), pady=(8, 0)
        )
        ttk.Label(api_frame, text="Dias restantes:").grid(row=5, column=2, sticky=tk.W, pady=(8, 0))
        ttk.Label(api_frame, textvariable=self.days_status_var).grid(
            row=5, column=3, sticky=tk.W, pady=(8, 0)
        )

        ttk.Label(api_frame, text="Licenca:").grid(row=6, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Label(api_frame, textvariable=self.license_status_var).grid(
            row=6, column=1, sticky=tk.W, padx=(5, 10), pady=(8, 0)
        )

        batch_frame = ttk.LabelFrame(self.root, text="Batch e Pastas", padding=10)
        batch_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

        ttk.Label(batch_frame, text="Origem:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(batch_frame, textvariable=self.input_dir_var, width=48).grid(
            row=0, column=1, sticky=tk.W, padx=(5, 10)
        )
        ttk.Button(batch_frame, text="Selecionar", command=self.select_input_dir).grid(
            row=0, column=2, sticky=tk.W
        )

        ttk.Label(batch_frame, text="Destino:").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(batch_frame, textvariable=self.output_dir_var, width=48).grid(
            row=1, column=1, sticky=tk.W, padx=(5, 10), pady=(8, 0)
        )
        ttk.Button(batch_frame, text="Selecionar", command=self.select_output_dir).grid(
            row=1, column=2, sticky=tk.W, pady=(8, 0)
        )

        ttk.Checkbutton(
            batch_frame, text="Pular arquivos ja traduzidos", variable=self.skip_existing_var
        ).grid(row=2, column=1, sticky=tk.W, pady=(8, 0))
        ttk.Button(
            batch_frame, text="Escolher arquivo", command=self.select_single_file
        ).grid(row=2, column=2, sticky=tk.W, pady=(8, 0))

        self.load_folder_btn = ttk.Button(batch_frame, text="Carregar pasta", command=self.load_folder)
        self.load_folder_btn.grid(
            row=2, column=3, sticky=tk.W, pady=(8, 0)
        )
        self.translate_folder_btn = ttk.Button(batch_frame, text="Traduzir pasta", command=self.translate_folder)
        self.translate_folder_btn.grid(
            row=2, column=4, sticky=tk.W, pady=(8, 0)
        )

        ai_frame = ttk.LabelFrame(self.root, text="IA e Qualidade", padding=10)
        ai_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

        ttk.Checkbutton(ai_frame, text="Traduzir com IA", variable=self.ai_translate_var).grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Checkbutton(ai_frame, text="Avaliar tokens com IA", variable=self.ai_evaluate_var).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )
        ttk.Checkbutton(ai_frame, text="Gerar glossario IA", variable=self.ai_glossary_var).grid(
            row=0, column=2, sticky=tk.W, padx=(10, 0)
        )
        ttk.Checkbutton(ai_frame, text="Tradução em lote (+ rápido)", variable=self.batch_translate_var).grid(
            row=0, column=3, sticky=tk.W, padx=(10, 0)
        )

        ttk.Label(ai_frame, text="Provider:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        provider_combo = ttk.Combobox(ai_frame, textvariable=self.translation_provider_var, state="readonly", width=12)
        provider_combo["values"] = ("libretranslate", "nllb", "ambos")
        provider_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 10))

        self.evaluate_ai_btn = ttk.Button(ai_frame, text="Avaliar agora", command=self.evaluate_tokens_ai)
        self.evaluate_ai_btn.grid(
            row=0, column=6, sticky=tk.W, padx=(10, 0)
        )
        self.glossary_ai_btn = ttk.Button(ai_frame, text="Criar glossario", command=self.build_glossary_ai)
        self.glossary_ai_btn.grid(
            row=0, column=7, sticky=tk.W, padx=(10, 0)
        )

        batch_list_frame = ttk.LabelFrame(self.root, text="Arquivos da pasta", padding=10)
        batch_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        self.files_list = ttk.Treeview(
            batch_list_frame,
            columns=("file", "status", "percent"),
            show="headings",
            height=8,
        )
        self.files_list.heading("file", text="Arquivo")
        self.files_list.heading("status", text="Status")
        self.files_list.heading("percent", text="%")
        self.files_list.column("file", width=420, anchor=tk.W)
        self.files_list.column("status", width=90, anchor=tk.W)
        self.files_list.column("percent", width=60, anchor=tk.E)
        self.files_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.files_list.bind("<<TreeviewSelect>>", self.on_file_select)
        list_scroll = ttk.Scrollbar(batch_list_frame, orient=tk.VERTICAL, command=self.files_list.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_list.configure(yscrollcommand=list_scroll.set)

        batch_controls = ttk.Frame(self.root, padding=6)
        batch_controls.pack(fill=tk.X, padx=10, pady=(0, 6))
        ttk.Button(batch_controls, text="Selecionar todos", command=self.select_all_files).pack(
            side=tk.LEFT
        )
        ttk.Button(batch_controls, text="Limpar selecao", command=self.clear_file_selection).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Label(batch_controls, textvariable=self.files_count_var).pack(side=tk.RIGHT)

        batch_progress = ttk.Frame(self.root, padding=6)
        batch_progress.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.batch_progress = ttk.Progressbar(batch_progress, length=360, mode="determinate")
        self.batch_progress.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(batch_progress, textvariable=self.eta_var).pack(side=tk.LEFT)
        ttk.Label(batch_progress, textvariable=self.translation_time_var, foreground="green").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(batch_progress, textvariable=self.file_progress_var).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(batch_progress, textvariable=self.spinner_var).pack(side=tk.LEFT, padx=(10, 0))

        controls = ttk.Frame(self.root, padding=10)
        controls.pack(fill=tk.X)

        load_btn = ttk.Button(controls, text="Carregar arquivo", command=self.load_file)
        load_btn.pack(side=tk.LEFT)

        self.translate_selected_btn = ttk.Button(
            controls, text="Traduzir selecionado", command=self.translate_selected
        )
        self.translate_selected_btn.pack(side=tk.LEFT, padx=(5, 0))

        self.translate_all_btn = ttk.Button(controls, text="Traduzir todos", command=self.translate_all)
        self.translate_all_btn.pack(side=tk.LEFT, padx=(5, 0))

        clear_btn = ttk.Button(controls, text="Limpar lista", command=self.clear_tokens)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))

        save_btn = ttk.Button(controls, text="Exportar CSV", command=self.export_csv)
        save_btn.pack(side=tk.LEFT, padx=(5, 0))

        export_doc_btn = ttk.Button(controls, text="Exportar documento", command=self.export_documents)
        export_doc_btn.pack(side=tk.LEFT, padx=(5, 0))

        self.status_var = tk.StringVar(value="Nenhum arquivo carregado.")
        status_lbl = ttk.Label(controls, textvariable=self.status_var)
        status_lbl.pack(side=tk.RIGHT)

        progress_frame = ttk.Frame(self.root, padding=10)
        progress_frame.pack(fill=tk.X)

        self.progress_total = ttk.Progressbar(progress_frame, length=360, mode="determinate")
        self.progress_total.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(progress_frame, textvariable=self.eta_var).pack(side=tk.LEFT)
        ttk.Label(progress_frame, textvariable=self.file_progress_var).pack(side=tk.RIGHT)

        columns = ("status", "original", "translation", "location")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=18)
        self.tree.heading("status", text="Status")
        self.tree.heading("original", text="Original")
        self.tree.heading("translation", text="Traducao")
        self.tree.heading("location", text="Local")
        self.tree.column("status", width=90, anchor=tk.W)
        self.tree.column("original", width=260, anchor=tk.W)
        self.tree.column("translation", width=200, anchor=tk.W)
        self.tree.column("location", width=160, anchor=tk.W)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        yscroll = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(fill=tk.X, padx=10, pady=(0, 10))

        form = ttk.Frame(self.root, padding=10)
        form.pack(fill=tk.X)

        self.original_var = tk.StringVar()
        ttk.Label(form, text="Texto selecionado:").pack(anchor=tk.W)
        self.original_entry = ttk.Entry(form, textvariable=self.original_var, state="readonly")
        self.original_entry.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(form, text="Traducao:").pack(anchor=tk.W)
        self.translation_var = tk.StringVar()
        self.translation_entry = ttk.Entry(form, textvariable=self.translation_var)
        self.translation_entry.pack(fill=tk.X, pady=(0, 5))

        self.save_translation_btn = ttk.Button(
            form, text="Salvar traducao", command=self.save_translation, state=tk.DISABLED
        )
        self.save_translation_btn.pack(anchor=tk.E)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for widget in (
            self.translate_selected_btn,
            self.translate_all_btn,
            self.register_device_btn,
            self.refresh_usage_btn,
            self.load_folder_btn,
            self.translate_folder_btn,
            self.evaluate_ai_btn,
            self.glossary_ai_btn,
        ):
            widget.config(state=state)
        if busy:
            self._start_spinner()
            self.save_translation_btn.config(state=tk.DISABLED)
        else:
            self._stop_spinner()
            self.save_translation_btn.config(
                state=tk.NORMAL if self._selected_index is not None else tk.DISABLED
            )

    def _start_spinner(self) -> None:
        if self._spinner_running:
            return
        self._spinner_running = True
        self._spin_frame = 0
        self._spin_step()

    def _spin_step(self) -> None:
        if not self._spinner_running:
            self.spinner_var.set("")
            return
        frames = ["|", "/", "-", "\\"]
        self.spinner_var.set(f"Carregando {frames[self._spin_frame % len(frames)]}")
        self._spin_frame += 1
        self.root.after(120, self._spin_step)

    def _stop_spinner(self) -> None:
        self._spinner_running = False

    def _apply_theme(self) -> None:
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
        style.configure("Header.TLabel", background="#f5f7fb", foreground="#0f172a", font=("Bahnschrift", 16, "bold"))
        style.configure("Subheader.TLabel", background="#f5f7fb", foreground="#64748b", font=("Bahnschrift", 10, "bold"))
        style.configure("TButton", background="#1d4ed8", foreground="#ffffff", padding=6)
        style.map(
            "TButton",
            background=[("active", "#2563eb"), ("pressed", "#1d4ed8")],
            foreground=[("disabled", "#94a3b8"), ("active", "#ffffff")],
        )
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#0f172a")
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#0f172a")
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#0f172a")
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#0f172a")])
        style.configure("TCheckbutton", background="#f5f7fb", foreground="#0f172a")
        style.configure("TProgressbar", background="#1d4ed8", troughcolor="#e2e8f0", bordercolor="#f5f7fb")

    def _run_in_thread(self, func, on_success, on_error) -> None:  # noqa: ANN001
        def worker() -> None:
            try:
                result = func()
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, on_error, exc)
                return
            self.root.after(0, on_success, result)

        threading.Thread(target=worker, daemon=True).start()

    def _get_language_code(self, value: str) -> str:
        return value.split(" - ", 1)[0].strip()

    def _get_language_entry(self, code: str) -> Optional[dict]:
        for lang in self.languages:
            if lang.get("code") == code:
                return lang
        return None

    def _estimate_units(self, text: str) -> int:
        clean = text.strip()
        if not clean:
            return 1
        return max(1, (len(clean) + 1799) // 1800)

    def _to_nllb_code(self, iso_code: str) -> str:
        """Convert ISO language code to NLLB-200 format."""
        mapping = {
            "en": "eng_Latn",
            "pt": "por_Latn",
            "fr": "fra_Latn",
            "es": "spa_Latn",
            "de": "deu_Latn",
            "it": "ita_Latn",
            "nl": "nld_Latn",
            "pl": "pol_Latn",
            "ru": "rus_Cyrl",
            "ar": "arb_Arab",
            "zh": "zho_Hans",
            "ja": "jpn_Jpan",
            "ko": "kor_Hang",
            "hi": "hin_Deva",
            "tr": "tur_Latn",
            "vi": "vie_Latn",
            "th": "tha_Thai",
            "id": "ind_Latn",
            "ms": "zsm_Latn",
            "sw": "swh_Latn",
            "he": "heb_Hebr",
            "cs": "ces_Latn",
            "da": "dan_Latn",
            "fi": "fin_Latn",
            "el": "ell_Grek",
            "hu": "hun_Latn",
            "no": "nob_Latn",
            "ro": "ron_Latn",
            "sk": "slk_Latn",
            "sv": "swe_Latn",
            "uk": "ukr_Cyrl",
            "bg": "bul_Cyrl",
            "ca": "cat_Latn",
            "hr": "hrv_Latn",
            "sr": "srp_Cyrl",
            "sl": "slv_Latn",
            "et": "est_Latn",
            "lv": "lvs_Latn",
            "lt": "lit_Latn",
            "fa": "pes_Arab",
            "ur": "urd_Arab",
            "bn": "ben_Beng",
            "ta": "tam_Taml",
            "te": "tel_Telu",
            "ml": "mal_Mlym",
            "kn": "kan_Knda",
            "mr": "mar_Deva",
            "gu": "guj_Gujr",
            "pa": "pan_Guru",
        }
        return mapping.get(iso_code.lower(), iso_code)

    def _token_status(self, token: Token) -> str:
        if token.skip:
            return "PULAR"
        if token.translation:
            return "OK"
        return "PENDENTE"

    def _display_source(self, token: Token) -> str:
        return token.source_original or token.source_file

    def _update_progress(self, current: int, total: int, eta: str, token_index: int, token: Token) -> None:
        self.progress_total["value"] = current
        self.status_var.set(f"Traduzindo {current}/{total}...")
        self.eta_var.set(eta)
        self.file_progress_var.set(f"Arquivo: {os.path.basename(self._display_source(token))}")
        self.tree.selection_set(str(token_index))
        self.tree.see(str(token_index))

    def _update_batch_progress(self, current: int, eta: str, path: str) -> None:
        self.batch_progress["value"] = current
        self.file_progress_var.set(f"Arquivo: {os.path.basename(path)}")
        self.eta_var.set(eta)
        iid = self.file_iid_map.get(path)
        if iid is not None:
            self.files_list.set(iid, column="status", value="OK")
            self.files_list.set(iid, column="percent", value="100%")

    def _update_token_row(self, token_index: int, token: Token) -> None:
        self.tree.set(str(token_index), column="translation", value=token.translation)
        self.tree.set(str(token_index), column="status", value=self._token_status(token))

    def _update_file_percent(self, path: str, percent: int) -> None:
        iid = self.file_iid_map.get(path)
        if iid is not None:
            self.files_list.set(iid, column="status", value="TRADUZINDO")
            self.files_list.set(iid, column="percent", value=f"{percent}%")

    def _config_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".tradutor_master.json")

    def _load_local_config(self) -> None:
        path = self._config_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return

        base_url = str(data.get("base_url") or "").strip()
        if base_url:
            self.base_url_var.set(base_url)
        license_key = str(data.get("license_key") or "").strip()
        if license_key and not self.license_key_var.get().strip():
            self.license_key_var.set(license_key)
        device_id = str(data.get("device_id") or "").strip()
        if device_id and not self.device_id_var.get().strip():
            self.device_id_var.set(device_id)
        device_name = str(data.get("device_name") or "").strip()
        if device_name and not self.device_name_var.get().strip():
            self.device_name_var.set(device_name)

    def _save_local_config(self) -> None:
        payload = {
            "base_url": self.base_url_var.get().strip(),
            "license_key": self.license_key_var.get().strip(),
            "device_id": self.device_id_var.get().strip(),
            "device_name": self.device_name_var.get().strip(),
        }
        try:
            with open(self._config_path(), "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=True, indent=2)
        except OSError:
            return

    def _on_close(self) -> None:
        self._save_local_config()
        self.root.destroy()

    def _auto_start(self) -> None:
        if self.device_token:
            self.load_languages()
            self.refresh_usage()
            return
        license_key = self.license_key_var.get().strip()
        device_id = self.device_id_var.get().strip()
        if license_key and device_id:
            self.register_device()

    def load_languages(self) -> None:
        base_url = self.base_url_var.get().strip()
        if not base_url:
            messagebox.showwarning("Aviso", "Informe a Base URL da API.")
            return
        if not self._ensure_device_token():
            return

        self.status_var.set("Carregando linguas...")
        self._set_busy(True)

        def task() -> List[dict]:
            return get_languages(base_url, self.device_token or "")

        def on_success(langs: List[dict]) -> None:
            self.languages = langs
            options = []
            for lang in langs:
                code = lang.get("code")
                name = lang.get("name") or code
                if isinstance(code, str):
                    options.append(f"{code} - {name}")
            options.sort()
            self.source_combo["values"] = options
            if options:
                self.source_combo.current(0)
                self.on_source_change()
                self.status_var.set(f"Linguas carregadas: {len(options)}")
            else:
                self.target_combo["values"] = []
                self.source_var.set("")
                self.target_var.set("")
                self.status_var.set("Nenhuma lingua retornada pela API.")
            self._set_busy(False)

        def on_error(exc: Exception) -> None:
            self._set_busy(False)
            messagebox.showerror("Erro", f"Nao foi possivel carregar linguas:\n{exc}")
            self.status_var.set("Falha ao carregar linguas.")

        self._run_in_thread(task, on_success, on_error)

    def on_source_change(self, event: tk.Event | None = None) -> None:  # noqa: ANN001
        value = self.source_var.get().strip()
        if not value:
            return
        source_code = self._get_language_code(value)
        entry = self._get_language_entry(source_code)
        if not entry:
            return
        targets = entry.get("targets") or []
        name_map = {lang.get("code"): lang.get("name") for lang in self.languages}
        target_options = []
        for code in targets:
            if not isinstance(code, str):
                continue
            name = name_map.get(code) or code
            target_options.append(f"{code} - {name}")
        target_options.sort()
        self.target_combo["values"] = target_options
        if target_options:
            self.target_combo.current(0)
        else:
            self.target_var.set("")

    def _ensure_languages_ready(self) -> bool:
        if not self.languages:
            messagebox.showwarning("Aviso", "Aguardando linguas da API. Verifique a licenca/status.")
            return False
        if not self.source_var.get() or not self.target_var.get():
            messagebox.showwarning("Aviso", "Selecione os idiomas de origem e destino.")
            return False
        return True

    def _ensure_device_token(self, force: bool = False) -> bool:
        if self.device_token and not force:
            return True
        base_url = self.base_url_var.get().strip()
        if not base_url:
            messagebox.showwarning("Aviso", "Informe a Base URL da API.")
            return False
        license_key = self.license_key_var.get().strip()
        device_id = self.device_id_var.get().strip()
        if not license_key or not device_id:
            messagebox.showwarning("Aviso", "Informe a licenca e o Device ID.")
            return False
        device_name = self.device_name_var.get().strip() or None
        try:
            self.device_token = register_device(base_url, license_key, device_id, device_name=device_name)
            self._save_local_config()
            self.status_var.set("Dispositivo registrado.")
        except APIError as exc:
            messagebox.showerror("Erro", self._format_license_error(str(exc)))
            return False
        return True

    def register_device(self) -> None:
        self.device_token = None
        if self._ensure_device_token(force=True):
            self.load_languages()
            self.refresh_usage()

    def refresh_usage(self) -> None:
        base_url = self.base_url_var.get().strip()
        if not base_url:
            messagebox.showwarning("Aviso", "Informe a Base URL da API.")
            return
        if not self._ensure_device_token():
            return

        self.status_var.set("Atualizando status...")
        self._set_busy(True)

        def task() -> dict:
            return get_usage(base_url, self.device_token or "")

        def on_success(data: dict) -> None:
            self.usage_snapshot = data
            quota_type = data.get("quota_type") or "UNITS"
            quota_limit = data.get("quota_limit")
            quota_remaining = data.get("quota_remaining")
            quota_period = data.get("quota_period") or ""
            if quota_remaining is None or quota_limit in (None, 0):
                quota_text = f"{quota_type} {quota_period}: ilimitado".strip()
            else:
                quota_text = f"{quota_type} {quota_period}: {quota_remaining}/{quota_limit}".strip()

            self.usage_status_var.set(quota_text)

            expires_at = data.get("license_expires_at")
            if isinstance(expires_at, str) and expires_at:
                try:
                    normalized = expires_at.replace("Z", "+00:00")
                    exp_dt = datetime.fromisoformat(normalized)
                    remaining = ceil((exp_dt.replace(tzinfo=None) - datetime.utcnow()).total_seconds() / 86400)
                    self.days_status_var.set(str(max(0, remaining)))
                except ValueError:
                    self.days_status_var.set("-")
            else:
                self.days_status_var.set("-")

            license_active = data.get("license_active")
            if license_active is True:
                self.license_status_var.set("Ativa")
            elif license_active is False:
                self.license_status_var.set("Inativa")
            else:
                self.license_status_var.set("-")

            self.status_var.set("Status atualizado.")
            self._set_busy(False)

        def on_error(exc: Exception) -> None:
            self._set_busy(False)
            messagebox.showerror("Erro", self._format_license_error(str(exc)))
            self.status_var.set("Falha ao atualizar status.")

        self._run_in_thread(task, on_success, on_error)

    def evaluate_tokens_ai(self) -> None:
        if not self.tokens:
            messagebox.showinfo("Aviso", "Nenhum token carregado.")
            return
        if not self._ensure_device_token():
            return
        if not self._ensure_languages_ready():
            return

        base_url = self.base_url_var.get().strip()
        source = self._get_language_code(self.source_var.get())
        target = self._get_language_code(self.target_var.get())
        self.status_var.set("Avaliando tokens com IA...")
        self._set_busy(True)

        def task() -> List[Dict[str, Any]]:
            return ai_evaluate_texts(base_url, self.device_token or "", [t.text for t in self.tokens], source, target)

        def on_success(items: List[Dict[str, Any]]) -> None:
            for token, item in zip(self.tokens, items):
                translatable = item.get("translatable")
                if isinstance(translatable, bool):
                    token.skip = not translatable
                    token.skip_reason = str(item.get("reason") or "")
            self.refresh_tree()
            self.status_var.set("Avaliacao IA concluida.")
            self._set_busy(False)

        def on_error(exc: Exception) -> None:
            self._set_busy(False)
            messagebox.showerror("Erro", f"Nao foi possivel avaliar com IA:\n{exc}")
            self.status_var.set("Falha ao avaliar com IA.")

        self._run_in_thread(task, on_success, on_error)

    def build_glossary_ai(self) -> None:
        if not self.tokens:
            messagebox.showinfo("Aviso", "Nenhum token carregado.")
            return
        if not self._ensure_device_token():
            return
        if not self._ensure_languages_ready():
            return

        base_url = self.base_url_var.get().strip()
        source = self._get_language_code(self.source_var.get())
        target = self._get_language_code(self.target_var.get())
        sample_texts = [t.text for t in self.tokens if t.text.strip()][:80]
        if not sample_texts:
            messagebox.showinfo("Aviso", "Nenhum texto valido para glossario.")
            return

        self.status_var.set("Gerando glossario IA...")
        self._set_busy(True)

        def task() -> Dict[str, str]:
            return ai_build_glossary(base_url, self.device_token or "", sample_texts, source, target)

        def on_success(glossary: Dict[str, str]) -> None:
            self.glossary = glossary
            self.status_var.set(f"Glossario pronto: {len(glossary)} termos.")
            self._set_busy(False)

        def on_error(exc: Exception) -> None:
            self._set_busy(False)
            messagebox.showerror("Erro", f"Nao foi possivel gerar glossario:\n{exc}")
            self.status_var.set("Falha ao gerar glossario.")

        self._run_in_thread(task, on_success, on_error)

    def translate_selected(self) -> None:
        if self._selected_index is None:
            messagebox.showinfo("Aviso", "Selecione um item para traduzir.")
            return
        if not self._ensure_languages_ready():
            return
        token = self.tokens[self._selected_index]
        if token.skip:
            messagebox.showinfo("Aviso", "Token marcado para pular.")
            return
        if token.translation and not self.overwrite_var.get():
            messagebox.showinfo("Aviso", "A traducao ja existe. Marque sobrescrever para atualizar.")
            return
        if not self._ensure_device_token():
            return
        self._translate_tokens([(self._selected_index, token)])

    def translate_all(self) -> None:
        if not self.tokens:
            messagebox.showinfo("Aviso", "Nenhum token para traduzir.")
            return
        if not self._ensure_languages_ready():
            return
        overwrite = self.overwrite_var.get()
        pending = [
            (idx, t)
            for idx, t in enumerate(self.tokens)
            if not t.skip and (overwrite or not t.translation)
        ]
        if not pending:
            messagebox.showinfo("Aviso", "Nao ha tokens pendentes de traducao.")
            return
        if not self._ensure_device_token():
            return
        self._translate_tokens(pending)

    def _translate_tokens(self, items: List[tuple[int, Token]], on_done=None) -> None:  # noqa: ANN001
        base_url = self.base_url_var.get().strip()
        source = self._get_language_code(self.source_var.get())
        target = self._get_language_code(self.target_var.get())
        total = len(items)

        guard = TokenGuard(enable_ai=False)

        self._set_busy(True)
        self.status_var.set(f"Traduzindo 0/{total}...")
        self.progress_total["value"] = 0
        self.progress_total["maximum"] = max(1, total)
        self.eta_var.set("ETA: -")

        def task() -> tuple[List[tuple[int, str]], List[str]]:
            if self.ai_evaluate_var.get():
                eval_items = ai_evaluate_texts(
                    base_url,
                    self.device_token or "",
                    [t.text for _, t in items],
                    source,
                    target,
                )
                for (_, token), item in zip(items, eval_items):
                    translatable = item.get("translatable")
                    if isinstance(translatable, bool):
                        token.skip = not translatable
                        token.skip_reason = str(item.get("reason") or "")
                self.root.after(0, self.refresh_tree)
            if self.ai_glossary_var.get() and not self.glossary:
                sample_texts = [t.text for _, t in items if t.text.strip()][:80]
                if sample_texts:
                    self.glossary = ai_build_glossary(
                        base_url, self.device_token or "", sample_texts, source, target
                    )
            usage = get_usage(base_url, self.device_token or "")
            self.usage_snapshot = usage
            quota_remaining = usage.get("quota_remaining")
            if quota_remaining is not None:
                needed_units = sum(self._estimate_units(t.text) for _, t in items if not t.skip)
                if quota_remaining <= 0 or needed_units > quota_remaining:
                    raise APIError(
                        f"Cota insuficiente. Necessario {needed_units}, restante {quota_remaining}."
                    )
            results: List[tuple[int, str]] = []
            errors: List[str] = []
            start_time = time.time()
            batch_items: List[tuple[int, int, Token]] = []  # Para rastrear tokens traduzidos em batch

            # Batch translation: traduz tokens simples (sem segmentos) de uma vez
            if self.batch_translate_var.get() and not self.ai_translate_var.get():
                # Coleta tokens que podem ser traduzidos em batch
                for idx, (token_index, token) in enumerate(items, start=1):
                    if token.skip:
                        continue
                    segments = guard.segment_text(token.text)
                    # Apenas tokens simples (sem segmentação ou 1 segmento traduzível)
                    if (not segments) or (len(segments) == 1 and segments[0].translatable):
                        batch_items.append((idx, token_index, token))

                if batch_items:
                    try:
                        # Traduz todos de uma vez
                        texts_to_translate = [token.text for _, _, token in batch_items]
                        total_units = sum(self._estimate_units(t) for t in texts_to_translate)

                        provider = self.translation_provider_var.get()
                        batch_start_time = time.time()

                        if provider == "nllb":
                            # Converte códigos para NLLB (en -> eng_Latn, pt -> por_Latn)
                            nllb_source = self._to_nllb_code(source)
                            nllb_target = self._to_nllb_code(target)
                            translations = translate_nllb_batch(
                                base_url,
                                self.device_token or "",
                                texts_to_translate,
                                nllb_source,
                                nllb_target,
                                units=total_units,
                            )
                        elif provider == "ambos":
                            # Traduz com os dois e compara
                            nllb_source = self._to_nllb_code(source)
                            nllb_target = self._to_nllb_code(target)

                            libre_start = time.time()
                            libre_translations = translate_batch(base_url, self.device_token or "", texts_to_translate, source, target, units=total_units)
                            libre_time = time.time() - libre_start

                            nllb_start = time.time()
                            nllb_translations = translate_nllb_batch(base_url, self.device_token or "", texts_to_translate, nllb_source, nllb_target, units=total_units)
                            nllb_time = time.time() - nllb_start

                            # Usa o mais rápido (ou permite escolher)
                            if libre_time < nllb_time:
                                translations = libre_translations
                                self.root.after(0, lambda: self.translation_time_var.set(f"⚡ LibreTranslate: {libre_time:.1f}s | NLLB: {nllb_time:.1f}s"))
                            else:
                                translations = nllb_translations
                                self.root.after(0, lambda: self.translation_time_var.set(f"⚡ NLLB: {nllb_time:.1f}s | Libre: {libre_time:.1f}s"))
                        else:
                            # LibreTranslate (padrão)
                            translations = translate_batch(
                                base_url,
                                self.device_token or "",
                                texts_to_translate,
                                source,
                                target,
                                units=total_units,
                            )

                        batch_elapsed = time.time() - batch_start_time
                        if provider != "ambos":
                            self.root.after(0, lambda: self.translation_time_var.set(f"Tempo: {batch_elapsed:.1f}s ({provider})"))

                        # Aplica resultados
                        for (idx, token_index, token), translated in zip(batch_items, translations):
                            results.append((token_index, translated))
                            # Atualiza progresso
                            elapsed = time.time() - start_time
                            avg = elapsed / max(1, idx)
                            remaining = avg * max(0, total - idx)
                            eta_text = f"ETA: {int(remaining)}s (batch)"
                            self.root.after(
                                0,
                                lambda i=idx, eta=eta_text, t_idx=token_index, tok=token: self._update_progress(
                                    i, total, eta, t_idx, tok
                                ),
                            )
                    except APIError as exc:
                        errors.append(f"Batch translation error: {exc}")
                        # Fallback para tradução individual se batch falhar
                        self.batch_translate_var.set(False)

            # Set de token_index já traduzidos em batch
            batch_translated_indexes = {token_index for _, token_index, _ in batch_items} if self.batch_translate_var.get() and not self.ai_translate_var.get() and batch_items else set()

            # Tradução individual (tokens restantes ou quando batch está desativado)
            for idx, (token_index, token) in enumerate(items, start=1):
                # Pula se já foi traduzido em batch
                if token_index in batch_translated_indexes:
                    continue
                if token.skip:
                    elapsed = time.time() - start_time
                    avg = elapsed / max(1, idx)
                    remaining = avg * max(0, total - idx)
                    eta_text = f"ETA: {int(remaining)}s"
                    self.root.after(
                        0,
                        lambda i=idx, eta=eta_text, t_idx=token_index, tok=token: self._update_progress(
                            i, total, eta, t_idx, tok
                        ),
                    )
                    continue
                try:
                    segments = guard.segment_text(token.text)
                    if not segments:
                        final_text = token.text
                    elif len(segments) == 1 and segments[0].translatable:
                        units = self._estimate_units(token.text)
                        if self.ai_translate_var.get():
                            final_text = ai_translate_text(
                                base_url,
                                self.device_token or "",
                                token.text,
                                source,
                                target,
                                glossary=self.glossary or None,
                                units=units,
                            )
                        else:
                            # Respeita a escolha do provider
                            provider = self.translation_provider_var.get()
                            if provider == "nllb":
                                nllb_source = self._to_nllb_code(source)
                                nllb_target = self._to_nllb_code(target)
                                final_text = translate_nllb(
                                    base_url, self.device_token or "", token.text, nllb_source, nllb_target, units=units
                                )
                            elif provider == "ambos":
                                # Para individual, testa ambos e usa o LibreTranslate
                                nllb_source = self._to_nllb_code(source)
                                nllb_target = self._to_nllb_code(target)
                                final_text = translate_text(
                                    base_url, self.device_token or "", token.text, source, target, units=units
                                )
                            else:
                                final_text = translate_text(
                                    base_url, self.device_token or "", token.text, source, target, units=units
                                )
                    else:
                        parts: List[str] = []
                        for segment in segments:
                            if not segment.translatable or not segment.text.strip():
                                parts.append(segment.text)
                                continue
                            units = self._estimate_units(segment.text)
                            if self.ai_translate_var.get():
                                translated_part = ai_translate_text(
                                    base_url,
                                    self.device_token or "",
                                    segment.text,
                                    source,
                                    target,
                                    glossary=self.glossary or None,
                                    units=units,
                                )
                            else:
                                # Respeita a escolha do provider
                                provider = self.translation_provider_var.get()
                                if provider == "nllb":
                                    nllb_source = self._to_nllb_code(source)
                                    nllb_target = self._to_nllb_code(target)
                                    translated_part = translate_nllb(
                                        base_url, self.device_token or "", segment.text, nllb_source, nllb_target, units=units
                                    )
                                elif provider == "ambos":
                                    # Para individual, usa LibreTranslate
                                    translated_part = translate_text(
                                        base_url, self.device_token or "", segment.text, source, target, units=units
                                    )
                                else:
                                    translated_part = translate_text(
                                        base_url, self.device_token or "", segment.text, source, target, units=units
                                    )
                            parts.append(translated_part)
                        final_text = "".join(parts)
                    results.append((token_index, final_text))
                except APIError as exc:
                    errors.append(f"{os.path.basename(self._display_source(token))} ({token.location}): {exc}")
                elapsed = time.time() - start_time
                avg = elapsed / max(1, idx)
                remaining = avg * max(0, total - idx)
                eta_text = f"ETA: {int(remaining)}s"
                self.root.after(
                    0,
                    lambda i=idx, eta=eta_text, t_idx=token_index, tok=token: self._update_progress(
                        i, total, eta, t_idx, tok
                    ),
                )
            return results, errors

        def on_success(payload: tuple[List[tuple[int, str]], List[str]]) -> None:
            results, errors = payload
            for token_index, translated in results:
                self.tokens[token_index].translation = translated
                self.tree.set(str(token_index), column="translation", value=translated)
                self.tree.set(
                    str(token_index), column="status", value=self._token_status(self.tokens[token_index])
                )
                if self._selected_index == token_index:
                    self.translation_var.set(translated)
            if errors:
                messagebox.showwarning(
                    "Aviso", f"{len(errors)} traducao(oes) falharam:\n" + "\n".join(errors[:8])
                )
            self.status_var.set(f"Traducao concluida: {len(results)}/{total}.")
            self._set_busy(False)
            self.refresh_usage()
            if on_done:
                on_done()

        def on_error(exc: Exception) -> None:
            self._set_busy(False)
            messagebox.showerror("Erro", self._format_license_error(str(exc)))
            self.status_var.set("Falha ao traduzir.")

        self._run_in_thread(task, on_success, on_error)

    def load_file(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=(
                ("Documentos", "*.docx *.pptx *.ppsx *.xlsx *.xlsm *.txt *.pdf"),
                ("Todos", "*.*"),
            )
        )
        if not file_path:
            return
        try:
            new_tokens = extract_tokens(file_path)
            merge_tokens(self.tokens, new_tokens)
            self.refresh_tree()
            self.status_var.set(f"{len(self.tokens)} tokens carregados.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Nao foi possivel extrair tokens:\n{exc}")

    def select_input_dir(self) -> None:
        path = filedialog.askdirectory(title="Pasta de origem")
        if path:
            self.input_dir_var.set(path)

    def select_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Pasta de destino")
        if path:
            self.output_dir_var.set(path)

    def select_single_file(self) -> None:
        single = filedialog.askopenfilename(
            title="Selecionar um arquivo",
            filetypes=(
                ("Documentos", "*.docx *.pptx *.ppsx *.xlsx *.xlsm *.txt *.pdf"),
                ("Todos", "*.*"),
            ),
        )
        if not single:
            return
        self.input_dir_var.set(os.path.dirname(single))
        self.folder_files = [single]
        self.files_list.delete(*self.files_list.get_children())
        self.file_iid_map.clear()
        rel = os.path.basename(single)
        self.files_list.insert("", tk.END, iid="0", values=(rel, "PENDENTE", "0%"))
        self.file_iid_map[single] = "0"
        self.files_count_var.set("Arquivos: 1")
        self.status_var.set("Arquivo selecionado. Clique para carregar tokens ou traduzir.")

    def select_all_files(self) -> None:
        for iid in self.files_list.get_children():
            self.files_list.selection_add(iid)

    def clear_file_selection(self) -> None:
        self.files_list.selection_remove(self.files_list.selection())

    def _selected_batch_files(self) -> List[str]:
        iids = list(self.files_list.selection())
        if not iids:
            return []
        return [self.folder_files[int(iid)] for iid in iids]

    def load_folder(self) -> None:
        root_dir = self.input_dir_var.get().strip()
        if not root_dir:
            messagebox.showwarning("Aviso", "Selecione a pasta de origem.")
            return
        output_dir = self.output_dir_var.get().strip()
        files = self._iter_supported_files(root_dir)
        if not files:
            messagebox.showinfo("Aviso", "Nenhum arquivo suportado encontrado.")
            return
        filtered: List[str] = []
        for path in files:
            if output_dir and self.skip_existing_var.get():
                output_path = self._output_path_for(path, root_dir, output_dir)
                if os.path.exists(output_path):
                    continue
            filtered.append(path)
        self.folder_files = filtered
        self.files_list.delete(*self.files_list.get_children())
        self.file_iid_map.clear()
        for idx, path in enumerate(self.folder_files):
            rel = os.path.relpath(path, root_dir)
            iid = str(idx)
            self.files_list.insert("", tk.END, iid=iid, values=(rel, "PENDENTE", "0%"))
            self.file_iid_map[path] = iid
        self.files_count_var.set(f"Arquivos: {len(self.folder_files)}")
        self.status_var.set("Selecione os arquivos e clique em Traduzir pasta.")

    def on_file_select(self, event: tk.Event) -> None:  # noqa: ANN001
        selection = list(self.files_list.selection())
        if not selection:
            return
        path = self.folder_files[int(selection[0])]
        try:
            self.tokens = extract_tokens(path)
            self.refresh_tree()
            self.status_var.set(f"Tokens carregados de {os.path.basename(path)}.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Nao foi possivel carregar tokens:\n{exc}")

    def translate_folder(self) -> None:
        root_dir = self.input_dir_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        if not root_dir or not output_dir:
            messagebox.showwarning("Aviso", "Selecione pasta de origem e destino.")
            return
        if not self.folder_files:
            self.load_folder()
        selected = self._selected_batch_files()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione os arquivos a traduzir.")
            return
        if not self._ensure_languages_ready():
            return
        if not self._ensure_device_token():
            return

        base_url = self.base_url_var.get().strip()
        source = self._get_language_code(self.source_var.get())
        target = self._get_language_code(self.target_var.get())
        self.batch_progress["value"] = 0
        self.batch_progress["maximum"] = max(1, len(selected))
        self.batch_files_order = selected
        self.batch_files_done = set()
        self.eta_var.set("ETA: -")
        self._set_busy(True)

        def task() -> List[str]:
            errors: List[str] = []
            start_time = time.time()
            for idx, path in enumerate(selected, start=1):
                try:
                    tokens = extract_tokens(path)
                    self.tokens = tokens
                    self.root.after(0, self.refresh_tree)
                    self.root.after(0, lambda p=path: self._update_file_percent(p, 0))

                    if self.ai_evaluate_var.get():
                        eval_items = ai_evaluate_texts(
                            base_url,
                            self.device_token or "",
                            [t.text for t in tokens],
                            source,
                            target,
                        )
                        for token, item in zip(tokens, eval_items):
                            translatable = item.get("translatable")
                            if isinstance(translatable, bool):
                                token.skip = not translatable
                                token.skip_reason = str(item.get("reason") or "")
                        self.root.after(0, self.refresh_tree)

                    if self.ai_glossary_var.get() and not self.glossary:
                        sample_texts = [t.text for t in tokens if t.text.strip()][:80]
                        if sample_texts:
                            self.glossary = ai_build_glossary(
                                base_url, self.device_token or "", sample_texts, source, target
                            )

                    usage = get_usage(base_url, self.device_token or "")
                    quota_remaining = usage.get("quota_remaining")
                    if quota_remaining is not None:
                        needed_units = sum(self._estimate_units(t.text) for t in tokens if not t.skip)
                        if quota_remaining <= 0 or needed_units > quota_remaining:
                            raise APIError(
                                f"Cota insuficiente. Necessario {needed_units}, restante {quota_remaining}."
                            )

                    translated_count = 0
                    total_tokens = max(1, sum(1 for t in tokens if not t.skip))
                    for token_index, token in enumerate(tokens):
                        if token.skip:
                            continue
                        units = self._estimate_units(token.text)
                        if self.ai_translate_var.get():
                            translated = ai_translate_text(
                                base_url,
                                self.device_token or "",
                                token.text,
                                source,
                                target,
                                glossary=self.glossary or None,
                                units=units,
                            )
                        else:
                            translated = translate_text(
                                base_url, self.device_token or "", token.text, source, target, units=units
                            )
                        token.translation = translated
                        translated_count += 1
                        self.root.after(
                            0,
                            lambda t_idx=token_index, t=token: self._update_token_row(t_idx, t),
                        )
                        percent = int((translated_count / total_tokens) * 100)
                        self.root.after(0, lambda p=path, pct=percent: self._update_file_percent(p, pct))

                    output_path = self._output_path_for(path, root_dir, output_dir)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    source_for_export = tokens[0].source_file if tokens else path
                    export_translated_document(source_for_export, tokens, output_path)

                    elapsed = time.time() - start_time
                    avg = elapsed / max(1, idx)
                    remaining = avg * max(0, len(selected) - idx)
                    eta_text = f"ETA: {int(remaining)}s"
                    self.root.after(
                        0,
                        lambda i=idx, eta=eta_text, p=path: self._update_batch_progress(i, eta, p),
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{os.path.basename(path)}: {exc}")
            return errors

        def on_success(errors: List[str]) -> None:
            self._set_busy(False)
            self.refresh_usage()
            if errors:
                messagebox.showerror("Erro", "Alguns arquivos falharam:\n" + "\n".join(errors[:6]))
            else:
                messagebox.showinfo("Sucesso", f"Arquivos traduzidos salvos em:\n{output_dir}")

        def on_error(exc: Exception) -> None:
            self._set_busy(False)
            messagebox.showerror("Erro", self._format_license_error(str(exc)))

        self._run_in_thread(task, on_success, on_error)

    def _format_license_error(self, message: str) -> str:
        lower = message.lower()
        if "invalid license" in lower or "licenca" in lower:
            return "Licenca invalida. Contacte Pedro Manjate: 874381448"
        if "device limit reached" in lower:
            return "Licenca ja associada a outro dispositivo. Contacte Pedro Manjate: 874381448"
        if "device blocked" in lower:
            return "Dispositivo bloqueado. Contacte Pedro Manjate: 874381448"
        if "limit exceeded" in lower or "cota" in lower:
            return "Cota esgotada. Contacte Pedro Manjate: 874381448"
        return message

    def _iter_supported_files(self, root_dir: str) -> List[str]:
        supported = {".docx", ".pptx", ".ppsx", ".xlsx", ".xlsm", ".txt", ".pdf"}
        files: List[str] = []
        for base, _, filenames in os.walk(root_dir):
            for name in filenames:
                ext = os.path.splitext(name)[1].lower()
                if ext in supported:
                    files.append(os.path.join(base, name))
        return files

    def _output_path_for(self, source_path: str, root_dir: str, output_dir: str) -> str:
        rel = os.path.relpath(source_path, root_dir)
        base, ext = os.path.splitext(rel)
        if ext.lower() == ".pdf":
            out_rel = f"{base}_traduzido.docx"
        else:
            out_rel = f"{base}_traduzido{ext}"
        return os.path.join(output_dir, out_rel)

    def _export_batch(self, root_dir: str, output_dir: str) -> None:
        sources = sorted({t.source_file for t in self.tokens})
        errors: List[str] = []
        for source_file in sources:
            file_tokens = [t for t in self.tokens if t.source_file == source_file]
            display_source = file_tokens[0].source_original or source_file
            output_path = self._output_path_for(display_source, root_dir, output_dir)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            if self.skip_existing_var.get() and os.path.exists(output_path):
                continue
            try:
                export_translated_document(source_file, file_tokens, output_path)
            except Exception as exc:  # noqa: BLE001
                    errors.append(f"{os.path.basename(display_source)}: {exc}")
        if errors:
            messagebox.showerror("Erro", "Falha ao exportar alguns arquivos:\n" + "\n".join(errors[:6]))
        else:
            messagebox.showinfo("Sucesso", f"Arquivos traduzidos salvos em:\n{output_dir}")

    def refresh_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, token in enumerate(self.tokens):
            self.tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    self._token_status(token),
                    token.text,
                    token.translation,
                    f"{os.path.basename(self._display_source(token))} ({token.location})",
                ),
            )

    def on_select(self, event: tk.Event) -> None:  # noqa: ANN001
        selection = self.tree.selection()
        if not selection:
            self._selected_index = None
            self.save_translation_btn.config(state=tk.DISABLED)
            return
        idx = int(selection[0])
        self._selected_index = idx
        token = self.tokens[idx]
        self.original_var.set(token.text)
        self.translation_var.set(token.translation)
        self.save_translation_btn.config(state=tk.NORMAL)
        if token.skip:
            self.status_var.set(f"Token marcado para pular: {token.skip_reason or 'sem motivo'}")

    def save_translation(self) -> None:
        if self._selected_index is None:
            return
        translation = self.translation_var.get()
        token = self.tokens[self._selected_index]
        token.translation = translation
        self.tree.set(str(self._selected_index), column="translation", value=translation)
        self.tree.set(str(self._selected_index), column="status", value=self._token_status(token))

    def clear_tokens(self) -> None:
        self.tokens.clear()
        self._selected_index = None
        self.refresh_tree()
        self.status_var.set("Nenhum arquivo carregado.")
        self.original_var.set("")
        self.translation_var.set("")
        self.save_translation_btn.config(state=tk.DISABLED)

    def export_csv(self) -> None:
        if not self.tokens:
            messagebox.showinfo("Aviso", "Nenhum token para exportar.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"), ("Todos", "*.*")),
            initialfile="tokens.csv",
        )
        if not file_path:
            return
        try:
            self._write_csv(file_path)
            messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{file_path}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Nao foi possivel exportar:\n{exc}")

    def export_documents(self) -> None:
        if not self.tokens:
            messagebox.showinfo("Aviso", "Nenhum token para exportar.")
            return

        output_dir = filedialog.askdirectory(title="Escolha a pasta de destino")
        if not output_dir:
            return

        sources = sorted({t.source_file for t in self.tokens})
        errors: List[str] = []
        for source_file in sources:
            file_tokens = [t for t in self.tokens if t.source_file == source_file]
            display_source = file_tokens[0].source_original or source_file
            base, ext = os.path.splitext(os.path.basename(display_source))
            if ext.lower() == ".pdf":
                output_path = os.path.join(output_dir, f"{base}_traduzido.docx")
            else:
                output_path = os.path.join(output_dir, f"{base}_traduzido{ext}")
            try:
                export_translated_document(source_file, file_tokens, output_path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{os.path.basename(display_source)}: {exc}")

        if errors:
            messagebox.showerror("Erro", "Nao foi possivel exportar alguns arquivos:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Sucesso", f"{len(sources)} arquivo(s) exportados em:\n{output_dir}")

    def _write_csv(self, path: str) -> None:
        import csv

        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow(["arquivo", "local", "original", "traducao"])
            for token in self.tokens:
                writer.writerow(
                    [os.path.basename(token.source_file), token.location, token.text, token.translation]
                )
