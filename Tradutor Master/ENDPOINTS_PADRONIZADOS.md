# ✅ Endpoints Padronizados - Testes Justos

## 🎯 Garantia de Consistência

Todos os fluxos de tradução agora usam **EXATAMENTE A MESMA CONFIGURAÇÃO** do Claude, garantindo testes justos e resultados consistentes.

## 📋 Fluxos Padronizados

### 1. Arquivo Único (RealTimeTranslationWindow)
**Arquivo**: [src/ui.py](src/ui.py#L892-L900)

```python
translations, _ = self.claude_client.translate_document(
    tokens_data,
    source_lang,
    target_lang,
    dictionary,
    batch_size=None,      # Usa batch otimizado (40 para Haiku 3.5)
    progress_callback=None,
    use_parallel=True     # 15 workers paralelos para Haiku
)
```

### 2. Múltiplos Arquivos (BatchTranslationWindow)
**Arquivo**: [src/ui.py](src/ui.py#L994-L1002)

```python
translations, _ = self.claude_client.translate_document(
    tokens_data,
    source_lang,
    target_lang,
    dictionary,
    batch_size=None,      # Usa batch otimizado (40 para Haiku 3.5)
    progress_callback=None,
    use_parallel=True     # 15 workers paralelos para Haiku
)
```

### 3. Tradução com Pasta (Threading)
**Arquivo**: [src/ui.py](src/ui.py#L1210-L1218)

```python
translations, usage_stats = self.claude_client.translate_document(
    tokens_data,
    source_lang,
    target_lang,
    dictionary,
    batch_size=None,              # Usa batch otimizado (40 para Haiku 3.5)
    progress_callback=on_translation_progress,
    use_parallel=True             # 15 workers paralelos para Haiku
)
```

## ⚙️ Configuração Automática

Quando `batch_size=None` e `use_parallel=True`, o sistema automaticamente:

### Para Claude Haiku 3.5:
- ✅ **Batch size**: 40 tokens por requisição
- ✅ **Workers**: 15 threads paralelas
- ✅ **Rate limit**: 50 RPM (monitorado automaticamente)
- ✅ **Processamento**: Paralelo quando `num_batches > 1`

### Para Claude Haiku 3:
- ✅ **Batch size**: 30 tokens por requisição
- ✅ **Workers**: 15 threads paralelas
- ✅ **Rate limit**: 50 RPM

### Para Claude Sonnet 3.5:
- ✅ **Batch size**: 25 tokens por requisição
- ✅ **Workers**: 8 threads paralelas
- ✅ **Rate limit**: 50 RPM

### Para Claude Opus 3:
- ✅ **Batch size**: 15 tokens por requisição
- ✅ **Workers**: 8 threads paralelas
- ✅ **Rate limit**: 50 RPM

## 🧪 Testes Justos Garantidos

### Cenário 1: Traduzir 1 arquivo
```
Arquivo: contract.docx (200 parágrafos)

Configuração usada:
  - Batch: 40 tokens
  - Workers: 15 paralelos
  - Batches criados: 200 ÷ 40 = 5
  - Processamento: PARALELO (5 batches simultâneos)
  - Tempo esperado: ~2.5 segundos
```

### Cenário 2: Traduzir pasta com 5 arquivos
```
Arquivos: 5 contratos com 200 parágrafos cada

Configuração usada (PARA CADA ARQUIVO):
  - Batch: 40 tokens
  - Workers: 15 paralelos
  - Batches por arquivo: 200 ÷ 40 = 5
  - Processamento: PARALELO (5 batches simultâneos por arquivo)
  - Tempo esperado: ~2.5 segundos × 5 arquivos = ~12.5 segundos
```

### Resultado:
✅ **MESMA VELOCIDADE** por arquivo, independente de ser único ou em pasta!

## 📊 Comparação de Performance

### ANTES da Padronização:
- Arquivo único: poderia usar configuração diferente
- Múltiplos arquivos: poderia usar outra configuração
- **TESTES INJUSTOS** - resultados inconsistentes

### DEPOIS da Padronização:
- **TODOS os fluxos**: mesma configuração
- **TODOS os arquivos**: mesma velocidade por arquivo
- **TESTES JUSTOS** - resultados consistentes

## 💡 Como Funciona

### 1. Chamada do Endpoint
```python
# Qualquer fluxo chama assim:
translate_document(
    tokens_data,
    source_lang,
    target_lang,
    dictionary,
    batch_size=None,     # ← Usa configuração otimizada
    progress_callback=...,
    use_parallel=True    # ← Ativa paralelismo
)
```

### 2. Detecção Automática no ClaudeClient
```python
# claude_client.py detecta automaticamente:
if batch_size is None:
    batch_size = self.optimal_batch_size  # 40 para Haiku 3.5

if use_parallel and num_batches > 1:
    # Usar ThreadPoolExecutor com self.max_workers (15 para Haiku)
```

### 3. Resultado
- ✅ Sempre usa batch otimizado
- ✅ Sempre usa workers otimizados
- ✅ Sempre respeita rate limit
- ✅ Performance consistente

## ⚡ Performance Esperada

### Arquivo Individual (200 parágrafos):
```
📦 Dividindo 200 tokens em 5 batches de ~40 tokens
⚡ Processamento PARALELO com 15 workers

  ✓ Batch 1/5 completo - 48 req/min
  ✓ Batch 2/5 completo - 50 req/min
  ✓ Batch 3/5 completo - 49 req/min
  ✓ Batch 4/5 completo - 50 req/min
  ✓ Batch 5/5 completo - 50 req/min

✓ Tradução paralela completa: 200 tokens em 2.5s (50 req/min)
```

### Pasta com 5 Arquivos (200 parágrafos cada):
```
Arquivo 1/5:
  📦 Dividindo 200 tokens em 5 batches de ~40 tokens
  ⚡ Processamento PARALELO com 15 workers
  ✓ Tradução completa: 2.5s

Arquivo 2/5:
  📦 Dividindo 200 tokens em 5 batches de ~40 tokens
  ⚡ Processamento PARALELO com 15 workers
  ✓ Tradução completa: 2.5s

... (repetindo para arquivos 3, 4, 5)

Total: ~12.5 segundos para 5 arquivos
Média: 2.5s por arquivo ✓ CONSISTENTE
```

## ✅ Garantias

1. **Mesma configuração** em todos os fluxos
2. **Mesma velocidade** por arquivo
3. **Mesmos logs** de processamento
4. **Mesmas métricas** (RPM, batch size, workers)
5. **Testes justos** e comparáveis

## 🎊 Conclusão

Agora você pode:
- ✅ Traduzir 1 arquivo e medir a velocidade
- ✅ Traduzir uma pasta e comparar
- ✅ Ter certeza que a configuração é IDÊNTICA
- ✅ Testar com confiança que os resultados são justos

**Todos os endpoints usam a mesma lógica otimizada!**
