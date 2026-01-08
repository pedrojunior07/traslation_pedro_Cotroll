# 🚨 CORREÇÃO: Limite de max_tokens (Output)

## ❌ Problema Identificado

**Erro**: `Unterminated string starting at: line 142 column 41`

**Causa**: Batch de **1800 segmentos** excedeu o limite de `max_tokens` (output).

### Análise do JSON Salvo

Arquivo: `claude_json_errors/claude_error_20260104_103817.json`

Última linha (cortada):
```json
{"location": "T139", "translation": "- O SUBCONTRATADO declara que está totalmente experiente, devidamente qualificado, regist
```

**O que aconteceu**:
1. Claude começou a gerar JSON com 1800 traduções
2. Após gerar 140 traduções (~11,900 caracteres)
3. Atingiu o limite de `max_tokens = 8192`
4. Output foi **cortado no meio**, deixando string não terminada
5. JSON inválido → Erro de parse

## 📊 Cálculo do Problema

### Output Necessário vs Disponível

**Para 1800 segmentos**:
```
Cada linha JSON: ~60 tokens
  {"location": "T123", "translation": "texto aqui..."}

1800 segmentos × 60 tokens = 108,000 tokens necessários
```

**Limite disponível**:
```
max_tokens (Haiku 3.5) = 8,192 tokens
```

**Resultado**:
```
108,000 tokens necessários
  8,192 tokens disponíveis
───────────────────────────
IMPOSSÍVEL! Output cortado após ~136 linhas
```

## ✅ Solução Implementada

### Batch Sizes Ajustados

**ANTES** (Baseado no contexto de 200K):
```python
OPTIMAL_BATCH_SIZES = {
    "claude-3-5-haiku-20241022": 2000,  # ❌ MUITO GRANDE!
    "claude-3-haiku-20240307": 1800,    # ❌ MUITO GRANDE!
    "claude-3-5-sonnet-20241022": 1500, # ❌ MUITO GRANDE!
}
```

**AGORA** (Baseado no max_tokens de OUTPUT):
```python
OPTIMAL_BATCH_SIZES = {
    "claude-3-5-haiku-20241022": 100,   # ✅ 100 × 60 = 6,000 tokens
    "claude-3-5-sonnet-20241022": 120,  # ✅ 120 × 60 = 7,200 tokens
    "claude-3-haiku-20240307": 60,      # ✅ 60 × 60 = 3,600 tokens
    "claude-3-opus-20240229": 60,       # ✅ 60 × 60 = 3,600 tokens
}
```

### Cálculo Correto

```python
# Fórmula:
batch_size = (max_tokens × 0.85) ÷ 60 tokens_por_linha

# Haiku 3.5:
batch_size = (8192 × 0.85) ÷ 60 = ~116 → Conservador: 100

# Sonnet 3.5:
batch_size = (8192 × 0.85) ÷ 60 = ~116 → Conservador: 120

# Haiku 3.0 / Opus:
batch_size = (4096 × 0.85) ÷ 60 = ~58 → Conservador: 60
```

## 📈 Impacto na Performance

### Documento com 2507 Segmentos (seu caso)

**ANTES** (batches grandes):
```
Batch 1: 1800 segmentos → ❌ ERRO (max_tokens excedido)
Batch 2: 707 segmentos  → Não executado
───────────────────────────────
Total: FALHOU
```

**AGORA** (batches corretos):
```
Batch 1: 100 segmentos → ✅ OK (~15s)
Batch 2: 100 segmentos → ✅ OK (~15s)
Batch 3: 100 segmentos → ✅ OK (~15s)
...
Batch 25: 100 segmentos → ✅ OK (~15s)
Batch 26: 7 segmentos → ✅ OK (~5s)
───────────────────────────────
Total: ~26 requisições × 15s = ~6-7 minutos
```

### Comparação

