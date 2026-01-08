# -*- coding: utf-8 -*-
"""
CÓDIGO OTIMIZADO PARA O MÉTODO translate_document

Este código substitui o método translate_document no claude_client.py
para adicionar processamento paralelo e otimização de rate limiting.

INSTRUÇÕES:
1. Abra claude_client.py
2. Substitua o método translate_document (linhas 139-216) por este código
3. Adicione também o método _translate_batch_with_rate_limit
"""

def translate_document(
    self,
    tokens: List[Dict[str, str]],
    source: str,
    target: str,
    dictionary: Optional[Dict[str, str]] = None,
    batch_size: int = None,
    progress_callback: Optional[callable] = None,
    use_parallel: bool = True
) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    """
    Traduz documento em batches com processamento paralelo otimizado.

    Args:
        tokens: Lista de tokens [{"location": "...", "text": "..."}, ...]
        source: Código do idioma origem (en, pt, etc)
        target: Código do idioma destino
        dictionary: Dicionário opcional de termos a preservar
        batch_size: Número de tokens por batch (None = usar otimizado para o modelo)
        progress_callback: Função (mensagem, progresso_0_100) para atualizar UI
        use_parallel: Se True, processa batches em paralelo (padrão: True)

    Returns:
        Tuple (traduções, estatísticas_de_uso)
        - traduções: Lista de dicts [{"location": "...", "translation": "..."}, ...]
        - estatísticas: {"input_tokens": N, "output_tokens": N, "cost": 0.XX, ...}

    Raises:
        Exception: Se houver erro na tradução
    """
    if not tokens:
        return [], {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

    # Usar batch size otimizado se não especificado
    if batch_size is None:
        batch_size = self.optimal_batch_size

    # Se houver poucos tokens, traduzir tudo de uma vez
    if len(tokens) <= batch_size:
        if progress_callback:
            progress_callback(f"Traduzindo {len(tokens)} tokens com Claude...", 50)
        return self._translate_batch(tokens, source, target, dictionary)

    # Dividir em batches
    batches = []
    for i in range(0, len(tokens), batch_size):
        batches.append(tokens[i:i + batch_size])

    num_batches = len(batches)
    print(f"📦 Dividindo {len(tokens)} tokens em {num_batches} batches de ~{batch_size} tokens")
    print(f"⚡ Processamento {'PARALELO' if use_parallel else 'SEQUENCIAL'} com {self.max_workers} workers")

    # Inicializar estatísticas
    all_translations = []
    total_stats = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
        "cost": 0.0
    }

    if use_parallel and num_batches > 1:
        # PROCESSAMENTO PARALELO - Maximiza uso da API
        completed = 0
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submeter todos os batches
            future_to_batch = {
                executor.submit(self._translate_batch_with_rate_limit, batch, source, target, dictionary, i + 1, num_batches): i
                for i, batch in enumerate(batches)
            }

            # Processar conforme completam
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    translations, stats = future.result()
                    all_translations.extend(translations)

                    # Acumular estatísticas
                    for key in total_stats:
                        total_stats[key] += stats.get(key, 0)

                    completed += 1

                    # Atualizar progresso
                    progress_pct = (completed / num_batches) * 100
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (num_batches - completed) / rate if rate > 0 else 0

                    msg = f"Claude: {completed}/{num_batches} batches ({int(rate * 60):.0f} req/min, ETA: {eta:.0f}s)"
                    print(f"  ✓ Batch {completed}/{num_batches} completo ({len(translations)} tokens) - {int(rate * 60)} req/min")

                    if progress_callback:
                        progress_callback(msg, progress_pct)

                except Exception as e:
                    raise Exception(f"Erro no batch {batch_idx + 1}/{num_batches}: {str(e)}")

        elapsed_total = time.time() - start_time
        final_rate = num_batches / elapsed_total if elapsed_total > 0 else 0
        print(f"✓ Tradução paralela completa: {len(all_translations)} tokens em {elapsed_total:.1f}s ({int(final_rate * 60)} req/min)")

    else:
        # PROCESSAMENTO SEQUENCIAL - Para poucos batches
        for i, batch in enumerate(batches):
            batch_num = i + 1

            # Atualizar progresso na UI
            progress_pct = (batch_num / num_batches) * 100
            msg = f"Claude: Batch {batch_num}/{num_batches} ({len(batch)} tokens)"
            print(f"  Traduzindo batch {batch_num}/{num_batches} ({len(batch)} tokens)...")
            if progress_callback:
                progress_callback(msg, progress_pct)

            try:
                translations, stats = self._translate_batch(batch, source, target, dictionary)
                all_translations.extend(translations)

                # Acumular estatísticas
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)

            except Exception as e:
                raise Exception(f"Erro no batch {batch_num}/{num_batches}: {str(e)}")

        print(f"✓ Tradução sequencial completa: {len(all_translations)} tokens traduzidos")

    if progress_callback:
        progress_callback(f"✓ Tradução Claude completa: {len(all_translations)} tokens", 100)

    return all_translations, total_stats

def _translate_batch_with_rate_limit(
    self,
    tokens: List[Dict[str, str]],
    source: str,
    target: str,
    dictionary: Optional[Dict[str, str]],
    batch_num: int,
    total_batches: int
) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    """
    Traduz batch respeitando rate limit.
    Usado no processamento paralelo.
    """
    # Aguardar rate limit antes de fazer requisição
    self._wait_for_rate_limit()

    # Traduzir batch
    return self._translate_batch(tokens, source, target, dictionary)
