# -*- coding: utf-8 -*-
"""
Cache local de traduções para evitar reprocessamento.
Economiza tokens ao reutilizar traduções anteriores.
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict


class TranslationCache:
    """Cache local de traduções com suporte a expiração"""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 86400 * 7):
        """
        Inicializa cache de traduções.

        Args:
            cache_dir: Diretório para cache. Se None, usa padrão
            ttl_seconds: Tempo de vida do cache em segundos (padrão: 7 dias)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".tradutor_master" / "cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _get_hash(self, text: str, source: str, target: str) -> str:
        """
        Gera hash MD5 para chave de cache.

        Args:
            text: Texto original
            source: Idioma origem
            target: Idioma destino

        Returns:
            Hash MD5
        """
        data = f"{text}|{source}|{target}"
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    def _get_cache_file(self, text: str, source: str, target: str) -> Path:
        """Retorna caminho do arquivo de cache."""
        hash_key = self._get_hash(text, source, target)
        return self.cache_dir / f"{hash_key}.json"

    def get(self, text: str, source: str, target: str) -> Optional[str]:
        """
        Busca tradução no cache.

        Args:
            text: Texto original
            source: Idioma origem
            target: Idioma destino

        Returns:
            Tradução se encontrada e válida, None caso contrário
        """
        if not text or not text.strip():
            return None

        cache_file = self._get_cache_file(text, source, target)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)

            # Verificar expiração
            if time.time() - cached.get("timestamp", 0) > self.ttl_seconds:
                # Cache expirado, remover
                cache_file.unlink(missing_ok=True)
                return None

            # Verificar se texto ainda corresponde (evitar colisões)
            if cached.get("original") != text:
                return None

            return cached.get("translation")

        except (json.JSONDecodeError, IOError, KeyError):
            # Cache corrompido, remover
            cache_file.unlink(missing_ok=True)
            return None

    def set(
        self,
        text: str,
        source: str,
        target: str,
        translation: str,
        metadata: Optional[Dict] = None
    ):
        """
        Armazena tradução no cache.

        Args:
            text: Texto original
            source: Idioma origem
            target: Idioma destino
            translation: Tradução
            metadata: Metadados opcionais (provider, cost, etc)
        """
        if not text or not text.strip():
            return

        cache_file = self._get_cache_file(text, source, target)

        cache_data = {
            "original": text,
            "translation": translation,
            "source": source,
            "target": target,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Erro ao salvar cache: {e}")

    def clear_expired(self) -> int:
        """
        Remove entradas expiradas do cache.

        Returns:
            Número de arquivos removidos
        """
        removed = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)

                if current_time - cached.get("timestamp", 0) > self.ttl_seconds:
                    cache_file.unlink()
                    removed += 1
            except:
                # Arquivo corrompido, remover
                cache_file.unlink(missing_ok=True)
                removed += 1

        return removed

    def clear_all(self) -> int:
        """
        Remove todo o cache.

        Returns:
            Número de arquivos removidos
        """
        removed = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            removed += 1
        return removed

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do cache.

        Returns:
            Dicionário com estatísticas
        """
        total_files = 0
        total_size = 0
        expired_files = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            total_files += 1
            total_size += cache_file.stat().st_size

            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if current_time - cached.get("timestamp", 0) > self.ttl_seconds:
                    expired_files += 1
            except:
                expired_files += 1

        return {
            "total_entries": total_files,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "expired_entries": expired_files,
            "valid_entries": total_files - expired_files,
        }


if __name__ == "__main__":
    # Teste simples
    print("Testando TranslationCache...")

    cache = TranslationCache(ttl_seconds=60)  # 60 segundos para teste

    # Testar set/get
    cache.set("Hello World", "en", "pt", "Olá Mundo", metadata={"provider": "claude"})
    result = cache.get("Hello World", "en", "pt")
    assert result == "Olá Mundo"
    print("✓ Set/Get funcionando")

    # Testar cache miss
    result = cache.get("Non existent", "en", "pt")
    assert result is None
    print("✓ Cache miss funcionando")

    # Testar estatísticas
    stats = cache.get_stats()
    print(f"✓ Estatísticas do cache:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Limpar cache de teste
    removed = cache.clear_all()
    print(f"✓ Cache limpo: {removed} arquivos removidos")
