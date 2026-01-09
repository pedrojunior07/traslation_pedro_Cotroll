# -*- coding: utf-8 -*-
"""
Cliente direto para OpenAI Chat Completions.
Mantem a mesma estrutura de prompt usada no Claude.
"""
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import requests


class OpenAIClient:
    """Cliente direto para OpenAI com suporte a batches e parse robusto."""

    MAX_TOKENS_LIMITS = {
        "gpt-4o-mini": 4096,
        "gpt-4o": 4096,
    }
    MAX_WORKERS = {
        "gpt-4o-mini": 25,
        "gpt-4o": 25,
    }

    VALID_MODELS = list(MAX_TOKENS_LIMITS.keys())

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
        max_workers: int = None,
    ):
        if not api_key:
            raise ValueError("API key e obrigatoria")

        if model not in self.VALID_MODELS:
            available = ", ".join(self.VALID_MODELS)
            raise ValueError(
                f"Modelo '{model}' nao e valido.\n\n"
                f"Modelos disponiveis:\n{available}"
            )

        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_tokens = self.MAX_TOKENS_LIMITS.get(model, 4096)
        if max_workers is None:
            max_workers = self.MAX_WORKERS.get(model, 2)
        self.max_workers = max_workers

        self._request_times = []
        self._lock = threading.Lock()

        print("OpenAI Client inicializado:")
        print(f"   Modelo: {self.model}")
        print(f"   Max tokens: {self.max_tokens}")
        print(f"   Workers paralelos: {self.max_workers}")

    def _wait_for_rate_limit(self) -> None:
        with self._lock:
            now = time.time()
            self._request_times = [t for t in self._request_times if now - t < 60]
            self._request_times.append(time.time())

    def _create_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int, temperature: float = 0.0):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            raise Exception(f"Erro na API OpenAI ({resp.status_code}): {resp.text}")
        return resp.json()

    def translate_document(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]] = None,
        batch_size: int = None,
        progress_callback: Optional[callable] = None,
        use_parallel: bool = True,
        company_name: Optional[str] = None,
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        if not tokens:
            return [], {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

        max_output_tokens = int(self.max_tokens * 0.30)

        print(f"\nOpenAI: iniciando traduÇao de {len(tokens)} segmentos")

        batches = []
        current_batch = []
        current_estimated_tokens = 0

        for token in tokens:
            text = token.get("text", "")
            text_chars = len(text)
            estimated_text_tokens = int(text_chars * 0.5)
            json_overhead = 50
            segment_tokens = estimated_text_tokens + json_overhead

            if current_batch and (current_estimated_tokens + segment_tokens > max_output_tokens):
                batches.append(current_batch)
                current_batch = []
                current_estimated_tokens = 0

            current_batch.append(token)
            current_estimated_tokens += segment_tokens

        if current_batch:
            batches.append(current_batch)

        print(f"OpenAI: {len(batches)} batch(es) gerados para o arquivo")

        total_segments_in_batches = sum(len(b) for b in batches)
        if total_segments_in_batches != len(tokens):
            raise Exception(
                "ERRO CRITICO: Divisao de batches perdeu segmentos!"
            )

        if len(batches) == 1:
            if progress_callback:
                progress_callback(f"Traduzindo {len(tokens)} segmentos com OpenAI...", 50)
            return self._translate_batch(tokens, source, target, dictionary, company_name)

        num_batches = len(batches)
        all_translations = []
        total_stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "cost": 0.0,
        }

        if use_parallel and num_batches > 1:
            completed = 0
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_batch = {
                    executor.submit(
                        self._translate_batch_with_rate_limit,
                        batch,
                        source,
                        target,
                        dictionary,
                        company_name,
                    ): i
                    for i, batch in enumerate(batches)
                }

                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        translations, stats = future.result()
                        all_translations.extend(translations)
                        for key in total_stats:
                            total_stats[key] += stats.get(key, 0)

                        completed += 1
                        progress_pct = (completed / num_batches) * 100
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        eta = (num_batches - completed) / rate if rate > 0 else 0
                        msg = f"OpenAI: {completed}/{num_batches} batches ({int(rate * 60):.0f} req/min, ETA: {eta:.0f}s)"
                        print(f"OpenAI: batch {completed}/{num_batches} completo ({progress_pct:.0f}%)")
                        if progress_callback:
                            progress_callback(msg, progress_pct)
                    except Exception as e:
                        raise Exception(f"Erro no batch {batch_idx + 1}/{num_batches}: {str(e)}")
        else:
            for i, batch in enumerate(batches):
                batch_num = i + 1
                segments_done = len(all_translations)
                segments_total = len(tokens)
                progress_pct = (segments_done / segments_total) * 100
                msg = f"OpenAI: {segments_done}/{segments_total} segmentos (Batch {batch_num}/{num_batches})"
                if progress_callback:
                    progress_callback(msg, progress_pct)

                translations, stats = self._translate_batch(batch, source, target, dictionary, company_name)
                all_translations.extend(translations)
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)

                segments_done = len(all_translations)
                progress_pct = (segments_done / segments_total) * 100
                msg = f"OpenAI: {segments_done}/{segments_total} segmentos traduzidos"
                print(f"OpenAI: batch {batch_num}/{num_batches} completo ({progress_pct:.0f}%)")
                if progress_callback:
                    progress_callback(msg, progress_pct)

        if progress_callback:
            progress_callback(f"OpenAI: traducao completa: {len(all_translations)} tokens", 100)

        print(f"OpenAI: traduÇao completa ({len(all_translations)} segmentos)")

        return all_translations, total_stats

    def _translate_batch_with_rate_limit(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]],
        company_name: Optional[str] = None,
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        self._wait_for_rate_limit()
        return self._translate_batch(tokens, source, target, dictionary, company_name)

    def _translate_batch(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]] = None,
        company_name: Optional[str] = None,
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        if not tokens:
            return [], {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

        glossary_text = ""
        if dictionary:
            glossary_text = "\n\n" + "=" * 80 + "\n"
            glossary_text += "GLOSSARIO OBRIGATORIO - APLICAR COM PRECISAO TOTAL\n"
            glossary_text += "=" * 80 + "\n"
            glossary_text += "ATENCAO: Estes termos devem ser traduzidos EXATAMENTE como especificado.\n"
            glossary_text += "Inclui termos tecnicos, siglas, abreviacoes e expressoes especificas.\n"
            glossary_text += "Prioridade MAXIMA sobre traducao automatica.\n\n"

            sorted_dict = sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True)
            for term, translation in sorted_dict:
                glossary_text += f"- {term} -> {translation}\n"

            glossary_text += "\n" + "=" * 80 + "\n"

        company_protection = ""
        if company_name and company_name.strip():
            company_words = [w.strip() for w in company_name.split() if len(w.strip()) > 2]
            company_protection = "\n\n" + "#" * 50 + "\n"
            company_protection += "COMPANY NAME PROTECTION - CRITICAL RULES\n"
            company_protection += "#" * 50 + "\n"
            company_protection += f"PROTECTED COMPANY NAME: {company_name}\n"
            company_protection += f"PROTECTED WORDS (when appearing ALONE): {', '.join(company_words)}\n\n"
            company_protection += "RULE 1 - FULL COMPANY NAME:\n"
            company_protection += f"- When you find '{company_name}' (complete or partial), keep it EXACTLY as is\n"
            company_protection += f"- NEVER translate any part of '{company_name}'\n\n"
            company_protection += "RULE 2 - INDIVIDUAL WORDS:\n"
            company_protection += "- If a single protected word appears alone, keep it unchanged\n"
            company_protection += "#" * 50 + "\n"

        system_prompt = f"""You are a professional translator specialized in contractual and technical documents.
Translate from {source} to {target} with technical and legal precision.

LANGUAGE AND CONTEXT:
1. Use European Portuguese (pt-PT) by default.
2. Apply Mozambique context and terminology (institutions, legal/administrative terms, local usage).
3. Never convert Mozambican terms to Brazilian variants.
4. Tax ID must always be "NUIT" (never "NIF").

ABSOLUTE RULE: YOUR RESPONSE = ONLY PURE JSON

YOUR COMPLETE RESPONSE MUST BE:
{{
  "translations": [...]
}}

DO NOT WRITE IN YOUR RESPONSE:
- Comments like "validation completed"
- Explanations
- Confirmations
- Check mark emojis
- NOTHING except the JSON

VALIDATION (DO MENTALLY, DO NOT WRITE):
Before returning, validate MENTALLY (do not write this):
1. I counted {len(tokens)} locations -> I must return {len(tokens)} translations
2. There are {len(tokens)-1} commas between the {len(tokens)} objects
3. All quotes are closed
4. Last line ends with: ]}}

COMMON ERRORS (AVOID THESE):
- Triple quotes: \"\"\" -> use only \"
- Parentheses after quotes: "text") -> use only "text"}}
- Missing commas: }}\n{{ -> use }},\n{{
- Semicolons: "; -> use only "
- Unclosed strings: "text -> use "text"

REQUIRED FORMAT (NO VARIATIONS):
{{
  "translations": [
    {{"location": "LOC1", "translation": "translated text here"}},
    {{"location": "LOC2", "translation": "another translated text"}}
  ]
}}

JSON ESCAPE RULES (MEMORIZE):
1. Double quotes inside text -> \\"
    CORRECT: {{"translation": "He said \\\"hello\\\""}}
    WRONG: {{"translation": "He said \\\"\\\"\\\"hello\\\"\\\"\\\""}}

2. Backslashes -> \\\\
    CORRECT: {{"translation": "C:\\\\Users\\\\folder"}}

3. Line breaks -> \\n
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
I counted {len(tokens)} locations -> I must return {len(tokens)} translations
All quotes are closed
There are {len(tokens)-1} commas between the {len(tokens)} objects
Last line ends with ]}} (not ], not }}, ONLY ]}})
No extra characters after " (no ), no ;, no .)

TRANSLATION RULES:
1. ALWAYS check the glossary first before translating any term
2. Use EXACTLY the glossary translations when you find the terms
3. Maintain original formatting (uppercase, lowercase, punctuation)
4. Preserve numbers, dates, reference codes, NIUTs
5. IMPORTANT: Keep the token "NUIT" exactly as NUIT (never translate to NIF)
6. Same ORDER as the original texts{company_protection}{glossary_text}

CRITICAL: Invalid JSON = TOTAL FAILURE. Validate BEFORE returning!"""

        tokens_json = json.dumps(tokens, ensure_ascii=False, indent=2)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Traduza estes tokens:\n\n{tokens_json}"},
        ]

        data = self._create_chat_completion(messages, max_tokens=self.max_tokens, temperature=0.0)
        response_text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        translations = self._parse_json_with_retry(
            response_text=response_text,
            tokens=tokens,
            source=source,
            target=target,
            dictionary=dictionary,
            company_name=company_name,
        )

        usage = data.get("usage", {})
        stats = {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "cost": 0.0,
        }

        return translations, stats

    def _parse_json_with_retry(
        self,
        response_text: str,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]],
        company_name: Optional[str],
    ) -> List[Dict[str, str]]:
        import re
        from datetime import datetime

        try:
            cleaned = response_text
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            result = json.loads(cleaned)
            translations = result.get("translations", [])
            translations = [t for t in translations if t.get("translation", "").strip()]
            return translations
        except json.JSONDecodeError:
            pass

        try:
            fixed = response_text
            fixed = re.sub(r'\\"', r'\"', fixed)
            fixed = re.sub(r'\}\s*\n\s*\{', r'},\n    {', fixed)
            fixed = re.sub(r'"\s*\)(\s*[,\]\}])', r'"\1', fixed)
            fixed = re.sub(r'"\s*;(\s*[,\]\}])', r'"\1', fixed)
            fixed = re.sub(r'(?<!\\)\t', ' ', fixed)
            fixed = re.sub(r'(?<!\\)\r', '', fixed)
            fixed = re.sub(r':\s*"([^"]*)\n([^"]*)"', r': "\1\\n\2"', fixed)

            result = json.loads(fixed)
            translations = result.get("translations", [])
            translations = [t for t in translations if t.get("translation", "").strip()]
            return translations
        except Exception:
            pass

        try:
            simple_system = f"""You are a translator. Translate from {source} to {target}.

CRITICAL: Return ONLY this JSON structure (no other text):
{{
  "translations": [
    {{"location": "...", "translation": "..."}},
    {{"location": "...", "translation": "..."}}
  ]
}}

Rules:
1. EXACTLY {len(tokens)} translations (one per location)
2. Use double quotes (not single)
3. Escape quotes inside text: \\"
4. Add comma between objects
5. NO text before or after JSON"""

            tokens_json = json.dumps(tokens, ensure_ascii=False, indent=2)
            messages = [
                {"role": "system", "content": simple_system},
                {"role": "user", "content": f"Translate:\n{tokens_json}"},
            ]
            data = self._create_chat_completion(messages, max_tokens=self.max_tokens, temperature=0.1)
            response_text2 = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if response_text2.startswith("```"):
                lines = response_text2.split("\n")
                response_text2 = "\n".join(lines[1:-1])

            json_match = re.search(r'\{.*\}', response_text2, re.DOTALL)
            if json_match:
                response_text2 = json_match.group(0)

            result = json.loads(response_text2)
            translations = result.get("translations", [])
            translations = [t for t in translations if t.get("translation", "").strip()]
            return translations
        except Exception:
            pass

        if len(tokens) > 10 and response_text:
            try:
                mid = len(tokens) // 2
                batch1 = tokens[:mid]
                batch2 = tokens[mid:]

                trans1, _ = self._translate_batch(batch1, source, target, dictionary, company_name)
                trans2, _ = self._translate_batch(batch2, source, target, dictionary, company_name)
                return trans1 + trans2
            except Exception:
                pass

        try:
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            error_dir = os.path.join(project_root, "openai_json_errors")
            os.makedirs(error_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = os.path.join(error_dir, f"openai_error_{timestamp}.json")

            with open(error_file, "w", encoding="utf-8") as f:
                f.write("=== TOKENS ENVIADOS ===\n")
                f.write(json.dumps(tokens, ensure_ascii=False, indent=2))
                f.write("\n\n=== RESPOSTA RECEBIDA ===\n")
                f.write(response_text)
        except Exception:
            pass

        return [{"location": t["location"], "translation": t["text"]} for t in tokens]

    def test_connection(self) -> bool:
        try:
            data = self._create_chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10,
                temperature=0.0,
            )
            return bool(data.get("choices"))
        except Exception:
            return False
