# 🗂️ Salvamento de Erros JSON do Claude

## 📍 Localização dos Erros

Quando o Claude retorna JSON inválido, o sistema agora salva automaticamente no projeto:

```
📁 Tradutor Master/
  ├─ claude_json_errors/          ← PASTA DE ERROS
  │   ├─ claude_error_20260104_143022.json
  │   ├─ claude_error_20260104_143145.json
  │   └─ claude_error_20260104_143301.json
  │
  ├─ src/
  ├─ iniciar.bat
  └─ ...
```

## 🎯 Por Que No Projeto?

**ANTES**: Arquivos salvos em `C:\Users\...\AppData\Local\Temp\`
- Difícil de encontrar
- Pode ser limpo automaticamente pelo Windows
- Nome genérico

**AGORA**: Arquivos salvos em `claude_json_errors/` no projeto
- ✅ Fácil de encontrar
- ✅ Permanente para análise
- ✅ Nome com timestamp claro
- ✅ Não vai para o Git (está no .gitignore)

## 📋 Formato do Nome

```
claude_error_YYYYMMDD_HHMMSS.json
              │        │
              │        └─ Hora: 14:30:22
              └─ Data: 2026-01-04
```

**Exemplo**: `claude_error_20260104_143022.json`
- Data: 04 de Janeiro de 2026
- Hora: 14:30:22

## 🔍 Quando É Salvo?

O arquivo é salvo automaticamente quando:

1. Claude retorna resposta
2. Sistema tenta fazer parse do JSON
3. `json.loads()` falha (JSON inválido)
4. Sistema tenta corrigir (aspas simples → duplas)
5. Correção também falha
6. **Sistema salva JSON bruto no projeto** ← AQUI

## 📊 Informação No Console

Quando erro ocorre, você verá:

```
================================================================================
🚨 ERRO JSON SALVO PARA ANÁLISE:
   Arquivo: C:\...\claude_json_errors\claude_error_20260104_143022.json
   Tamanho: 12543 caracteres
   Erro: Unterminated string starting at: line 130 column 41 (char 11771)
================================================================================
```

## 🛠️ Como Usar Para Criar Algoritmo

### 1. Coletar Vários Exemplos

Execute traduções e colete vários JSONs problemáticos:
```
claude_json_errors/
  ├─ claude_error_20260104_140000.json  ← Erro 1
  ├─ claude_error_20260104_141500.json  ← Erro 2
  ├─ claude_error_20260104_143000.json  ← Erro 3
  └─ claude_error_20260104_144500.json  ← Erro 4
```

### 2. Analisar Padrões

Abra os arquivos e identifique padrões comuns:

**Padrão 1**: String não terminada
```json
{"location": "T1", "translation": "CCS IV S.c.a.r.l. [BRANCH DE MOÇAMBIQUE}
                                                                           ↑
                                                                    Falta fechar "
```

**Padrão 2**: Escape incorreto
```json
{"location": "T2", "translation": "Rua "Principal""}
                                       ↑         ↑
                                  Deveria ser \"  \"
```

**Padrão 3**: Quebra de linha não escapada
```json
{"location": "T3", "translation": "Linha 1
Linha 2"}
                                    ↑
                              Deveria ser \n
```

### 3. Criar Função de Correção

Com base nos padrões, criar função:

```python
def fix_claude_json(json_text: str) -> str:
    """Corrige erros comuns do Claude em JSON"""

    # Padrão 1: Strings não fechadas
    # TODO: Implementar detecção e correção

    # Padrão 2: Aspas não escapadas
    # TODO: Implementar regex para escapar aspas internas

    # Padrão 3: Quebras de linha
    json_text = json_text.replace('\n', '\\n')

    # Padrão 4: Barras invertidas
    # TODO: Implementar escape correto

    return json_text
```

### 4. Integrar No Código

Adicionar no `claude_client.py` antes do `json.loads()`:

```python
try:
    result = json.loads(response_text)
except json.JSONDecodeError:
    # Tentar corrigir com algoritmo
    fixed = fix_claude_json(response_text)
    result = json.loads(fixed)
```

## 📈 Exemplo Real Do Erro Atual

Do screenshot que você mostrou:

**Erro**: `Unterminated string starting at: line 130 column 41 (char 11771)`

**Arquivo Salvo**: `claude_error_20260104_XXXXXX.json`

**Conteúdo** (primeiros 1000 chars mostrados no erro):
```json
{
  "translations":[
    {"location":"T1","translation":"CCS IV S.c.a.r.l. [BRANCH DE MOÇAMBIQUE}"},
    {"location":"T1","translation":"CCS IV S.c.a.r.l. [BRANCH DE MOÇAMBIQUE}"},
    {"location":"T2","translation":"Edifício JAT V"},
    {"location":"T3","translation":"Edifício JAT V"},
    {"location":"T4","translation":"Rua dos Desportistas, n.º 833, 5° andar"},
    ...
```

**Linha 130, coluna 41**: String que não foi fechada corretamente.

**Solução**: Abrir o arquivo completo, ir até linha 130, identificar exatamente onde está o problema.

## 🎯 Fluxo Completo

```
1. Tradução falha com JSON inválido
   ↓
2. Sistema salva em: claude_json_errors/claude_error_XXXXXX.json
   ↓
3. Você abre o arquivo
   ↓
4. Analisa o erro específico (linha X, coluna Y)
   ↓
5. Identifica padrão do erro
   ↓
6. Cria/atualiza algoritmo de correção
   ↓
7. Integra no código
   ↓
8. Próxima vez, erro é corrigido automaticamente!
```

## 📝 Estrutura do JSON Esperado

```json
{
  "translations": [
    {"location": "T1", "translation": "texto traduzido aqui"},
    {"location": "T2", "translation": "outro texto traduzido"},
    {"location": "T3", "translation": "mais texto"}
  ]
}
```

**Regras de Escape**:
- Aspas duplas internas: `\"`
- Quebras de linha: `\n`
- Barras invertidas: `\\`
- Tabs: `\t`

## 🔧 Manutenção da Pasta

A pasta `claude_json_errors/` NÃO é versionada (está no .gitignore).

Para limpar arquivos antigos:
```bash
# Deletar erros de mais de 7 dias
# (Faça isso manualmente quando necessário)
```

Para analisar todos os erros de uma vez:
```python
import os
import json

error_dir = "claude_json_errors"
for filename in os.listdir(error_dir):
    if filename.endswith(".json"):
        filepath = os.path.join(error_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Analisar padrões...
```

## ✅ Vantagens

1. **Permanente**: Arquivos não são deletados automaticamente
2. **Organizado**: Todos em um lugar, fácil de encontrar
3. **Timestamp**: Saber exatamente quando cada erro ocorreu
4. **Completo**: JSON inteiro salvo, não apenas preview
5. **Local**: No projeto, fácil acesso
6. **Análise**: Pode criar scripts para analisar múltiplos erros

---

**Resumo**: Agora você tem acesso total aos JSONs problemáticos para criar um algoritmo de correção eficaz! 🚀
