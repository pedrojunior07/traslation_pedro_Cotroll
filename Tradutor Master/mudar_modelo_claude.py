#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para mudar o modelo Claude usado no Tradutor Master
"""
import json
from pathlib import Path

# Modelos disponíveis
MODELOS = {
    "1": {
        "nome": "Claude 4.5 Sonnet (Recomendado)",
        "id": "claude-sonnet-4-5-20250929",
        "descricao": "Melhor equilíbrio entre velocidade, inteligência e custo. Moderno (2025-09)."
    },
    "2": {
        "nome": "Claude 4.5 Opus (Mais Inteligente)",
        "id": "claude-opus-4-5-20251101",
        "descricao": "Modelo extremamente poderoso de 2026. Máxima precisão JSON."
    },
    "3": {
        "nome": "Claude 4.5 Haiku (Mais Rápido)",
        "id": "claude-haiku-4-5-20251001",
        "descricao": "Ideal para traduções rápidas e baratas. Muito eficiente."
    }
}

def get_config_path():
    """Retorna caminho do arquivo de configuração"""
    config_dir = Path.home() / ".tradutor_master"
    config_file = config_dir / "config.json"
    return config_file

def load_config():
    """Carrega configuração atual"""
    config_file = get_config_path()
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print("❌ Arquivo de configuração não encontrado!")
        print(f"   Esperado em: {config_file}")
        return None

def save_config(config):
    """Salva configuração"""
    config_file = get_config_path()
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"✅ Configuração salva em: {config_file}")

def main():
    print("=" * 80)
    print("🔧 MUDAR MODELO CLAUDE - Tradutor Master")
    print("=" * 80)
    print()

    # Carregar config atual
    config = load_config()
    if not config:
        return

    # Mostrar modelo atual
    modelo_atual = config.get("claude_model", "Não definido")
    print(f"📌 Modelo atual: {modelo_atual}")
    print()

    # Mostrar opções
    print("Modelos disponíveis:")
    print()
    for key, info in MODELOS.items():
        print(f"{key}. {info['nome']}")
        print(f"   ID: {info['id']}")
        print(f"   {info['descricao']}")
        print()

    # Pedir escolha
    escolha = input("Digite o número do modelo que deseja usar (ou 'q' para sair): ").strip()

    if escolha.lower() == 'q':
        print("❌ Operação cancelada.")
        return

    if escolha not in MODELOS:
        print("❌ Opção inválida!")
        return

    # Atualizar configuração
    modelo_novo = MODELOS[escolha]
    config["claude_model"] = modelo_novo["id"]

    print()
    print(f"🔄 Mudando de:")
    print(f"   {modelo_atual}")
    print(f"   ↓")
    print(f"   {modelo_novo['nome']} ({modelo_novo['id']})")
    print()

    confirma = input("Confirmar mudança? (s/n): ").strip().lower()
    if confirma == 's':
        save_config(config)
        print()
        print("✅ Modelo alterado com sucesso!")
        print("   Reinicie o Tradutor Master para usar o novo modelo.")
    else:
        print("❌ Operação cancelada.")

if __name__ == "__main__":
    main()