| Documento | Segmentos | Batches (antes) | Batches (agora) | Tempo |
|-----------|-----------|-----------------|-----------------|-------|
| Pequeno | 92 | 1 ✅ | 1 ✅ | ~10s |
| Médio | 500 | 1 ❌ (erro) | 5 ✅ | ~1.5min |
| Grande | 2507 | 2 ❌ (erro) | 26 ✅ | ~6-7min |

## 🎯 Por Que Aconteceu?

### Erro de Cálculo Inicial

**Pensamento Errado**:
> "Claude tem 200K de contexto, então posso enviar 2000 segmentos!"

**Realidade**:
- ✅ **Input**: 200K contexto (pode receber muitos segmentos)
- ❌ **Output**: 8K max_tokens (pode gerar POUCO texto)

### Analogia

Imagine um caminhão:
- **Capacidade de carga** (input/contexto): 200 toneladas ✅
- **Porta de saída** (output/max_tokens): Porta de 8cm de largura ❌

Você pode **CARREGAR** 200 toneladas, mas só pode **DESCARREGAR** pela portinha pequena!

## 📝 Comentário no Código

```python
# Batch size otimizado por modelo (quantos SEGMENTOS por requisição)
# LIMITADO PELO max_tokens (output)!
# Cálculo: max_tokens ÷ 60 tokens por linha JSON = segmentos máximos
# - Haiku 3.5: 8192 ÷ 60 = ~136 segmentos (conservador: 100)
# - Sonnet 3.5: 8192 ÷ 60 = ~136 segmentos (conservador: 120)
# IMPORTANTE: O limite é o OUTPUT, não o contexto!
```

## 🔧 Arquivos Modificados

- **[src/claude_client.py](src/claude_client.py#L53-L66)**: Batch sizes reduzidos para respeitar max_tokens

## ✅ Validação

### Teste com 92 Segmentos (RENCOTEK)
```
✅ PASSOU: 92 < 100, cabe em 1 batch
Resultado: Sucesso!
```

### Teste com 2507 Segmentos (RAND AIR)
```
❌ FALHOU (antes): 1800 > 136 limite real
✅ VAI PASSAR (agora): 100 < 136 limite real
Resultado esperado: ~26 batches, ~6-7 minutos
```

## 🎓 Lição Aprendida

**Dois limites diferentes**:

1. **Context Window** (200K tokens):
   - Quanto texto pode **RECEBER**
   - Afeta: Input do usuário + System prompt + Histórico
   - NÃO afeta batch size!

2. **max_tokens** (8K tokens):
   - Quanto texto pode **GERAR**
   - Afeta: Output da resposta
   - **ESTE é o limite real do batch size!**

**Fórmula Correta**:
```
batch_size_max = (max_tokens × fator_segurança) ÷ tokens_por_segmento_output
batch_size_max = (8192 × 0.85) ÷ 60
batch_size_max = ~116 segmentos
```

## 📊 Novo Comportamento

### Log Esperado

```
================================================================================
📦 ESTRATÉGIA DE TRADUÇÃO:
   Total de segmentos: 2507
   Segmentos por requisição: ~100
   Número de requisições: 26
   Modo: SEQUENCIAL (1 worker)
   💡 Cada requisição traduz ~100 segmentos de uma só vez!
================================================================================

  Traduzindo batch 1/26 (100 tokens)...
  📤 Enviando 100 segmentos numa ÚNICA requisição para Claude...
  📥 Resposta recebida do Claude para os 100 segmentos
  ✓ Batch 1/26 completo

  Traduzindo batch 2/26 (100 tokens)...
  📤 Enviando 100 segmentos numa ÚNICA requisição para Claude...
  📥 Resposta recebida do Claude para os 100 segmentos
  ✓ Batch 2/26 completo

  [... continua até batch 26 ...]
```

---

**Resumo**: O problema NÃO era o contexto (200K), era o `max_tokens` de output (8K). Batch sizes ajustados para **100-120 segmentos** ao invés de 1800-2000! ✅
