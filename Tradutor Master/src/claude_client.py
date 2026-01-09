# -*- coding: utf-8 -*-
"""
Cliente direto para Anthropic Claude.
Permite tradução de documentos completos com otimização de tokens via cache.
Suporta processamento paralelo otimizado para maximizar uso da API.
"""
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import anthropic


class ClaudeClient:
    """Cliente direto para Anthropic Claude com suporte a cache de prompts"""

    # Preços por 1M tokens (em USD) - Atualizado 2026
    PRICING = {
        # Séria 4.5 (Lançada final de 2025)
        "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
        "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
        "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25, "cache_write": 0.30, "cache_read": 0.03},
        # Sonnet 3.5 (Legado)
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
        "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
        # Opus 3 (Legado)
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
        # Haiku 3 (Legado)
        "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25, "cache_write": 0.30, "cache_read": 0.03},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25, "cache_write": 0.30, "cache_read": 0.03},
    }

    # Limites de max_tokens por modelo
    MAX_TOKENS_LIMITS = {
        "claude-sonnet-4-5-20250929": 8192,
        "claude-opus-4-5-20251101": 8192,
        "claude-haiku-4-5-20251001": 8192,
        "claude-3-5-sonnet-20241022": 8192,
        "claude-3-5-sonnet-20240620": 8192,
        "claude-3-opus-20240229": 4096,
        "claude-3-haiku-20240307": 4096,
        "claude-3-5-haiku-20241022": 8192,
    }

    # Rate limits (requisições por minuto) por modelo
    RATE_LIMITS = {
        "claude-sonnet-4-5-20250929": 100,  # Aumentado para 2026
        "claude-opus-4-5-20251101": 100,
        "claude-haiku-4-5-20251001": 100,
        "claude-3-5-sonnet-20241022": 50,
        "claude-3-5-sonnet-20240620": 50,
        "claude-3-opus-20240229": 50,
        "claude-3-haiku-20240307": 50,
        "claude-3-5-haiku-20241022": 50,
    }

    # Batch size otimizado por modelo (quantos SEGMENTOS por requisição)
    # LIMITADO PELO max_tokens (output)!
    # Textos longos (contratos) podem ter ~80-100 tokens cada, então ser CONSERVADOR
    # Cálculo seguro: max_tokens ÷ 100 tokens por segmento (textos longos)
    OPTIMAL_BATCH_SIZES = {
        "claude-sonnet-4-5-20250929": 100,
        "claude-opus-4-5-20251101": 100,
        "claude-haiku-4-5-20251001": 100,
        "claude-3-5-sonnet-20241022": 80,
        "claude-3-5-sonnet-20240620": 80,
        "claude-3-opus-20240229": 40,
        "claude-3-haiku-20240307": 40,
        "claude-3-5-haiku-20241022": 80,
    }

    # Modelos válidos (para validação)
    VALID_MODELS = list(PRICING.keys())

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929", timeout: float = 120.0, max_workers: int = None):
        """
        Inicializa cliente Claude.

        Args:
            api_key: API key da Anthropic
            model: Modelo Claude a usar
            timeout: Timeout em segundos
            max_workers: Número de threads paralelas (None = auto-detect baseado no modelo)
        """
        if not api_key:
            raise ValueError("API key é obrigatória")

        # Validar modelo
        if model not in self.VALID_MODELS:
            available = ", ".join(self.VALID_MODELS)
            raise ValueError(
                f"Modelo '{model}' não é válido.\n\n"
                f"Modelos disponíveis:\n{available}\n\n"
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
        # ESTRATÉGIA NOVA: Apenas 1 worker, batches GIGANTES
        # Com batches de 1500 segmentos, a maioria dos documentos vai em 1-2 requisições
        # SEM paralelismo = SEM problemas de rate limit
        if max_workers is None:
            max_workers = 1  # Apenas 1 worker = sem paralelismo, sem rate limit issues
        self.max_workers = max_workers

        # Controle de rate limiting
        self._request_times = []  # Lista de timestamps das últimas requisições
        self._lock = threading.Lock()

        print(f"🚀 Claude Client inicializado:")
        print(f"   Modelo: {model}")
        print(f"   Batch size otimizado: {self.optimal_batch_size}")
        print(f"   Workers paralelos: {self.max_workers}")
        print(f"   Rate limit: {self.rate_limit} RPM")

    def _wait_for_rate_limit(self):
        """Aguarda se necessário para respeitar rate limit (50 RPM)"""
        with self._lock:
            now = time.time()

            # Remover requisições antigas (> 60 segundos)
            self._request_times = [t for t in self._request_times if now - t < 60]

            # Se atingiu o limite, aguardar
            if len(self._request_times) >= self.rate_limit:
                # Tempo até a requisição mais antiga expirar
                oldest = self._request_times[0]
                wait_time = 60 - (now - oldest) + 0.5  # +0.5 para segurança extra

                if wait_time > 0:
                    print(f"⏸ Rate limit atingido ({self.rate_limit} RPM), aguardando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    now = time.time()
                    # Limpar novamente após espera
                    self._request_times = [t for t in self._request_times if now - t < 60]

            # Sem delay extra necessário - com 1 worker e batches gigantes,
            # naturalmente fica abaixo do rate limit
            # (cada requisição com 1500 segmentos demora ~10-20s para processar)

            # Registrar esta requisição
            self._request_times.append(time.time())

    def translate_document(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]] = None,
        batch_size: int = None,
        progress_callback: Optional[callable] = None,
        use_parallel: bool = True,
        company_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        Traduz documento em batches para evitar limite de output tokens.

        Args:
            tokens: Lista de tokens [{\"location\": \"...\", \"text\": \"...\"}, ...]
            source: Código do idioma origem (en, pt, etc)
            target: Código do idioma destino
            dictionary: Dicionário opcional de termos a preservar
            batch_size: Número de tokens por batch (padrão: 100)
            progress_callback: Função (mensagem, progresso_0_100) para atualizar UI

        Returns:
            Tuple (traduções, estatísticas_de_uso)
            - traduções: Lista de dicts [{\"location\": \"...\", \"translation\": \"...\"}, ...]
            - estatísticas: {\"input_tokens\": N, \"output_tokens\": N, \"cost\": 0.XX, ...}

        Raises:
            Exception: Se houver erro na tradução
        """
        if not tokens:
            return [], {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

        # DIVISÃO POR TOKENS REAIS (não por número de segmentos!)
        # Estratégia: Acumular segmentos até atingir limite de TOKENS estimados

        # Limite de tokens de output (30% para MARGEM ULTRA-CONSERVADORA)
        # Reduzido de 50% para 30% após testes mostrarem que ainda excedia
        max_output_tokens = int(self.max_tokens * 0.30)

        print(f"\n📊 Estratégia de Divisão:")
        print(f"   max_tokens disponível: {self.max_tokens}")
        print(f"   Usando 30% para MARGEM ULTRA-CONSERVADORA: {max_output_tokens} tokens")
        print(f"   Dividindo por TAMANHO REAL (não por número de segmentos)")

        # Dividir em batches baseado em TOKENS ESTIMADOS
        batches = []
        current_batch = []
        current_estimated_tokens = 0

        for token in tokens:
            text = token.get("text", "")
            text_chars = len(text)

            # Estimar tokens deste segmento - ULTRA CONSERVADOR:
            # Português: ~3.5 chars/token, mas usar 2.0 para margem
            # Multiplicador: 0.5 tokens/char (ao invés de real ~0.3)
            estimated_text_tokens = int(text_chars * 0.5)  # 0.5 token por char (conservador)
            json_overhead = 50  # Overhead da estrutura JSON (aumentado para 50)
            segment_tokens = estimated_text_tokens + json_overhead

            # Se adicionar este segmento EXCEDER o limite, fechar batch
            if current_batch and (current_estimated_tokens + segment_tokens > max_output_tokens):
                batches.append(current_batch)
                print(f"   ✓ Batch {len(batches)}: {len(current_batch)} segmentos, ~{current_estimated_tokens} tokens")
                current_batch = []
                current_estimated_tokens = 0

            # Adicionar segmento ao batch atual
            current_batch.append(token)
            current_estimated_tokens += segment_tokens

        # Adicionar último batch
        if current_batch:
            batches.append(current_batch)
            print(f"   ✓ Batch {len(batches)}: {len(current_batch)} segmentos, ~{current_estimated_tokens} tokens")

        # VALIDAÇÃO: Garantir que TODOS os segmentos foram incluídos
        total_segments_in_batches = sum(len(b) for b in batches)
        if total_segments_in_batches != len(tokens):
            raise Exception(
                f"ERRO CRÍTICO: Divisão de batches perdeu segmentos!\n"
                f"Total de segmentos: {len(tokens)}\n"
                f"Segmentos nos batches: {total_segments_in_batches}\n"
                f"Faltando: {len(tokens) - total_segments_in_batches}"
            )

        print(f"   ✅ Validação: {total_segments_in_batches}/{len(tokens)} segmentos em {len(batches)} batches")

        # Se tudo couber em 1 batch, traduzir direto
        if len(batches) == 1:
            if progress_callback:
                progress_callback(f"Traduzindo {len(tokens)} segmentos com Claude...", 50)
            return self._translate_batch(tokens, source, target, dictionary, company_name)

        num_batches = len(batches)

        # Calcular estatísticas dos batches
        avg_segments = sum(len(b) for b in batches) / len(batches) if batches else 0
        min_segments = min(len(b) for b in batches) if batches else 0
        max_segments = max(len(b) for b in batches) if batches else 0

        print(f"\n{'='*80}")
        print(f"📦 ESTRATÉGIA DE TRADUÇÃO:")
        print(f"   Total de segmentos: {len(tokens)}")
        print(f"   Número de requisições: {num_batches}")
        print(f"   Segmentos por batch: mín={min_segments}, máx={max_segments}, média={avg_segments:.0f}")
        print(f"   Modo: {'PARALELO' if use_parallel else 'SEQUENCIAL'} ({self.max_workers} worker{'s' if self.max_workers > 1 else ''})")
        print(f"   💡 Divisão por TAMANHO REAL (não por número fixo)!")
        print(f"{'='*80}\n")

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
                    executor.submit(self._translate_batch_with_rate_limit, batch, source, target, dictionary, company_name): i
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
                        print(f"  ✓ Batch {completed}/{num_batches} completo - {int(rate * 60)} req/min")

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

                # Calcular segmentos já traduzidos
                segments_done = len(all_translations)
                segments_total = len(tokens)

                # Atualizar progresso na UI ANTES de traduzir
                progress_pct = (segments_done / segments_total) * 100
                msg = f"Claude: {segments_done}/{segments_total} segmentos traduzidos (Batch {batch_num}/{num_batches})"
                print(f"  Traduzindo batch {batch_num}/{num_batches} ({len(batch)} segmentos)...")
                if progress_callback:
                    progress_callback(msg, progress_pct)

                try:
                    translations, stats = self._translate_batch(batch, source, target, dictionary, company_name)
                    all_translations.extend(translations)

                    # Acumular estatísticas
                    for key in total_stats:
                        total_stats[key] += stats.get(key, 0)

                    # Atualizar progresso na UI DEPOIS de traduzir (em tempo real!)
                    segments_done = len(all_translations)
                    progress_pct = (segments_done / segments_total) * 100
                    msg = f"Claude: {segments_done}/{segments_total} segmentos traduzidos ✓"
                    if progress_callback:
                        progress_callback(msg, progress_pct)

                except Exception as e:
                    raise Exception(f"Erro no batch {batch_num}/{num_batches}: {str(e)}")

            print(f"✓ Tradução sequencial completa: {len(all_translations)} segmentos traduzidos")

        if progress_callback:
            progress_callback(f"✓ Tradução Claude completa: {len(all_translations)} tokens", 100)

        return all_translations, total_stats

    def _translate_batch_with_rate_limit(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]],
        company_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        Traduz batch respeitando rate limit.
        Usado no processamento paralelo.
        """
        # Aguardar rate limit antes de fazer requisição
        self._wait_for_rate_limit()

        # Traduzir batch
        return self._translate_batch(tokens, source, target, dictionary, company_name)

    def _translate_batch(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]] = None,
        company_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        Traduz um único batch de tokens.

        Args:
            company_name: Nome da empresa que NUNCA deve ser traduzido

        Returns:
            Tuple (traduções, estatísticas)
        """
        if not tokens:
            return [], {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

        # Construir glossário se fornecido - formatado de forma rigorosa
        glossary_text = ""
        if dictionary:
            glossary_text = "\n\n" + "="*80 + "\n"
            glossary_text += "GLOSSÁRIO OBRIGATÓRIO - APLICAR COM PRECISÃO TOTAL\n"
            glossary_text += "="*80 + "\n"
            glossary_text += "ATENÇÃO: Estes termos devem ser traduzidos EXATAMENTE como especificado.\n"
            glossary_text += "Inclui termos técnicos, siglas, abreviações e expressões específicas.\n"
            glossary_text += "Prioridade MÁXIMA sobre tradução automática.\n\n"

            # Ordenar por comprimento (maiores primeiro) para capturar frases completas antes de palavras
            sorted_dict = sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True)

            for term, translation in sorted_dict:
                glossary_text += f"• {term} → {translation}\n"

            glossary_text += "\n" + "="*80 + "\n"

        # Adicionar proteção para nome da empresa
        company_protection = ""
        if company_name and company_name.strip():
            # Extrair palavras individuais do nome da empresa
            company_words = [w.strip() for w in company_name.split() if len(w.strip()) > 2]

            company_protection = f"\n\n" + "🚨"*50 + "\n"
            company_protection += "⛔ COMPANY NAME PROTECTION - CRITICAL RULES ⛔\n"
            company_protection += "🚨"*50 + "\n"
            company_protection += f"PROTECTED COMPANY NAME: {company_name}\n"
            company_protection += f"PROTECTED WORDS (when appearing ALONE): {', '.join(company_words)}\n\n"

            company_protection += "RULE 1 - FULL COMPANY NAME:\n"
            company_protection += f"• When you find '{company_name}' (complete or partial), keep it EXACTLY as is\n"
            company_protection += f"• NEVER translate any part of '{company_name}'\n\n"

            company_protection += "RULE 2 - INDIVIDUAL WORDS (TOKENS):\n"
            company_protection += f"• Protected words: {', '.join(company_words)}\n"
            company_protection += f"• If ANY of these words appears ALONE in a token (without other context), DO NOT translate it\n"
            company_protection += f"• If these words appear WITH CONTEXT in a sentence, you MAY translate them normally\n"
            company_protection += f"• EXCEPTION: If protected words appear in EMAILS, URLS, or CODES, keep them INTACT\n\n"

            company_protection += "EXAMPLES:\n"
            # Exemplo com palavra isolada
            if company_words:
                example_word = company_words[0]
                company_protection += f"  ✓ Token alone: \"{example_word}\" → \"{example_word}\" (NO TRANSLATION)\n"
                company_protection += f"  ✓ With context: \"The {example_word.lower()} was successful\" → \"O {example_word.lower()} foi bem-sucedido\" (TRANSLATE)\n"
                company_protection += f"  ✓ In email: \"user@{example_word.lower()}.com\" → \"user@{example_word.lower()}.com\" (KEEP INTACT)\n"

            company_protection += f"  ✓ Full name: \"{company_name}\" → \"{company_name}\" (NEVER TRANSLATE)\n"
            company_protection += "🚨"*50 + "\n"

        # System prompt com cache (dicionário será cacheado)
        system_prompt = f"""You are a professional translator specialized in contractual and technical documents.
Translate from {source} to {target} with technical and legal precision.

🔴🔴🔴 ABSOLUTE RULE: YOUR RESPONSE = ONLY PURE JSON 🔴🔴🔴

YOUR COMPLETE RESPONSE MUST BE:
{{
  "translations": [...]
}}

❌ DO NOT WRITE IN YOUR RESPONSE:
- Comments like "validation completed"
- Explanations
- Confirmations
- Check mark emojis
- Validation checklists
- NOTHING except the JSON

✅ VALIDATION (DO MENTALLY, DO NOT WRITE):
Before returning, validate MENTALLY (do not write this):
1. I counted {len(tokens)} locations → I must return {len(tokens)} translations
2. There are {len(tokens)-1} commas between the {len(tokens)} objects
3. All quotes are closed
4. Last line ends with: ]}}

❌ COMMON ERRORS (AVOID THESE):
- Triple quotes: \\"\\"\\" → use only \\"
- Parentheses after quotes: "text") → use only "text"}}
- Missing commas: }}}}\n{{{{ → use }}}},\n{{{{
- Semicolons: "; → use only "
- Unclosed strings: "text → use "text"

REQUIRED FORMAT (NO VARIATIONS):
{{
  "translations": [
    {{"location": "LOC1", "translation": "translated text here"}},
    {{"location": "LOC2", "translation": "another translated text"}}
  ]
}}

JSON ESCAPE RULES (MEMORIZE):
1. Double quotes inside text → \\" (ONE backslash, TWO quotes)
    CORRECT: {{"translation": "He said \\"hello\\""}}
    WRONG: {{"translation": "He said \\"\\"\\"hello\\"\\"\\""}}

2. Backslashes → \\\\
    CORRECT: {{"translation": "C:\\\\Users\\\\folder"}}

3. Line breaks → \\n
   CORRECT: {{"translation": "Line 1\\nLine 2"}}

4. DO NOT add characters OUTSIDE quotes
    CORRECT: {{"translation": "text"}}
    WRONG: {{"translation": "text")}}
    WRONG: {{"translation": "text";}}
5. Commas between objects (ALWAYS)
    CORRECT: {{"location": "T1", "translation": "a"}},
              {{"location": "T2", "translation": "b"}}
    WRONG: {{"location": "T1", "translation": "a"}}
              {{"location": "T2", "translation": "b"}}

FINAL VALIDATION (DO MENTALLY):
I counted {len(tokens)} locations → I must return {len(tokens)} translations
 All quotes are closed
 There are {len(tokens)-1} commas between the {len(tokens)} objects
 Last line ends with ]}} (not ], not }}, ONLY ]}})
