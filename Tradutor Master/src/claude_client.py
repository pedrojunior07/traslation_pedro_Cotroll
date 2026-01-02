# -*- coding: utf-8 -*-
"""
Cliente direto para Anthropic Claude.
Permite tradução de documentos completos com otimização de tokens via cache.
"""
import json
from typing import List, Dict, Optional, Tuple
import anthropic


class ClaudeClient:
    """Cliente direto para Anthropic Claude com suporte a cache de prompts"""

    # Preços por 1M tokens (em USD)
    PRICING = {
        # Sonnet 3.5 (versões disponíveis)
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
        "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
        # Opus 3
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
        # Sonnet 3 (versão antiga)
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
        # Haiku 3
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25, "cache_write": 0.30, "cache_read": 0.03},
    }

    # Limites de max_tokens por modelo
    MAX_TOKENS_LIMITS = {
        "claude-3-5-sonnet-20241022": 8192,
        "claude-3-5-sonnet-20240620": 8192,
        "claude-3-opus-20240229": 4096,
        "claude-3-sonnet-20240229": 4096,
        "claude-3-haiku-20240307": 4096,
    }

    # Modelos válidos (para validação)
    VALID_MODELS = list(PRICING.keys())

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", timeout: float = 120.0):
        """
        Inicializa cliente Claude.

        Args:
            api_key: API key da Anthropic
            model: Modelo Claude a usar
            timeout: Timeout em segundos
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

    def translate_document(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]] = None,
        batch_size: int = 100,
        progress_callback: Optional[callable] = None
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

        # Se houver poucos tokens, traduzir tudo de uma vez
        if len(tokens) <= batch_size:
            if progress_callback:
                progress_callback(f"Traduzindo {len(tokens)} tokens com Claude...", 50)
            return self._translate_batch(tokens, source, target, dictionary)

        # Dividir em batches e traduzir
        all_translations = []
        total_stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "cost": 0.0
        }

        num_batches = (len(tokens) + batch_size - 1) // batch_size
        print(f"📦 Dividindo {len(tokens)} tokens em {num_batches} batches de ~{batch_size} tokens")

        for i in range(0, len(tokens), batch_size):
            batch = tokens[i:i + batch_size]
            batch_num = (i // batch_size) + 1

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

        print(f"✓ Tradução completa: {len(all_translations)} tokens traduzidos")
        if progress_callback:
            progress_callback(f"✓ Tradução Claude completa: {len(all_translations)} tokens", 100)

        return all_translations, total_stats

    def _translate_batch(
        self,
        tokens: List[Dict[str, str]],
        source: str,
        target: str,
        dictionary: Optional[Dict[str, str]] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        Traduz um único batch de tokens.

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

        # System prompt com cache (dicionário será cacheado)
        system_prompt = f"""Você é um tradutor profissional especializado em documentos contratuais e técnicos.
Traduza de {source} para {target} com precisão técnica e legal.

IMPORTANTE: Retorne APENAS JSON válido, sem texto antes ou depois.

FORMATO OBRIGATÓRIO:
{{
  "translations": [
    {{"location": "LOC1", "translation": "texto traduzido aqui"}},
    {{"location": "LOC2", "translation": "outro texto traduzido"}}
  ]
}}

REGRAS DE ESCAPE (CRÍTICO):
1. Aspas duplas dentro do texto → use \\"
   Exemplo: {{"translation": "Ele disse \\"olá\\""}}

2. Barras invertidas → use \\\\
   Exemplo: {{"translation": "C:\\\\Users\\\\pasta"}}

3. Quebras de linha → use \\n (não quebrar linha real)
   Exemplo: {{"translation": "Linha 1\\nLinha 2"}}

4. NUNCA deixe strings abertas - sempre feche com "

