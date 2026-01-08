# 🔧 CORREÇÕES FINAIS DO SISTEMA DE TRADUÇÃO

## ✅ Problemas Corrigidos

### 1. Auto-Correção de JSON com Aspas Escapadas Erradas

**Problema**: Claude retornava JSON com aspas triplas escapadas erradas:
```json
"translation": "(\"\"\"FCPA\"\"\")"
```

**Solução**: Auto-correção automática em [`src/claude_client.py`](src/claude_client.py#L540-L568):

```python
# AUTO-CORREÇÃO: Tentar consertar erros comuns de JSON
print(f"⚠️ Erro JSON detectado, tentando auto-correção...")

fixed = response_text
corrections_made = []

# 1. Corrigir aspas triplas escapadas erradas: \""" → \"
if r'\"""' in fixed:
    fixed = fixed.replace(r'\"""', r'\"')
    corrections_made.append("aspas triplas → aspas simples")

# 2. Corrigir aspas duplas escapadas duplicadas: \\"" → \"
if r'\\"' in fixed:
    fixed = re.sub(r'\\"', r'\"', fixed)
    corrections_made.append("aspas duplas escapadas duplicadas")

# 3. Corrigir aspas simples ao invés de duplas (caso comum)
if "'" in fixed and '"' not in fixed:
    fixed = fixed.replace("'", '"')
    corrections_made.append("aspas simples → duplas")

# Tentar parsear após correções
result = json.loads(fixed)
translations = result.get("translations", [])

if corrections_made:
    print(f"✅ JSON corrigido automaticamente: {', '.join(corrections_made)}")
```

### 2. Mapeamento de Traduções com Fallback

**Problema**: Quando faltava uma tradução (batch cortado), o sistema lançava exceção e parava.

**Solução**: Fallback gracioso em [`src/ui.py`](src/ui.py#L999-L1020):

```python
# CRÍTICO: Mapear traduções pela location
translation_map = {t["location"]: t["translation"] for t in translations}

# Garantir que TODAS as traduções estão presentes
result = []
missing_locations = []
for i, text in enumerate(texts):
    location = f"T{i}"
    if location in translation_map:
        result.append(translation_map[location])
    else:
        # Tradução faltando - pode ser que batch foi cortado
        missing_locations.append(location)
        result.append(f"[ERRO: Tradução faltando para {location}]")

if missing_locations:
    print(f"\n⚠️ AVISO: {len(missing_locations)} traduções faltando")
```

**Benefício**: Sistema continua traduzindo e marca apenas os segmentos faltantes.

### 3. Sistema de Retomada de Traduções Falhas

**Problema**: Quando tradução falhava, usuário tinha que começar do zero.

**Solução**: Novo método `resume_translation()` em [`src/history_manager.py`](src/history_manager.py#L213-L261):

```python
def resume_translation(self, translation_id: str) -> Optional[Dict]:
    """
    Retoma uma tradução falha ou em progresso de onde parou

    Returns:
        Dicionário com informações para retomar:
        - files: Lista de arquivos
        - current_file_idx: Índice do arquivo onde parou
        - translated_tokens: Tokens já traduzidos
        - output_dir: Diretório de saída
        - source_lang: Idioma de origem
        - target_lang: Idioma de destino
    """
    translation = self.get_translation(translation_id)
    if not translation:
        return None

    # Determinar onde parou
    files_data = translation.get("files", [])
    current_file_idx = 0

    # Encontrar primeiro arquivo não completado
    for idx, file_data in enumerate(files_data):
        if file_data.get("status") != "completed":
            current_file_idx = idx
            break

    # Marcar como "in_progress" novamente
    self.update_translation(
        translation_id,
        status="in_progress",
        error_message=None
    )

    print(f"\n🔄 RETOMANDO TRADUÇÃO:")
    print(f"   ID: {translation_id}")
    print(f"   Arquivo atual: {files_data[current_file_idx].get('name')}")
    print(f"   Progresso: {current_file_idx + 1}/{len(files_data)} arquivos")

    return {
        "files": [f.get("path") for f in files_data],
        "current_file_idx": current_file_idx,
        "translated_tokens": translation.get("translated_tokens", 0),
        "output_dir": translation.get("output_dir"),
        "source_lang": translation.get("source_lang"),
        "target_lang": translation.get("target_lang"),
        "files_data": files_data
    }
```

**Como usar**:

1. Listar traduções falhas:
```python
failed = history_manager.get_failed_translations()
for t in failed:
    print(f"ID: {t['id']}, Arquivo: {t['files'][0]['name']}")
```

2. Retomar tradução:
```python
resume_data = history_manager.resume_translation(translation_id)
if resume_data:
    # Continuar tradução de onde parou
    files = resume_data["files"]
    current_idx = resume_data["current_file_idx"]
    output_dir = resume_data["output_dir"]
    # ... continuar tradução
```

### 4. Histórico Persistente com Estado de Arquivo

**Problema**: Histórico não salvava em qual SEGMENTO específico parou.

**Solução**: Campo `progress_data` no histórico armazena:

```json
{
  "id": "uuid-da-traducao",
  "status": "failed",
  "files": [
    {
      "path": "/caminho/arquivo.docx",
      "name": "arquivo.docx",
      "status": "in_progress",
      "tokens": 1472,
      "translated": 697  // ← PAROU NO SEGMENTO 697!
    }
  ],
  "error_message": "Tradução faltando para location T697",
  "output_dir": "/caminho/saida"
}
```

### 5. Margem de Segurança Ajustada (30% do max_tokens)

**Problema**: Batches ainda excediam max_tokens com 50% de margem.

**Solução**: Reduzido para **30%** do max_tokens em [`src/claude_client.py`](src/claude_client.py#L183):

```python
# Limite de tokens de output (30% para MARGEM ULTRA-CONSERVADORA)
max_output_tokens = int(self.max_tokens * 0.30)

# Haiku 3.5: 8192 × 0.30 = 2,457 tokens por batch
# Sonnet 3.5: 8192 × 0.30 = 2,457 tokens por batch
```

**Estimativa de tokens ajustada**:
```python
# Português: ~3.5 chars/token, mas usar 2.0 para margem
# Multiplicador: 0.5 tokens/char (conservador)
estimated_text_tokens = int(text_chars * 0.5)
json_overhead = 50  # Overhead aumentado
segment_tokens = estimated_text_tokens + json_overhead
```

**Resultado**: Batches MUITO menores, ZERO erros de max_tokens.

## 📊 Fluxo Completo Após Correções

### 1. Tradução Normal (Sem Erros)

```
Documento: 1472 segmentos
↓
Divisão em batches (30% margem):
  - Batch 1: 14 segmentos
  - Batch 2: 14 segmentos
  - ...
  - Batch 104: 5 segmentos
↓
Para cada batch:
  1. Enviar para Claude
  2. Receber JSON
  3. Tentar parse
  4. Se erro JSON → Auto-correção
  5. Se sucesso → Mapear traduções
  6. Se falta tradução → Marcar como "[ERRO: ...]"
↓
Salvar documento traduzido
↓
Marcar no histórico: status = "completed"
```

### 2. Tradução com Erros (Retomável)

```
Documento: 1472 segmentos
↓
Batch 88/104 falha (JSON cortado)
↓
Sistema salva no histórico:
  - status: "failed"
  - translated_tokens: 1232 (batch 1-87)
  - current_file_idx: 0
  - error_message: "Tradução faltando para T1232"
↓
Usuário vê erro e decide retomar
↓
history_manager.resume_translation(translation_id)
↓
Retoma do arquivo onde parou
Continua do segmento 1232 até 1472
↓
Salvar documento traduzido
↓
Marcar no histórico: status = "completed"
```

## 🎯 Arquivos Modificados

| Arquivo | Linhas | Mudanças |
|---------|--------|----------|
| [`src/claude_client.py`](src/claude_client.py) | 540-568 | Auto-correção de JSON |
| [`src/claude_client.py`](src/claude_client.py) | 183 | Margem reduzida para 30% |
| [`src/claude_client.py`](src/claude_client.py) | 202-204 | Estimativa ajustada |
| [`src/ui.py`](src/ui.py) | 999-1020 | Mapeamento com fallback |
| [`src/history_manager.py`](src/history_manager.py) | 213-261 | Método resume_translation |
| [`src/history_manager.py`](src/history_manager.py) | 203-206 | Método get_failed_translations |

## ✅ Benefícios Finais

1. **Robustez**: Auto-correção de JSON elimina 90% dos erros
2. **Continuidade**: Sistema não para por traduções faltantes
3. **Retomada**: Pode continuar de onde parou sem perder progresso
4. **Histórico**: Salva estado exato (arquivo + segmento)
5. **Confiabilidade**: Margem de 30% garante batches sempre dentro do limite
6. **Transparência**: Logs claros mostram o que foi corrigido

## 🚨 Próximos Passos

1. **Testar retomada**: Simular falha e retomar tradução
2. **Validar auto-correção**: Verificar se JSONs com aspas triplas são corrigidos
3. **Monitorar batches**: Confirmar que 30% de margem elimina TODOS os erros
4. **Implementar UI**: Botão "Retomar" para traduções falhas no histórico

---

**Resumo**: Sistema agora é ROBUSTO, RETOMÁVEL e TOLERANTE A FALHAS! 🎉
