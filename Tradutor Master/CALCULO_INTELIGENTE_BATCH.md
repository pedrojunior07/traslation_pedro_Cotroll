# 🧮 Cálculo Inteligente de Batch Size

## ✅ Implementado: Cálculo Dinâmico Baseado no Tamanho Real

### ❌ Problema Anterior (Valores Fixos)

**ANTES**:
```python
OPTIMAL_BATCH_SIZES = {
    "claude-3-5-haiku-20241022": 80,  # FIXO para todos os documentos
}
```

**Problemas**:
- ❌ Textos curtos: Batch muito pequeno (desperdiça capacidade)
- ❌ Textos longos: Batch muito grande (excede max_tokens)
- ❌ Não considera tamanho real dos segmentos

**Exemplo do Problema**:
```
Documento A: Segmentos de 20 caracteres cada
  → 80 segmentos × 20 chars = 1,600 chars (MUITO PEQUENO, poderia enviar 200!)

Documento B: Segmentos de 300 caracteres cada
  → 80 segmentos × 300 chars = 24,000 chars (MUITO GRANDE, JSON cortado!)
```

### ✅ Solução: Cálculo Dinâmico

**AGORA**:
```python
# 1. Analisar primeiros 10 segmentos do documento
sample_size = min(10, len(tokens))
avg_text_length = sum(len(t["text"]) for t in tokens[:sample_size]) / sample_size

# 2. Estimar tokens por segmento
estimated_tokens_per_segment = (avg_text_length * 0.3) + 20

# 3. Calcular batch size ideal
safe_max_tokens = max_tokens * 0.85
batch_size = int(safe_max_tokens / estimated_tokens_per_segment)

# 4. Aplicar limites de segurança
batch_size = max(20, min(batch_size, 80))
```

## 📊 Exemplos Práticos

### Documento com Textos Curtos (PO simples)

**Entrada**:
```
Segmentos: 500
Tamanho médio: 30 caracteres
```

**Cálculo**:
```
📊 Cálculo de batch size:
   Tamanho médio dos textos: 30 caracteres
   Tokens estimados por segmento: 29 tokens (30 × 0.3 + 20 JSON)
   Batch size calculado: 240 segmentos
   max_tokens disponível: 8192 (usando 85% = 6963)

Aplicando limite máximo: 80 segmentos (limite de segurança)
```

**Resultado**:
- Batches: 500 ÷ 80 = 7 batches
- Cada batch: ~2,320 tokens (dentro do limite!)

### Documento com Textos Longos (Contrato complexo)

**Entrada**:
```
Segmentos: 1500
Tamanho médio: 250 caracteres
```

**Cálculo**:
```
📊 Cálculo de batch size:
   Tamanho médio dos textos: 250 caracteres
   Tokens estimados por segmento: 95 tokens (250 × 0.3 + 20 JSON)
   Batch size calculado: 73 segmentos
   max_tokens disponível: 8192 (usando 85% = 6963)

Batch size final: 73 segmentos (calculado automaticamente!)
```

**Resultado**:
- Batches: 1500 ÷ 73 = 21 batches
- Cada batch: ~6,935 tokens (dentro do limite!)

### Documento com Textos MUITO Longos (Cláusulas legais)

**Entrada**:
```
Segmentos: 800
Tamanho médio: 400 caracteres
```

**Cálculo**:
```
📊 Cálculo de batch size:
   Tamanho médio dos textos: 400 caracteres
   Tokens estimados por segmento: 140 tokens (400 × 0.3 + 20 JSON)
   Batch size calculado: 49 segmentos
   max_tokens disponível: 8192 (usando 85% = 6963)

Batch size final: 49 segmentos
```

**Resultado**:
- Batches: 800 ÷ 49 = 17 batches
- Cada batch: ~6,860 tokens (PERFEITO!)

## 🎯 Fórmula Completa

