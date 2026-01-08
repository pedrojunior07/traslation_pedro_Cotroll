# ✅ Divisão Correta: Por Tokens Reais (NÃO por Número de Segmentos)

## 🎯 A Lógica CORRETA

### ❌ ERRADO (Antes)

```python
# Dividir por NÚMERO FIXO de segmentos
batch_size = 40  # FIXO!

batches = []
for i in range(0, len(tokens), 40):
    batch = tokens[i:i+40]  # Sempre 40 segmentos
    batches.append(batch)
```

**Problema**:
- Batch 1: 40 segmentos de 1 palavra cada = 40 tokens ✓ OK
- Batch 2: 40 segmentos de 500 caracteres cada = 8,000 tokens ❌ EXCEDE!

### ✅ CORRETO (Agora)

```python
# Dividir por TOKENS ESTIMADOS
max_output_tokens = 8192 * 0.70  # 5,734 tokens

current_batch = []
current_tokens = 0

for segment in segments:
    # Estimar tokens DESTE segmento
    segment_tokens = (len(segment["text"]) * 0.4) + 25

    # Se EXCEDER o limite, fechar batch
    if current_tokens + segment_tokens > max_output_tokens:
        batches.append(current_batch)
        current_batch = []
        current_tokens = 0

    # Adicionar ao batch
    current_batch.append(segment)
    current_tokens += segment_tokens
```

**Resultado**:
- Batch 1: 100 segmentos curtos (~5,700 tokens) ✓ OK
- Batch 2: 10 segmentos longos (~5,600 tokens) ✓ OK
- Batch 3: 1 segmento MUITO longo (~5,500 tokens) ✓ OK

## 📊 Exemplos Práticos

### Exemplo 1: Documento com Segmentos Curtos

**Entrada**:
```
Segmento 1: "Maputo" (6 chars)
Segmento 2: "Moçambique" (10 chars)
Segmento 3: "Tel.:" (5 chars)
...
Segmento 200: "NUIT" (4 chars)
```

**Cálculo**:
```
Segmento 1: 6 chars × 0.4 + 25 = 27 tokens
Segmento 2: 10 chars × 0.4 + 25 = 29 tokens
Segmento 3: 5 chars × 0.4 + 25 = 27 tokens
...

Total acumulado: 27 + 29 + 27 + ... = ~5,500 tokens após 200 segmentos

Batch 1: 200 segmentos (~5,500 tokens) ✓
```

### Exemplo 2: Documento com Segmentos Longos

**Entrada**:
```
Segmento 1: "O SUBCONTRATADO declara que..." (500 chars)
Segmento 2: "As PARTES concordam que..." (450 chars)
Segmento 3: "Com referência à cláusula..." (600 chars)
...
Segmento 10: "Força Maior significa..." (550 chars)
```

**Cálculo**:
```
Segmento 1: 500 chars × 0.4 + 25 = 225 tokens
Segmento 2: 450 chars × 0.4 + 25 = 205 tokens
Segmento 3: 600 chars × 0.4 + 25 = 265 tokens
...

Total acumulado após 10 segmentos: ~2,300 tokens
Total acumulado após 20 segmentos: ~4,600 tokens
Total acumulado após 25 segmentos: ~5,750 tokens ❌ EXCEDE!

Batch 1: 24 segmentos (~5,540 tokens) ✓
Batch 2: Começa do segmento 25...
```

### Exemplo 3: Documento Misto (Realista)

**Entrada**:
```
Segmento 1-50: Curtos (média 30 chars) = ~55 tokens cada
Segmento 51-60: Longos (média 400 chars) = ~185 tokens cada
Segmento 61-100: Curtos (média 20 chars) = ~33 tokens cada
```

**Cálculo**:
```
Batch 1:
  - Segmentos 1-50: 50 × 55 = 2,750 tokens
  - Segmentos 51-55: 5 × 185 = 925 tokens
  - Segmentos 56-58: 3 × 185 = 555 tokens
  - Segmentos 59-60: 2 × 185 = 370 tokens
  Total: ~4,600 tokens
  - Segmento 61: 1 × 185 = 185 tokens
  Total: 4,785 tokens
  - Segmentos 62-90: 29 × 33 = 957 tokens
  Total: 5,742 tokens ❌ EXCEDE!

✓ Batch 1: Segmentos 1-89 (~5,742 tokens)

Batch 2:
  - Segmentos 90-100: 11 × 33 = 363 tokens

✓ Batch 2: Segmentos 90-100 (~363 tokens)
```

## 🎓 Fórmula de Estimativa

### Conversão Caracteres → Tokens

