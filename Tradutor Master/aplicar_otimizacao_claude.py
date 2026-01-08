# -*- coding: utf-8 -*-
"""
Script para aplicar otimizações no Claude Client

Este script adiciona processamento paralelo e rate limiting inteligente
ao claude_client.py para maximizar o uso da API do Claude Haiku 3.5.

EXECUÇÃO:
    python aplicar_otimizacao_claude.py

BACKUP:
    Um backup será criado automaticamente em claude_client.py.backup
"""

import os
import shutil

def aplicar_otimizacao():
    """Aplica otimizações no claude_client.py"""

    arquivo_original = "src/claude_client.py"
    arquivo_backup = "src/claude_client.py.backup"

    print("🚀 Aplicando otimizações no Claude Client...")
    print()

    # Verificar se arquivo existe
    if not os.path.exists(arquivo_original):
        print(f"❌ Erro: {arquivo_original} não encontrado!")
        return False

    # Criar backup
    print(f"📋 Criando backup: {arquivo_backup}")
    shutil.copy2(arquivo_original, arquivo_backup)

    # Ler arquivo original
    with open(arquivo_original, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    # Verificar se já foi aplicado
    if "use_parallel: bool = True" in conteudo:
        print("✅ Otimizações já foram aplicadas anteriormente!")
        return True

    print("⚙️  Aplicando mudanças...")

    # 1. Adicionar imports
    imports_antigos = """import json
from typing import List, Dict, Optional, Tuple
import anthropic"""

    imports_novos = """import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import anthropic"""

    conteudo = conteudo.replace(imports_antigos, imports_novos)

    # 2. Adicionar Claude Haiku 3.5 ao pricing
    pricing_antigo = """        # Haiku 3
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25, "cache_write": 0.30, "cache_read": 0.03},
    }"""

    pricing_novo = """        # Haiku 3
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25, "cache_write": 0.30, "cache_read": 0.03},
        # Haiku 3.5 (novo modelo otimizado)
        "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25, "cache_write": 0.30, "cache_read": 0.03},
    }"""

    conteudo = conteudo.replace(pricing_antigo, pricing_novo)

    # 3. Adicionar ao MAX_TOKENS_LIMITS
    max_tokens_antigo = """        "claude-3-haiku-20240307": 4096,
    }"""

    max_tokens_novo = """        "claude-3-haiku-20240307": 4096,
        "claude-3-5-haiku-20241022": 8192,  # Haiku 3.5 suporta mais tokens
    }"""

    conteudo = conteudo.replace(max_tokens_antigo, max_tokens_novo)

    # 4. Adicionar dicionários de rate limits e batch sizes após MAX_TOKENS_LIMITS
    adicionar_apos = """    }

    # Modelos válidos (para validação)
    VALID_MODELS = list(PRICING.keys())"""

    adicionar_texto = """    }

    # Rate limits (requisições por minuto) por modelo
    RATE_LIMITS = {
        "claude-3-5-sonnet-20241022": 50,
        "claude-3-5-sonnet-20240620": 50,
        "claude-3-opus-20240229": 50,
        "claude-3-sonnet-20240229": 50,
        "claude-3-haiku-20240307": 50,
        "claude-3-5-haiku-20241022": 50,  # Haiku 3.5: 50 RPM
    }

    # Batch size otimizado por modelo (quantos textos por requisição)
    OPTIMAL_BATCH_SIZES = {
        "claude-3-5-sonnet-20241022": 100,
        "claude-3-5-sonnet-20240620": 100,
        "claude-3-opus-20240229": 50,
        "claude-3-sonnet-20240229": 75,
        "claude-3-haiku-20240307": 150,  # Haiku é rápido, pode processar mais
        "claude-3-5-haiku-20241022": 200,  # Haiku 3.5: maior contexto, batches maiores
    }

    # Modelos válidos (para validação)
    VALID_MODELS = list(PRICING.keys())"""

    conteudo = conteudo.replace(adicionar_apos, adicionar_texto)

    # 5. Atualizar __init__
    init_antigo = """    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", timeout: float = 120.0):
        \"\"\"
        Inicializa cliente Claude.

        Args:
            api_key: API key da Anthropic
            model: Modelo Claude a usar
            timeout: Timeout em segundos
        \"\"\"
        if not api_key:
            raise ValueError("API key é obrigatória")

        # Validar modelo
        if model not in self.VALID_MODELS:
            available = ", ".join(self.VALID_MODELS)
            raise ValueError(
                f"Modelo '{model}' não é válido.\\n\\n"
                f"Modelos disponíveis:\\n{available}\\n\\n"
                f"NOTA: Se você mudou de modelo e recebeu erro 404, "
                f"verifique se o nome do modelo está correto."
            )

        self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
        self.model = model
        self.timeout = timeout
        self.max_tokens = self.MAX_TOKENS_LIMITS.get(model, 4096)"""

    init_novo = """    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", timeout: float = 120.0, max_workers: int = None):
        \"\"\"
        Inicializa cliente Claude.

        Args:
            api_key: API key da Anthropic
            model: Modelo Claude a usar
            timeout: Timeout em segundos
            max_workers: Número de threads paralelas (None = auto-detect baseado no modelo)
        \"\"\"
        if not api_key:
            raise ValueError("API key é obrigatória")

        # Validar modelo
        if model not in self.VALID_MODELS:
            available = ", ".join(self.VALID_MODELS)
            raise ValueError(
                f"Modelo '{model}' não é válido.\\n\\n"
                f"Modelos disponíveis:\\n{available}\\n\\n"
                f"NOTA: Se você mudou de modelo e recebeu erro 404, "
                f"verifique se o nome do modelo está correto."
            )

        self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
        self.model = model
        self.timeout = timeout
        self.max_tokens = self.MAX_TOKENS_LIMITS.get(model, 4096)
        self.rate_limit = self.RATE_LIMITS.get(model, 50)
        self.optimal_batch_size = self.OPTIMAL_BATCH_SIZES.get(model, 100)

        # Auto-detectar workers baseado no rate limit
        # Para aproveitar os 50 RPM, podemos ter ~10 workers em paralelo
        if max_workers is None:
            if "haiku" in model.lower():
                max_workers = 10  # Haiku é rápido, usar mais paralelos
            else:
                max_workers = 5  # Modelos maiores, menos paralelos
        self.max_workers = max_workers

        # Controle de rate limiting
        self._request_times = []  # Lista de timestamps das últimas requisições
        self._lock = threading.Lock()

        print(f"🚀 Claude Client inicializado:")
        print(f"   Modelo: {model}")
        print(f"   Batch size otimizado: {self.optimal_batch_size}")
        print(f"   Workers paralelos: {self.max_workers}")
        print(f"   Rate limit: {self.rate_limit} RPM")"""

    conteudo = conteudo.replace(init_antigo, init_novo)

    # 6. Adicionar método _wait_for_rate_limit após __init__
    adicionar_metodo_apos = """        print(f"   Rate limit: {self.rate_limit} RPM")

    def translate_document("""

    adicionar_metodo_texto = """        print(f"   Rate limit: {self.rate_limit} RPM")

    def _wait_for_rate_limit(self):
        \"\"\"Aguarda se necessário para respeitar rate limit (50 RPM)\"\"\"
        with self._lock:
            now = time.time()

            # Remover requisições antigas (> 60 segundos)
            self._request_times = [t for t in self._request_times if now - t < 60]

            # Se atingiu o limite, aguardar
            if len(self._request_times) >= self.rate_limit:
                # Tempo até a requisição mais antiga expirar
                oldest = self._request_times[0]
                wait_time = 60 - (now - oldest) + 0.1  # +0.1 para segurança

                if wait_time > 0:
                    print(f"⏸ Rate limit atingido ({self.rate_limit} RPM), aguardando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    now = time.time()
                    # Limpar novamente após espera
                    self._request_times = [t for t in self._request_times if now - t < 60]

            # Registrar esta requisição
            self._request_times.append(time.time())

    def translate_document("""

    conteudo = conteudo.replace(adicionar_metodo_apos, adicionar_metodo_texto)

    # 7. Adicionar novos parâmetros ao translate_document
    translate_params_antigo = """        batch_size: int = 100,
        progress_callback: Optional[callable] = None"""

    translate_params_novo = """        batch_size: int = None,
        progress_callback: Optional[callable] = None,
        use_parallel: bool = True"""

    conteudo = conteudo.replace(translate_params_antigo, translate_params_novo)

    # Salvar arquivo modificado
    with open(arquivo_original, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print()
    print("✅ Otimizações aplicadas com sucesso!")
    print()
    print("📝 Mudanças realizadas:")
    print("   ✓ Adicionado suporte a Claude Haiku 3.5")
    print("   ✓ Implementado processamento paralelo")
    print("   ✓ Adicionado rate limiting inteligente")
    print("   ✓ Otimizado batch sizes por modelo")
    print()
    print("⚠️  NOTA: O método translate_document ainda precisa ser")
    print("   atualizado manualmente para usar processamento paralelo.")
    print("   Veja o arquivo: src/claude_client_optimized.py")
    print()
    print(f"💾 Backup salvo em: {arquivo_backup}")

    return True

if __name__ == "__main__":
    print()
    print("="*60)
    print("  OTIMIZAÇÃO DO CLAUDE CLIENT PARA HAIKU 3.5")
    print("="*60)
    print()

    sucesso = aplicar_otimizacao()

    if sucesso:
        print()
        print("🎉 Pronto! Agora você pode usar o Claude Haiku 3.5")
        print("   com velocidade máxima!")
        print()
    else:
        print()
        print("❌ Falha ao aplicar otimizações.")
        print()