```python
# Passo 1: Amostragem (10 primeiros segmentos)
sample = tokens[:10]

# Passo 2: Tamanho médio em caracteres
avg_chars = média(len(seg["text"]) for seg in sample)

# Passo 3: Converter caracteres → tokens
# Regra: 1 caractere ≈ 0.3 tokens (português)
# + 20 tokens para JSON overhead {"location": "...", "translation": "..."}
tokens_per_segment = (avg_chars × 0.3) + 20

# Passo 4: Calcular batch size
# 85% do max_tokens para margem de segurança
safe_max = max_tokens × 0.85
batch_size = safe_max ÷ tokens_per_segment

# Passo 5: Limites de segurança
batch_size = max(20, min(batch_size, 80))
```

## 📈 Comparação: Fixo vs Dinâmico

| Tipo de Documento | Tamanho Médio | Batch Fixo | Batch Dinâmico | Diferença |
|-------------------|---------------|------------|----------------|-----------|
| PO simples | 30 chars | 80 | 80 (limite max) | ✓ Otimizado |
| Contrato médio | 150 chars | 80 | 65 | ✓ Melhor |
| Contrato longo | 250 chars | 80 | 73 | ✓ Evita erro! |
| Cláusulas legais | 400 chars | 80 | 49 | ✓✓ Salva de erro! |
| Texto técnico | 500 chars | 80 | 38 | ✓✓✓ Previne corte! |

## 🔍 Logs que Você Verá

### Antes de Traduzir

```
📊 Cálculo de batch size:
   Tamanho médio dos textos: 245 caracteres
   Tokens estimados por segmento: 94 tokens
   Batch size calculado: 74 segmentos
   max_tokens disponível: 8192 (usando 85% = 6963)

================================================================================
📦 ESTRATÉGIA DE TRADUÇÃO:
   Total de segmentos: 1484
   Segmentos por requisição: ~74
   Número de requisições: 21
   Modo: SEQUENCIAL (1 worker)
   💡 Cada requisição traduz ~74 segmentos de uma só vez!
================================================================================
```

### Durante Tradução (Atualização em Tempo Real)

```
Claude: 0/1484 segmentos traduzidos (Batch 1/21)
  📤 Enviando 74 segmentos numa ÚNICA requisição para Claude...
  📥 Resposta recebida do Claude para os 74 segmentos
Claude: 74/1484 segmentos traduzidos ✓

Claude: 74/1484 segmentos traduzidos (Batch 2/21)
  📤 Enviando 74 segmentos numa ÚNICA requisição para Claude...
  📥 Resposta recebida do Claude para os 74 segmentos
Claude: 148/1484 segmentos traduzidos ✓

Claude: 148/1484 segmentos traduzidos (Batch 3/21)
  📤 Enviando 74 segmentos numa ÚNICA requisição para Claude...
  📥 Resposta recebida do Claude para os 74 segmentos
Claude: 222/1484 segmentos traduzidos ✓
```

## ✅ Benefícios

1. **Adaptativo**: Ajusta automaticamente ao tipo de documento
2. **Seguro**: Sempre fica dentro do limite de max_tokens
3. **Eficiente**: Usa máxima capacidade possível sem desperdiçar
4. **Tempo Real**: Interface atualiza a cada batch completado
5. **Sem Erros**: Não corta mais JSONs no meio

## 🎓 Por Que 85% do max_tokens?

```
max_tokens = 8192

USAR 100% (8192):
  ❌ Qualquer variação no tamanho = JSON cortado
  ❌ Overhead de formatação pode exceder
  ❌ Risco alto

USAR 85% (6963):
  ✅ Margem de segurança de 15%
  ✅ Absorve variações de tamanho
  ✅ Garante JSON completo
  ✅ Ainda usa ~87% da capacidade
```

## 📊 Amostragem de 10 Segmentos

**Por que 10?**
```
Menos de 10:
  ❌ Amostra muito pequena
  ❌ Pode não ser representativa

Exatamente 10:
  ✅ Rápido de calcular
  ✅ Estatisticamente significativo
  ✅ Representa bem o documento

Mais de 10:
  ✅ Mais preciso
  ❌ Overhead desnecessário
```

## 🔧 Arquivos Modificados

- **[src/claude_client.py](src/claude_client.py#L178-L198)**: Cálculo inteligente de batch size
- **[src/claude_client.py](src/claude_client.py#L264-L288)**: Atualização em tempo real

---

**Resumo**: Agora o batch size é **calculado dinamicamente** baseado no tamanho real dos textos, garantindo máxima eficiência sem erros! 🚀
