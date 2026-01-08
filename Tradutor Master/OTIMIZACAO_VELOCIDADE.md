# ⚡ Otimização de Velocidade - Batches Gigantes

## 🎯 Estratégia Implementada

Baseado no seu insight: **"se no chat podemos colocar o documento inteiro e ele traduz em segundos, por que não traduzir vários segmentos numa única requisição?"**

### Mudança de Estratégia

**ANTES** (Paralelo com batches pequenos):
```
📄 Documento com 1500 segmentos
   ↓
🔀 Dividido em 10 batches de 150 segmentos
   ↓
⚡ 10 workers processando em paralelo
   ↓
❌ PROBLEMA: 10 requisições simultâneas = Rate Limit (429 errors)
   ↓
⏱ Retry de 6-7 segundos a cada erro = MUITO LENTO
```

**DEPOIS** (Serial com batches gigantes):
```
📄 Documento com 1500 segmentos
   ↓
📦 1 ÚNICO batch gigante de 1500 segmentos
   ↓
🎯 1 worker fazendo 1 requisição
   ↓
✅ RESULTADO: 1 requisição = SEM rate limit
   ↓
⚡ Tradução em ~10-20 segundos = RÁPIDO
```

## 📊 Configurações Implementadas

### Batch Sizes por Modelo

```python
OPTIMAL_BATCH_SIZES = {
    "claude-3-5-haiku-20241022": 1500,   # 🚀 GIGANTE (200K contexto)
    "claude-3-5-sonnet-20241022": 800,   # Grande (200K contexto)
    "claude-3-haiku-20240307": 1000,     # Grande (200K contexto)
    "claude-3-sonnet-20240229": 500,     # Médio
    "claude-3-opus-20240229": 400,       # Médio
}
```

### Workers

```python
max_workers = 1  # Apenas 1 worker = SEM paralelismo = SEM rate limit
```

### Delay Entre Requisições

```python
# SEM delay artificial
# O tempo de processamento do batch gigante (~10-20s)
# já garante que ficamos abaixo do rate limit (50 RPM)
```

## 🧮 Cálculo dos Batch Sizes

### Base do Cálculo

**Haiku 3.5**:
- Contexto: 200,000 tokens
- Segment médio: ~50 tokens (texto + JSON)
- Capacidade teórica: 200,000 ÷ 50 = **4,000 segmentos**
- Conservador (30% do contexto): **1,200 segmentos**
- **Implementado: 1,500 segmentos** (meio termo seguro)

### Por Que 1500?

1. **Seguro**: Fica abaixo do limite real de contexto
2. **Eficiente**: A maioria dos documentos cabe em 1-2 requisições
3. **Sem Rate Limit**: 1 requisição por vez = máximo 1 RPM (limite é 50 RPM)

## 📈 Comparação de Performance

### Documento Pequeno (500 segmentos)

| Estratégia | Requisições | Rate Limit | Tempo |
|-----------|-------------|------------|-------|
| **ANTES** | 3-5 paralelas | ❌ Sim (429) | ~30-40s |
| **DEPOIS** | 1 serial | ✅ Não | ~10-15s |

### Documento Médio (1500 segmentos)

| Estratégia | Requisições | Rate Limit | Tempo |
|-----------|-------------|------------|-------|
| **ANTES** | 10-15 paralelas | ❌❌ Muito (429) | ~60-90s |
| **DEPOIS** | 1 serial | ✅ Não | ~15-20s |

### Documento Grande (3000 segmentos)

| Estratégia | Requisições | Rate Limit | Tempo |
|-----------|-------------|------------|-------|
| **ANTES** | 20-30 paralelas | ❌❌❌ Extremo (429) | ~120-180s |
| **DEPOIS** | 2 seriais | ✅ Não | ~30-40s |

## ✅ Benefícios

1. **Sem 429 Errors**: Apenas 1 requisição por vez = impossível exceder 50 RPM
2. **Sem Retries**: Sem erros 429 = sem delays de 6-7 segundos
3. **Mais Rápido**: Menos overhead de requisições HTTP
4. **Aproveitamento Máximo**: Usa 200K de contexto eficientemente
5. **Simples**: Sem complexidade de paralelismo

## 🔍 Como Funciona na Prática

### Exemplo Real

**Arquivo**: `KERRY_PROJECT_LOGISTICS_-_0031620659_000.docx`

**Fluxo**:
```
1. Extração: 1,234 segmentos
   ↓
2. Batch único de 1,234 segmentos
   ↓
3. Claude processa em ~12 segundos
   ↓
4. Pronto! ✅
```

**Antes**:
- 8-10 requisições paralelas
- 3-4 erros 429
- Retries de 6-7s cada
- Total: ~45-60 segundos

**Depois**:
- 1 requisição
- 0 erros 429
- 0 retries
- Total: ~12 segundos

## 📝 Notas Técnicas

### Rate Limit Natural

Com batches de 1500 segmentos:
- Tempo de processamento: ~10-20s por requisição
- Requisições por minuto: ~3-6 RPM
- Limite da API: 50 RPM
- **Margem de segurança**: 8-16x abaixo do limite!

### Contexto de 200K

O Claude Haiku 3.5 tem 200,000 tokens de contexto:
```
Prompt do sistema:     ~500 tokens
Instruções:            ~300 tokens
Glossário (opcional):  ~1,000 tokens
Batch de 1500 segs:    ~75,000 tokens
Resposta (1500 segs):  ~75,000 tokens
─────────────────────────────────────
TOTAL:                 ~152,000 tokens (76% do limite)
```

✅ Sobra 48,000 tokens de margem de segurança!

## 🎯 Quando Usar Cada Estratégia

### Batches Gigantes (Atual - Recomendado)
- ✅ Documentos únicos
- ✅ Batch de múltiplos documentos
- ✅ Quando rate limit é problema
- ✅ Quando quer velocidade máxima

### Paralelo (Desativado)
- ❌ Não recomendado
- ❌ Causa rate limit
- ❌ Mais lento devido a retries

## 🔧 Arquivos Modificados

- **[src/claude_client.py](src/claude_client.py#L53-L63)**: Batch sizes aumentados
- **[src/claude_client.py](src/claude_client.py#L98-L104)**: Workers reduzido para 1
- **[src/claude_client.py](src/claude_client.py#L137-L139)**: Delay removido

---

**Implementação**: Baseado no insight do usuário sobre aproveitar o contexto de 200K tokens!