No extra characters after " (no ), no ;, no .)

TRANSLATION RULES:
1. ALWAYS check the glossary first before translating any term
2. Use EXACTLY the glossary translations when you find the terms
3. Maintain original formatting (uppercase, lowercase, punctuation)
4. Preserve numbers, dates, reference codes, NIUTs
5. Same ORDER as the original texts{company_protection}{glossary_text}

 CRITICAL: Invalid JSON = TOTAL FAILURE. Validate BEFORE returning!"""

        # Preparar tokens em JSON
        tokens_json = json.dumps(tokens, ensure_ascii=False, indent=2)

        # LOG: Mostrar claramente quantos segmentos estamos enviando NESTA requisição
        print(f"   Enviando {len(tokens)} segmentos numa ÚNICA requisição para Claude...")

        try:
            # Chamar Claude com cache no system prompt
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,  # Usar limite correto para cada modelo
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}  # Cache do system prompt
                    }
                ],
                messages=[
                    {"role": "user", "content": f"Traduza estes tokens:\n\n{tokens_json}"}
                ]
            )

            # Extrair resposta
            response_text = message.content[0].text.strip()

            # LOG: Mostrar que recebemos a resposta
            print(f"   Resposta recebida do Claude para os {len(tokens)} segmentos")

            # LIMPEZA AGRESSIVA: Extrair APENAS o JSON puro
            # Remover TUDO antes de { e TUDO depois de }
            import re
            json_match = re.search(r'\{{.*\}}', response_text, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)
                if cleaned != response_text:
                    response_text = cleaned
                    print(f"  🧹 Texto extra removido (antes/depois do JSON)")

            # 🛡️ SISTEMA ANTI-FALHA: Parse JSON com múltiplas tentativas
            translations = self._parse_json_with_retry(
                response_text=response_text,
                tokens=tokens,
                source=source,
                target=target,
                dictionary=dictionary,
                company_name=company_name
            )

            # Calcular estatísticas de uso
            usage = message.usage
            stats = {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
                "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0),
            }

            # Calcular custo
            stats["cost"] = self.calculate_cost(stats)

            return translations, stats

        except anthropic.APIError as e:
            error_str = str(e)
            # Erro 404 geralmente significa modelo inválido
            if "404" in error_str or "not_found" in error_str.lower():
                available_models = ", ".join(self.VALID_MODELS[:3])  # Mostrar apenas os principais
                raise Exception(
                    f"Erro 404 - Modelo não encontrado: '{self.model}'\n\n"
                    f"Modelos principais disponíveis (2026):\n"
                    f"- claude-sonnet-4-5-20250929 (Mais moderno, recomendado)\n"
                    f"- claude-opus-4-5-20251101 (Mais poderoso)\n"
                    f"- claude-haiku-4-5-20251001 (Mais rápido)\n\n"
                    f"Vá para a aba '🤖 Claude API' e selecione um modelo válido.\n\n"
                    f"Erro original: {error_str}"
                )
            raise Exception(f"Erro na API Claude: {error_str}")
        except Exception as e:
            raise Exception(f"Erro ao traduzir documento com Claude: {str(e)}")

    def _parse_json_with_retry(
        self,
        response_text: str,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]],
        company_name: Optional[str]
    ) -> List[Dict[str, str]]:
        """
        🛡️ SISTEMA ANTI-FALHA COMPLETO

        Parse JSON com múltiplas camadas de proteção:
        1. Tentativa normal
        2. Auto-correção de erros comuns
        3. Re-prompt reformulado (se falhar 2x)
        4. Divisão do batch (se extrapolou limites)
        5. Fallback com texto original (NUNCA FALHA)

        Returns:
            Lista de traduções (SEMPRE retorna algo, nunca falha)
        """
        import re
        from datetime import datetime

        # 🔹 TENTATIVA 1: Parse normal
        try:
            # Remover markdown code blocks se existirem
            cleaned = response_text
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            result = json.loads(cleaned)
            translations = result.get("translations", [])

            # VALIDAÇÃO: Remover traduções vazias
            original_count = len(translations)
            translations = [t for t in translations if t.get("translation", "").strip()]
            removed = original_count - len(translations)
            if removed > 0:
                print(f"⚠️ {removed} traduções vazias removidas automaticamente")

            print(f"   ✅ JSON parseado com sucesso ({len(translations)} traduções)")
            return translations

        except json.JSONDecodeError as e:
            print(f"   ⚠️ Erro JSON na tentativa 1: {str(e)[:100]}")

        # 🔹 TENTATIVA 2: Auto-correção de erros comuns
        try:
            print(f"   🔧 Tentando auto-correção de JSON...")
            fixed = response_text
            corrections_made = []

            # 2. Corrigir aspas duplas escapadas duplicadas
            if r'\\"' in fixed:
                fixed = re.sub(r'\\"', r'\"', fixed)
                corrections_made.append("aspas duplas escapadas")

            # 3. Corrigir aspas simples ao invés de duplas
            if "'" in fixed and '"' not in fixed:
                fixed = fixed.replace("'", '"')
                corrections_made.append("aspas simples → duplas")

            # 4. Corrigir vírgulas faltantes entre objetos JSON
            virgula_faltante = re.compile(r'\}\s*\n\s*\{')
            if virgula_faltante.search(fixed):
                fixed = virgula_faltante.sub(r'},\n    {', fixed)
                corrections_made.append("vírgulas faltantes")

            # 5. Corrigir ponto e vírgula antes de chave
            if '";}"' in fixed or "';}" in fixed:
                fixed = fixed.replace('";}"', '"}').replace("';}'", "}")
                corrections_made.append("ponto e vírgula")

            # 6. Remover caracteres de controle inválidos
            fixed = re.sub(r'(?<!\\)\t', ' ', fixed)
            fixed = re.sub(r'(?<!\\)\r', '', fixed)
            fixed = re.sub(r':\s*"([^"]*)\n([^"]*)"', r': "\1\\n\2"', fixed)

            # 7. Corrigir caracteres extras após aspas
            fixed = re.sub(r'"\s*\)(\s*[,\]\}])', r'"\1', fixed)
            fixed = re.sub(r'"\s*;(\s*[,\]\}])', r'"\1', fixed)
            if '")' in response_text or '";' in response_text:
                corrections_made.append("caracteres extras")

            # 8. Escapar aspas não escapadas dentro de valores
            lines_fixed = []
            aspas_corrigidas = False
            for line in fixed.split('\n'):
                if '"location":' in line or '"translation":' in line:
                    quote_count = line.count('"') - line.count('\\"') * 2
                    if quote_count > 4:
                        if '": "' in line:
                            parts = line.split('": "', 1)
                            if len(parts) == 2:
                                key_part = parts[0] + '": "'
                                value_part = parts[1]
                                value_end = '"},' if value_part.endswith('"},') else '"}'
                                value_clean = value_part.rstrip('"},')
                                value_escaped = value_clean.replace('"', '\\"')
                                line = key_part + value_escaped + value_end
                                aspas_corrigidas = True
                lines_fixed.append(line)

            if aspas_corrigidas:
                fixed = '\n'.join(lines_fixed)
                corrections_made.append("aspas não escapadas")

            # Tentar parsear após correções
            result = json.loads(fixed)
            translations = result.get("translations", [])

            # VALIDAÇÃO: Remover traduções vazias
            original_count = len(translations)
            translations = [t for t in translations if t.get("translation", "").strip()]
            removed = original_count - len(translations)
            if removed > 0:
                print(f"⚠️ {removed} traduções vazias removidas")

            if corrections_made:
                print(f"   ✅ JSON corrigido: {', '.join(corrections_made)}")

            return translations

        except Exception as e2:
            print(f"   ⚠️ Auto-correção falhou: {str(e2)[:100]}")

        # 🔹 TENTATIVA 3: Re-prompt com instruções ULTRA simplificadas
        print(f"   🔄 Re-prompt com instruções simplificadas (tentativa 3)...")
        try:
            # Prompt ultra simplificado focado APENAS em JSON válido
            simple_system = f"""You are a translator. Translate from {source} to {target}.

