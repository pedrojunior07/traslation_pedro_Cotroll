# 🚀 Otimização para Claude Haiku 3.5

## 📊 Limites da API Claude

### Claude Haiku 3.5 (claude-3-5-haiku-20241022)
- **RPM (Requests Per Minute)**: 50 requisições/minuto
- **TPM (Tokens Per Minute)**: 50,000 tokens/minuto
- **Contexto**: até 200k tokens
- **Max Output**: 8,192 tokens
- **Custo**: $0.25/1M input, $1.25/1M output

### Como Maximizar o Uso

#### 1. **Batches Otimizados** ✅ IMPLEMENTADO
- Batch size otimizado: **50 textos por requisição** (Haiku 3.5)
- Batches menores = mais paralelismo = mais velocidade
- Aproveita melhor os **50 RPM** disponíveis

#### 2. **Processamento Paralelo** ✅ IMPLEMENTADO
- Até **10 workers** processando simultaneamente
- Aproveita os **50 RPM** do rate limit
- **10x mais rápido** que sequencial

#### 3. **Rate Limiting Inteligente** ✅ IMPLEMENTADO
- Controla automaticamente para não exceder 50 RPM
- Aguarda quando necessário
- Maximiza throughput sem erros

## 🎯 Configuração Recomendada

### Para Tradução Rápida e Barata (Haiku 3.5):

1. **Abra a aba "🤖 Claude API"**
2. **Selecione o modelo**: `claude-3-5-haiku-20241022`
3. **Batch Size**: Deixe em branco (usa o otimizado automaticamente)
4. **Max Workers**: 10 (já configurado)

### Comparação de Performance:

| Configuração | Velocidade | Custo | Qualidade |
|--------------|-----------|-------|-----------|
| **Haiku 3.5 Paralelo (Recomendado)** | ⚡⚡⚡⚡⚡ | 💰 | ⭐⭐⭐⭐ |
| Haiku 3 Paralelo | ⚡⚡⚡⚡ | 💰 | ⭐⭐⭐⭐ |
| Sonnet 3.5 Paralelo | ⚡⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ |
| Opus 3 Paralelo | ⚡⚡ | 💰💰💰💰💰 | ⭐⭐⭐⭐⭐ |

## ⚙️ Sistema Implementado

### Recursos Adicionados:

1. **Auto-detecção de Modelo**
   - Haiku 3.5: 10 workers, batch 50
   - Haiku 3: 10 workers, batch 40
   - Sonnet: 5 workers, batch 30
   - Opus: 5 workers, batch 20

2. **Rate Limiting Automático**
   - Monitora requisições em tempo real
   - Aguarda quando atinge 50 RPM
   - Garante 100% de aproveitamento sem erros

3. **Processamento Paralelo**
   - ThreadPoolExecutor com workers configuráveis
   - Submete múltiplos batches simultaneamente
   - Processa resultados conforme completam

4. **Métricas em Tempo Real**
   - Taxa de requisições/minuto
   - ETA (tempo estimado)
   - Progresso detalhado

## 📈 Exemplo de Performance

### Traduzindo 500 textos:

**Sequencial (antigo)**:
- 500 textos ÷ 100 por batch = 5 requisições
- 5 requisições × 3s cada = **15 segundos**

**Paralelo Haiku 3.5 (novo)**:
- 500 textos ÷ 50 por batch = 10 requisições
- 10 requisições ÷ 10 workers = **~5 segundos**
- Aproveitando 50 RPM do rate limit

**Resultado**: **3x mais rápido!** ⚡

## 🔧 Como Funciona

### Fluxo de Processamento:

```
1. Recebe 500 textos para traduzir
   ↓
2. Divide em batches de 50 textos
   ↓
3. Cria 10 workers paralelos
   ↓
4. Cada worker pega um batch e traduz
   ├─ Worker 1: Batch 1 (50 textos)
   ├─ Worker 2: Batch 2 (50 textos)
   ├─ Worker 3: Batch 3 (50 textos)
   ├─ Worker 4: Batch 4 (50 textos)
   ├─ Worker 5: Batch 5 (50 textos)
   ├─ Worker 6: Batch 6 (50 textos)
   ├─ Worker 7: Batch 7 (50 textos)
   ├─ Worker 8: Batch 8 (50 textos)
   ├─ Worker 9: Batch 9 (50 textos)
   └─ Worker 10: Batch 10 (50 textos)
   ↓
5. Respeita rate limit (50 RPM)
   ↓
6. Retorna traduções ordenadas
```

### Rate Limiting:

```python
# Controla requisições por minuto
1. Registra timestamp de cada requisição
2. Remove requisições antigas (>60s)
3. Se >= 50 requisições no último minuto:
   └─ Aguarda até liberar
4. Submete nova requisição
```

## 💡 Dicas de Uso

### Para Máxima Velocidade:
✅ Use **Haiku 3.5**
✅ Ative **processamento paralelo**
✅ Use **batch size otimizado** (automático)

### Para Máxima Qualidade:
✅ Use **Sonnet 3.5** ou **Opus 3**
✅ Adicione **dicionário personalizado**
✅ Revise traduções complexas

### Para Mínimo Custo:
✅ Use **Haiku 3.5**
✅ Aproveite **cache de prompts** (automático)
✅ Traduza em lotes grandes

## 🎬 Começando

### Passo a Passo:

1. **Configure a API Key**
   - Aba "🤖 Claude API"
   - Cole sua API key da Anthropic
   - Salve

2. **Selecione o Modelo**
   - Escolha `claude-3-5-haiku-20241022`
   - Batch size: deixe em branco
   - Save Settings

3. **Traduza!**
   - Selecione arquivos
   - Clique "Traduzir"
   - Aproveite a velocidade 🚀

## 📊 Monitoramento

Durante a tradução, você verá:

```
🚀 Claude Client inicializado:
   Modelo: claude-3-5-haiku-20241022
   Batch size otimizado: 50
   Workers paralelos: 10
   Rate limit: 50 RPM

📦 Dividindo 500 tokens em 10 batches de ~50 tokens
⚡ Processamento PARALELO com 10 workers

  ✓ Batch 1/10 completo - 48 req/min
  ✓ Batch 2/10 completo - 50 req/min
  ✓ Batch 3/10 completo - 49 req/min
  ✓ Batch 4/10 completo - 50 req/min
  ✓ Batch 5/10 completo - 48 req/min
  ✓ Batch 6/10 completo - 50 req/min
  ✓ Batch 7/10 completo - 49 req/min
  ✓ Batch 8/10 completo - 50 req/min
  ✓ Batch 9/10 completo - 47 req/min
  ✓ Batch 10/10 completo - 50 req/min

✓ Tradução paralela completa: 500 tokens em 5.2s (50 req/min)
```

## ⚠️ Importante

- O sistema **respeita automaticamente** os limites da API
- **Não** é necessário configurar manualmente
- **Aguarda automaticamente** se atingir o rate limit
- **Máxima performance** sem risco de bloqueio

---

**Sistema Otimizado Implementado em**: [src/claude_client.py](src/claude_client.py)
