# -*- coding: utf-8 -*-
"""
Gerenciador de configurações locais do desktop app.
Armazena configurações em JSON no diretório do usuário.
"""
import json
import os
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Gerencia configurações locais do desktop app"""

    def __init__(self, app_name: str = "tradutor_master"):
        """
        Inicializa gerenciador de configuração.

        Args:
            app_name: Nome da aplicação (usado para nome da pasta)
        """
        self.app_name = app_name
        self.config_dir = Path.home() / f".{app_name}"
        self.config_file = self.config_dir / "config.json"

        # Criar diretório se não existir
        self.config_dir.mkdir(exist_ok=True)

        # Carregar configuração
        self.config = self._load()

    def _load(self) -> dict:
        """
        Carrega configuração do arquivo JSON.

        Returns:
            Dicionário com configurações
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Se arquivo estiver corrompido, usar padrões
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict:
        """
        Retorna configuração padrão.

        Returns:
            Dicionário com valores padrão
        """
        return {
            # Claude/Anthropic
            "claude_api_key": "",
            "claude_model": "claude-sonnet-4-5-20250929",

            # OpenAI
            "openai_api_key": "",
            "openai_model": "gpt-4o-mini",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_timeout": 60.0,

            # LibreTranslate
            "libretranslate_url": "http://102.211.186.44/translate",
            "libretranslate_timeout": 15.0,

            # Backend API (para licenças e registro)
            "api_base_url": "http://127.0.0.1:8000",

            # Base de dados MySQL
            "mysql_host": "102.211.186.44",
            "mysql_port": 3306,
            "mysql_user": "root",
            "mysql_password": "Root@12345!",
            "mysql_database": "tradutor_db",

            # Preferências de tradução
            "use_dictionary": True,
            "use_ai": True,
            "ai_provider": "claude",
            "auto_glossary": False,
            "default_source_lang": "en",
            "default_target_lang": "pt",

            # Nome da empresa (NUNCA traduzir)
            "company_name": "",  # Nome da empresa que aparece nos documentos
            "extract_company_from_filename": True,  # Extrair nome da empresa do arquivo automaticamente

            # UI
            "window_width": 1200,
            "window_height": 800,
            "theme": "light",

            # Último uso
            "last_input_dir": "",
            "last_output_dir": "",
        }

    def save(self):
        """Salva configuração no arquivo JSON."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Erro ao salvar configuração: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração.

        Args:
            key: Chave da configuração
            default: Valor padrão se chave não existir

        Returns:
            Valor da configuração ou default
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Define valor de configuração e salva.

        Args:
            key: Chave da configuração
            value: Novo valor
        """
        self.config[key] = value
        self.save()

    def update(self, updates: dict):
        """
        Atualiza múltiplas configurações de uma vez.

        Args:
            updates: Dicionário com chaves e valores a atualizar
        """
        self.config.update(updates)
        self.save()

    def reset(self):
        """Reseta configuração para valores padrão."""
        self.config = self._default_config()
        self.save()

    def export_config(self, file_path: str):
        """
        Exporta configuração para arquivo.

        Args:
            file_path: Caminho do arquivo de destino
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def import_config(self, file_path: str):
        """
        Importa configuração de arquivo.

        Args:
            file_path: Caminho do arquivo de origem
        """
        with open(file_path, "r", encoding="utf-8") as f:
            imported = json.load(f)
            self.config.update(imported)
            self.save()

    @property
    def config_path(self) -> Path:
        """Retorna caminho do arquivo de configuração."""
        return self.config_file


if __name__ == "__main__":
    # Teste simples
    config = ConfigManager()

    print("Testando ConfigManager...")
    print(f"✓ Arquivo de configuração: {config.config_path}")

    # Testar get
    api_key = config.get("claude_api_key")
    print(f"✓ Claude API Key: {'(configurada)' if api_key else '(não configurada)'}")

    # Testar set
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"
    print("✓ Set/Get funcionando")

    # Testar update
    config.update({"key1": "value1", "key2": "value2"})
    assert config.get("key1") == "value1"
    print("✓ Update funcionando")

    print("\n📊 Configurações atuais:")
    for key, value in config.config.items():
        if "password" in key.lower() or "api_key" in key.lower():
            display_value = "***" if value else "(vazio)"
        else:
            display_value = value
        print(f"  {key}: {display_value}")