CRITICAL: Return ONLY this JSON structure (no other text):
{{{{
  "translations": [
    {{{{"location": "...", "translation": "..."}}}},
    {{{{"location": "...", "translation": "..."}}}}
  ]
}}}}

Rules:
1. EXACTLY {len(tokens)} translations (one per location)
2. Use double quotes (not single)
3. Escape quotes inside text: \\"
4. Add comma between objects
5. NO text before or after JSON"""

            tokens_json = json.dumps(tokens, ensure_ascii=False, indent=2)

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.1,  # Mais determinístico
                system=[{"type": "text", "text": simple_system}],
                messages=[{"role": "user", "content": f"Translate:\n{tokens_json}"}]
            )

            response_text2 = message.content[0].text.strip()

            # Limpar response
            if response_text2.startswith("```"):
                lines = response_text2.split("\n")
                response_text2 = "\n".join(lines[1:-1])

            # Extrair apenas JSON
            json_match = re.search(r'\{.*\}', response_text2, re.DOTALL)
            if json_match:
                response_text2 = json_match.group(0)

            result = json.loads(response_text2)
            translations = result.get("translations", [])
            translations = [t for t in translations if t.get("translation", "").strip()]

            print(f"   ✅ Re-prompt funcionou! ({len(translations)} traduções)")
            return translations

        except Exception as e3:
            print(f"   ⚠️ Re-prompt falhou: {str(e3)[:100]}")

        # 🔹 TENTATIVA 4: Dividir batch em partes menores
        if len(tokens) > 10 and response_text:  # Só se tiver response_text (não é recursão)
            print(f"   ✂️ Dividindo batch em 2 partes e fazendo novas requisições...")
            try:
                mid = len(tokens) // 2
                batch1 = tokens[:mid]
                batch2 = tokens[mid:]

                # Traduzir primeira metade (faz nova requisição à API)
                print(f"   📤 Traduzindo parte 1/2 ({len(batch1)} tokens)...")
                trans1, _ = self._translate_batch(batch1, source, target, dictionary, company_name)

                # Traduzir segunda metade (faz nova requisição à API)
                print(f"   📤 Traduzindo parte 2/2 ({len(batch2)} tokens)...")
                trans2, _ = self._translate_batch(batch2, source, target, dictionary, company_name)

                print(f"   ✅ Divisão funcionou! ({len(trans1)+len(trans2)} traduções)")
                return trans1 + trans2

            except Exception as e4:
                print(f"   ⚠️ Divisão falhou: {str(e4)[:100]}")

        # 🔹 FALLBACK FINAL: Salvar erro e retornar texto original
        print(f"   ⛔ TODAS as tentativas falharam!")
        print(f"   📝 Usando TEXTO ORIGINAL como fallback (tradução continuará)")

        # Salvar JSON bruto para análise
        try:
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            error_dir = os.path.join(project_root, "claude_json_errors")
            os.makedirs(error_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = os.path.join(error_dir, f"claude_error_{timestamp}.json")

            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"=== TOKENS ENVIADOS ===\n")
                f.write(json.dumps(tokens, ensure_ascii=False, indent=2))
                f.write(f"\n\n=== RESPOSTA RECEBIDA ===\n")
                f.write(response_text)

            print(f"   💾 Erro salvo em: {error_file}")
        except:
            pass

        # Retornar tokens com texto original (NUNCA FALHA)
        fallback_translations = [
            {"location": t["location"], "translation": t["text"]}
            for t in tokens
        ]

        print(f"   ⚠️ Retornando {len(fallback_translations)} textos SEM tradução")
        print(f"   🔄 Tradução continuará com próximo batch...")

        return fallback_translations

    def calculate_cost(self, usage: Dict[str, int]) -> float:
        """
        Calcula custo da chamada em USD.

        Args:
            usage: Dicionário com contadores de tokens

        Returns:
            Custo total em USD
        """
        pricing = self.PRICING.get(self.model, self.PRICING["claude-3-5-sonnet-20241022"])

        input_cost = (usage.get("input_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("output_tokens", 0) / 1_000_000) * pricing["output"]
        cache_write_cost = (usage.get("cache_creation_tokens", 0) / 1_000_000) * pricing["cache_write"]
        cache_read_cost = (usage.get("cache_read_tokens", 0) / 1_000_000) * pricing["cache_read"]

        return input_cost + output_cost + cache_write_cost + cache_read_cost

    def test_connection(self) -> bool:
        """
        Testa conexão com API Claude.

        Returns:
            True se conexão bem-sucedida, False caso contrário
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except:
            return False