EXEMPLO COMPLETO:
Input: [{{"location": "A", "text": "Hello \\"World\\""}}, {{"location": "B", "text": "Line 1\\nLine 2"}}]
Output: {{
  "translations": [
    {{"location": "A", "translation": "Olá \\"Mundo\\""}},
    {{"location": "B", "translation": "Linha 1\\nLinha 2"}}
  ]
}}

REGRAS DE TRADUÇÃO:
1. SEMPRE consulte o glossário primeiro antes de traduzir qualquer termo
2. Use EXATAMENTE as traduções do glossário quando encontrar os termos
3. Mantenha formatação original (maiúsculas, minúsculas, pontuação)
4. Preserve números, datas, códigos de referência, NIUTs
5. Siglas: mantenha conforme glossário (ex: "VAT" → "IVA", "TAX ID" → "NUIT")
6. Abreviações: aplique conforme glossário (ex: "Tel. No." → "Tel.")
7. Expressões contratuais: use termos formais (ex: "shall be" → "deverá ser")
8. Nomes de empresas e locais: adapte apenas quando especificado no glossário
9. Mesma ORDEM dos textos originais
10. Preserve estrutura e quebras de linha{glossary_text}

EXEMPLOS DE APLICAÇÃO DO GLOSSÁRIO:
- "Purchase Order No. 31628809" → "Ordem de Compra n.º 31628809"
- "TAX ID: 401015418" → "NUIT: 401015418"
- "Tel. No.: +258843118753" → "Tel.: +258843118753"
- "Vendor code: 172248" → "Código do Fornecedor: 172248"
- "Subject: PROVISION OF MEDICAL SERVICES" → "Assunto: PROVISÃO DOS SERVIÇOS MÉDICOS"
- "Our reference: Work Order No. 31628809" → "Nossa referência: Ordem de Serviço n.º 31628809"

ATENÇÃO CRÍTICA:
- JSON inválido = erro fatal. Valide mentalmente antes de enviar.
- Glossário tem PRIORIDADE ABSOLUTA sobre qualquer outra regra de tradução.
- Revise cada termo para garantir que está no glossário antes de usar tradução automática."""

        # Preparar tokens em JSON
        tokens_json = json.dumps(tokens, ensure_ascii=False, indent=2)

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

            # Parse JSON da resposta
            try:
                # Remover markdown code blocks se existirem
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    response_text = "\n".join(lines[1:-1])  # Remove primeira e última linha

                result = json.loads(response_text)
                translations = result.get("translations", [])
            except json.JSONDecodeError as e:
                # Tentar consertar JSON comum: aspas simples ao invés de duplas
                try:
                    # Substituir aspas simples por duplas (caso comum)
                    fixed = response_text.replace("'", '"')
                    result = json.loads(fixed)
                    translations = result.get("translations", [])
                except:
                    # Salvar JSON bruto em arquivo para análise
                    import os
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', prefix='claude_error_', encoding='utf-8') as f:
                        f.write(response_text)
                        error_file = f.name

                    # Se ainda falhar, mostrar erro detalhado
                    error_msg = f"Erro ao fazer parse da resposta Claude: {str(e)}\n\n"
                    error_msg += f"Resposta recebida (primeiros 1000 chars):\n{response_text[:1000]}\n\n"
                    error_msg += f"JSON bruto salvo em: {error_file}\n\n"
                    error_msg += "DICA: O Claude retornou JSON inválido. Tente novamente ou use um modelo diferente."
                    raise Exception(error_msg)

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
                    f"Modelos principais disponíveis:\n"
                    f"- claude-3-5-sonnet-20241022 (Mais recente, recomendado)\n"
                    f"- claude-3-opus-20240229 (Mais poderoso)\n"
                    f"- claude-3-haiku-20240307 (Mais rápido)\n\n"
                    f"Vá para a aba '🤖 Claude API' e selecione um modelo válido.\n\n"
                    f"Erro original: {error_str}"
                )
            raise Exception(f"Erro na API Claude: {error_str}")
        except Exception as e:
            raise Exception(f"Erro ao traduzir documento com Claude: {str(e)}")

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