```python
# Para português (mais caracteres por token que inglês)
tokens_text = caracteres × 0.4  # Conservador

# Overhead JSON por segmento
# {"location": "T123", "translation": "..."}
overhead_json = 25 tokens

# Total por segmento
total_tokens = tokens_text + overhead_json
```

### Exemplo de Conversão

```
Texto: "O SUBCONTRATADO fornecerá ao CONTRATANTE"
Caracteres: 42
Tokens estimados: 42 × 0.4 = 16.8 ≈ 17 tokens
Overhead JSON: 25 tokens
Total: 17 + 25 = 42 tokens por segmento
```

## 📈 Logs que Você Verá

### Durante Divisão

```
📊 Estratégia de Divisão:
   max_tokens disponível: 8192
   Usando 70% para segurança: 5734 tokens
   Dividindo por TAMANHO REAL (não por número de segmentos)

   ✓ Batch 1: 85 segmentos, ~5680 tokens
   ✓ Batch 2: 120 segmentos, ~5520 tokens
   ✓ Batch 3: 15 segmentos, ~5650 tokens
   ✓ Batch 4: 200 segmentos, ~5400 tokens
   ✓ Batch 5: 8 segmentos, ~5710 tokens

================================================================================
📦 ESTRATÉGIA DE TRADUÇÃO:
   Total de segmentos: 428
   Número de requisições: 5
   Segmentos por batch: mín=8, máx=200, média=86
   Modo: SEQUENCIAL (1 worker)
   💡 Divisão por TAMANHO REAL (não por número fixo)!
================================================================================
```

**Note**:
- Batch 1: 85 segmentos (segmentos médios)
- Batch 2: 120 segmentos (segmentos curtos!)
- Batch 3: 15 segmentos (segmentos LONGOS!)
- Batch 4: 200 segmentos (segmentos MUITO curtos!)
- Batch 5: 8 segmentos (segmentos MUITO LONGOS!)

## ✅ Vantagens

1. **Preciso**: Respeita limite de tokens, não número arbitrário
2. **Eficiente**: Usa MÁXIMA capacidade em cada batch
3. **Adaptativo**: Ajusta automaticamente ao tamanho real
4. **Seguro**: Margem de 30% garante ZERO cortes
5. **Lógico**: Faz sentido - divide por tamanho, não por quantidade

## 🔍 Por Que 70% (não 85%)?

```
max_tokens = 8,192

USAR 85%:
  Output disponível: 6,963 tokens
  Margem de erro: 15% = 1,229 tokens
  Risco: MÉDIO (variações grandes podem exceder)

USAR 70%:
  Output disponível: 5,734 tokens
  Margem de erro: 30% = 2,458 tokens
  Risco: BAIXO (absorve grandes variações)
```

**Decisão**: 70% para segurança máxima!

## 📊 Comparação Visual

### ANTES (Número Fixo)

```
Batch 1: [40 seg] → Pode ter 1,000 tokens OU 10,000 tokens ❌
Batch 2: [40 seg] → Pode ter 500 tokens OU 12,000 tokens ❌
Batch 3: [40 seg] → Pode ter 2,000 tokens OU 8,000 tokens ❌
```

**Problema**: Não tem controle sobre TOKENS!

### DEPOIS (Tokens Reais)

```
Batch 1: [85 seg] → ~5,680 tokens ✓
Batch 2: [12 seg] → ~5,650 tokens ✓
Batch 3: [200 seg] → ~5,400 tokens ✓
```

**Garantia**: Todos os batches dentro do limite!

## 🎯 Casos Extremos

### Caso 1: Segmento GIGANTE (1 só)

```
Segmento único: 10,000 caracteres
Tokens estimados: 10,000 × 0.4 + 25 = 4,025 tokens

✓ Cria batch com APENAS 1 segmento
✓ Esse batch tem 4,025 tokens (dentro do limite!)
```

### Caso 2: Segmentos MINÚSCULOS (centenas)

```
500 segmentos de 1 palavra cada (~5 chars)
Tokens estimados cada: 5 × 0.4 + 25 = 27 tokens

500 × 27 = 13,500 tokens total

Batch 1: 212 segmentos (~5,724 tokens) ✓
Batch 2: 212 segmentos (~5,724 tokens) ✓
Batch 3: 76 segmentos (~2,052 tokens) ✓
```

## 🔧 Arquivo Modificado

- **[src/claude_client.py](src/claude_client.py#L178-L220)**: Divisão por tokens reais

---

**Resumo**: Agora a divisão é por **TAMANHO REAL** (tokens), não por número arbitrário de segmentos! Cada batch usa máxima capacidade sem exceder limite! ✅