if __name__ == "__main__":
    # Teste simples (requer API key)
    import os

    api_key = os.getenv("CLAUDE_API_KEY", "")
    if not api_key:
        print("⚠ Defina CLAUDE_API_KEY para testar")
        exit(1)

    client = ClaudeClient(api_key=api_key)

    print("Testando ClaudeClient...")

    # Testar conexão
    if client.test_connection():
        print("✓ Conexão com Claude bem-sucedida")

        # Testar tradução de documento
        tokens = [
            {"location": "Para1", "text": "Hello, this is a test."},
            {"location": "Para2", "text": "The weather is nice today."},
        ]

        dictionary = {"test": "teste"}

        translations, stats = client.translate_document(
            tokens=tokens,
            source="en",
            target="pt",
            dictionary=dictionary
        )

        print(f"\n✓ Tradução concluída:")
        for trans in translations:
            print(f"  [{trans['location']}] {trans['translation']}")

        print(f"\n📊 Estatísticas:")
        print(f"  Input tokens: {stats['input_tokens']}")
        print(f"  Output tokens: {stats['output_tokens']}")
        print(f"  Cache creation: {stats['cache_creation_tokens']}")
        print(f"  Cache read: {stats['cache_read_tokens']}")
        print(f"  Custo: ${stats['cost']:.6f}")
    else:
        print("✗ Falha ao conectar com Claude")
