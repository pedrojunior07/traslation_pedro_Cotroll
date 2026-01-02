# -*- coding: utf-8 -*-
"""
Cliente direto para LibreTranslate (sem API intermediária).
Permite tradução direta sem passar pelo backend FastAPI.
"""
import requests
from typing import List, Dict, Optional

try:
    from .glossary_processor import GlossaryProcessor
    from .post_processor import DocumentPostProcessor
except ImportError:
    from glossary_processor import GlossaryProcessor
    from post_processor import DocumentPostProcessor


class LibreTranslateClient:
    """Cliente direto para LibreTranslate com suporte a glossário"""

    def __init__(
        self,
        base_url: str = "http://102.211.186.44:5000",
        timeout: float = 30.0,
        glossary: Optional[Dict[str, str]] = None
    ):
        """
        Inicializa cliente LibreTranslate.

        Args:
            base_url: URL base do servidor LibreTranslate (sem /translate no final)
            timeout: Timeout em segundos para requests (padrão: 30s)
            glossary: Dicionário opcional {termo_origem: tradução} para pós-processamento
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.batch_size = 50  # Traduzir no máximo 50 textos por vez

        # Configurar processador de glossário
        self.glossary_processor = None
        if glossary:
            self.set_glossary(glossary)

        # Sempre ativar pós-processador para correções de formatação
        self.post_processor = DocumentPostProcessor()

    def set_glossary(self, glossary: Dict[str, str]) -> None:
        """
        Define glossário para pós-processamento de traduções.

        Args:
            glossary: Dicionário {termo_origem: tradução}
        """
        if glossary:
            self.glossary_processor = GlossaryProcessor(glossary)
            print(f"  ℹ Glossário ativado com {len(glossary)} termos")
        else:
            self.glossary_processor = None

    def translate(self, text: str, source: str, target: str) -> str:
        """
        Traduz texto simples e aplica glossário se configurado.

        Args:
            text: Texto a traduzir
            source: Código do idioma origem (en, pt, fr, etc)
            target: Código do idioma destino

        Returns:
            Texto traduzido (com glossário aplicado se configurado)

        Raises:
            requests.HTTPError: Se houver erro na requisição
        """
        if not text or not text.strip():
            return text

        url = f"{self.base_url}/translate"
        payload = {"q": text, "source": source, "target": target}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Verificar se há erro na resposta
            if "error" in data:
                raise Exception(f"LibreTranslate retornou erro: {data['error']}")

            translated = data.get("translatedText", "")
            if not translated:
                raise Exception(f"LibreTranslate retornou resposta vazia. Payload: {payload}")

            # Aplicar glossário se configurado
            if self.glossary_processor:
                translated, _ = self.glossary_processor.apply_to_text(translated)

            # SEMPRE aplicar pós-processamento de formatação CCS JV
            translated, corrections = self.post_processor.process_text(translated)
            if corrections > 0:
                print(f"  ✓ Pós-processamento aplicou {corrections} correções")

            return translated
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout ao traduzir com LibreTranslate após {self.timeout}s. URL: {url}")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Erro de conexão com LibreTranslate em {self.base_url}: {str(e)}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Erro HTTP {response.status_code} do LibreTranslate: {response.text[:200]}")
        except Exception as e:
            if "LibreTranslate" in str(e):
                raise
            raise Exception(f"Erro ao traduzir com LibreTranslate: {str(e)}\nURL: {url}\nPayload: {payload}")

    def translate_batch(
        self,
        texts: List[str],
        source: str,
        target: str,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """
        Traduz múltiplos textos.

        Se progress_callback for fornecido, traduz um por um mostrando progresso.
        Caso contrário, traduz em lote (chunks de 50 para evitar timeout).

        Args:
            texts: Lista de textos a traduzir
            source: Código do idioma origem
            target: Código do idioma destino
            progress_callback: Função (texto_traduzido, index, total) para progresso

        Returns:
            Lista de textos traduzidos (mesma ordem)

        Raises:
            requests.HTTPError: Se houver erro na requisição
        """
        if not texts:
            return []

        # Filtrar textos vazios mas manter índices
        # Proteção: garantir que todos os itens são strings
        non_empty_indices = []
        for i, t in enumerate(texts):
            if isinstance(t, str) and t and t.strip():
                non_empty_indices.append(i)
            elif not isinstance(t, str):
                # Se não for string, converter ou ignorar
                print(f"  AVISO: Item {i} não é string, é {type(t)}: {t}")

        non_empty_texts = [texts[i] for i in non_empty_indices]

        if not non_empty_texts:
            return texts

        # Se houver callback de progresso, traduzir um por um
        if progress_callback:
            print(f"  LibreTranslate: traduzindo {len(non_empty_texts)} textos um por um...")
            all_translations = []

            for idx, text in enumerate(non_empty_texts):
                translation = self.translate(text, source, target)
                all_translations.append(translation)

                # Chamar callback
                progress_callback(translation, idx + 1, len(non_empty_texts))

            # Reconstruir lista completa
            result = list(texts)
            for i, translation in zip(non_empty_indices, all_translations):
                result[i] = translation

            return result

        # Sem callback - traduzir em lote
        # Se houver muitos textos, dividir em chunks para evitar timeout
        if len(non_empty_texts) > self.batch_size:
            print(f"  LibreTranslate: dividindo {len(non_empty_texts)} textos em chunks de {self.batch_size}...")
            all_translations = []

            for i in range(0, len(non_empty_texts), self.batch_size):
                chunk = non_empty_texts[i:i + self.batch_size]
                chunk_num = (i // self.batch_size) + 1
                total_chunks = (len(non_empty_texts) + self.batch_size - 1) // self.batch_size

                print(f"  LibreTranslate: chunk {chunk_num}/{total_chunks} ({len(chunk)} textos)...")
                chunk_translations = self._translate_batch_single(chunk, source, target)
                all_translations.extend(chunk_translations)

            # Reconstruir lista completa
            result = list(texts)
            for i, translation in zip(non_empty_indices, all_translations):
                result[i] = translation

            return result

        # Batch pequeno - traduzir tudo de uma vez
        return self._translate_batch_single_full(texts, non_empty_indices, non_empty_texts, source, target)

    def _translate_batch_single(self, texts: List[str], source: str, target: str) -> List[str]:
        """
        Traduz um único chunk de textos (usado internamente).

        Returns:
            Lista de traduções (com glossário aplicado se configurado)
        """
        url = f"{self.base_url}/translate"
        payload = {"q": texts, "source": source, "target": target}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Verificar se há erro na resposta
            if isinstance(data, dict) and "error" in data:
                raise Exception(f"LibreTranslate retornou erro: {data['error']}")

            # LibreTranslate retorna lista de dicts: [{"translatedText": "..."}, ...]
            if isinstance(data, list):
                translations = [item.get("translatedText", "") for item in data]

                # Verificar se alguma tradução está vazia
                empty_count = sum(1 for t in translations if not t)
                if empty_count > 0:
                    raise Exception(f"LibreTranslate retornou {empty_count} traduções vazias de {len(translations)}")

                # Aplicar glossário se configurado
                if self.glossary_processor:
                    translations, subs_dict = self.glossary_processor.apply_to_batch(translations)
                    if subs_dict:
                        print(f"  ✓ Glossário aplicou {sum(len(subs) for subs in subs_dict.values())} substituições")

                # SEMPRE aplicar pós-processamento de formatação CCS JV
                translations, total_corrections = self.post_processor.process_batch(translations)
                if total_corrections > 0:
                    print(f"  ✓ Pós-processamento aplicou {total_corrections} correções")

                return translations
            else:
                # Fallback se formato for diferente
                translation = data.get("translatedText", "")

                # Aplicar glossário se configurado
                if self.glossary_processor and translation:
                    translation, _ = self.glossary_processor.apply_to_text(translation)

                return [translation] * len(texts)

        except requests.exceptions.Timeout:
            raise Exception(f"Timeout ao traduzir chunk com LibreTranslate após {self.timeout}s. URL: {url}")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Erro de conexão com LibreTranslate em {self.base_url}: {str(e)}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Erro HTTP {response.status_code} do LibreTranslate: {response.text[:200]}")
        except Exception as e:
            if "LibreTranslate" in str(e):
                raise
            raise Exception(f"Erro ao traduzir chunk com LibreTranslate: {str(e)}\nURL: {url}\nChunk size: {len(texts)}")

    def _translate_batch_single_full(
        self,
        texts: List[str],
        non_empty_indices: List[int],
        non_empty_texts: List[str],
        source: str,
        target: str
    ) -> List[str]:
        """
        Traduz batch completo (quando já filtrado).
        """
        translations = self._translate_batch_single(non_empty_texts, source, target)

        # Reconstruir lista completa com traduções nos índices corretos
        result = list(texts)  # Cópia para preservar textos vazios
        for i, translation in zip(non_empty_indices, translations):
            result[i] = translation

        return result

    def get_languages(self) -> List[Dict[str, str]]:
        """
        Obtém lista de idiomas disponíveis.

        Returns:
            Lista de dicionários com informações dos idiomas
            Formato: [{"code": "en", "name": "English"}, ...]

        Raises:
            requests.HTTPError: Se houver erro na requisição
        """
        url = f"{self.base_url}/languages"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout ao buscar idiomas após {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Erro de conexão com LibreTranslate em {self.base_url}")
        except Exception as e:
            raise Exception(f"Erro ao buscar idiomas: {str(e)}")

    def is_available(self) -> bool:
        """
        Verifica se o servidor LibreTranslate está disponível.

        Returns:
            True se servidor responder, False caso contrário
        """
        try:
            self.get_languages()
            return True
        except:
            return False


if __name__ == "__main__":
    # Teste simples
    client = LibreTranslateClient()

    print("Testando LibreTranslateClient...")

    # Testar disponibilidade
    if client.is_available():
        print("✓ Servidor LibreTranslate disponível")

        # Testar tradução simples
        result = client.translate("Hello World", "en", "pt")
        print(f"✓ Tradução simples: 'Hello World' → '{result}'")

        # Testar tradução em lote
        texts = ["Hello", "Good morning", "Thank you"]
        results = client.translate_batch(texts, "en", "pt")
        print(f"✓ Tradução em lote:")
        for original, translated in zip(texts, results):
            print(f"  '{original}' → '{translated}'")
    else:
        print("✗ Servidor LibreTranslate indisponível")
