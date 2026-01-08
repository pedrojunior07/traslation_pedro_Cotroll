# 🏢 Extração Automática do Nome da Empresa

## ✅ Como Funciona

O sistema **extrai automaticamente** o nome da empresa do nome do arquivo e protege esse nome durante a tradução!

### Fluxo Automático:

```
1. Você seleciona o arquivo: "Contrato_ACME_Corporation_2024.docx"
   ↓
2. Sistema extrai: "ACME Corporation"
   ↓
3. Claude recebe instrução: NUNCA traduzir "ACME Corporation"
   ↓
4. Tradução protege o nome automaticamente!
```

## 📋 Exemplos de Nomes de Arquivos

### ✅ Formato Recomendado

Use **underscore (_)** para separar as partes:

| Nome do Arquivo | Nome Extraído |
|----------------|---------------|
| `Contrato_ACME_Corporation_2024.docx` | `ACME Corporation` |
| `PO_Sasol_Mozambique_Limitada.docx` | `Sasol Mozambique Limitada` |
| `Invoice_ABC_Company_Ltd_12345.docx` | `ABC Company Ltd` |
| `WO_Vale_Mocambique_SA_2024.docx` | `Vale Mocambique SA` |

### 📐 Regras de Extração

O sistema usa esta lógica:

```
Nome do arquivo: "Tipo_EMPRESA_NOME_Info.docx"
                    ↓     ↓      ↓     ↓
Partes:          [Tipo, EMPRESA, NOME, Info]
                         └─────┬─────┘
                    Nome Extraído: "EMPRESA NOME"
```

**Detalhes:**
1. Remove a **primeira parte** (tipo de documento: Contrato, PO, Invoice, etc.)
2. Remove a **última parte** se for número ou data (2024, 12345, etc.)
3. Une as partes do **meio** com espaços
4. Resultado: Nome da empresa!

### ❌ Formatos Que NÃO Funcionam Bem

| Nome do Arquivo | Problema |
|----------------|----------|
| `Contrato ACME Corporation 2024.docx` | Usa espaços em vez de underscore |
| `ContratoACME.docx` | Tudo junto, sem separadores |
| `ACME_2024.docx` | Muito curto, não há partes suficientes |

**Solução**: Use underscore (_) para separar as partes!

## 🔄 Prioridade de Proteção

O sistema usa esta ordem de prioridade:

1. **Nome extraído do arquivo** (PRIORIDADE MÁXIMA)
2. Se não encontrar → **Nome configurado nas Preferências**
3. Se nenhum dos dois → Nenhuma proteção especial

### Exemplo:

```
Arquivo: "PO_Sasol_Mozambique_2024.docx"
Preferências: Nome configurado = "ACME Corporation"

Resultado: Protege "Sasol Mozambique" ← Do arquivo, NÃO das preferências!
```

## 🎯 Casos de Uso

### Caso 1: Múltiplos Contratos, Múltiplas Empresas

```
📁 Contratos/
  ├─ Contrato_ACME_Corp_2024.docx      → Protege "ACME Corp"
  ├─ Contrato_Sasol_Moz_2024.docx      → Protege "Sasol Moz"
  └─ Contrato_Vale_SA_2024.docx        → Protege "Vale SA"
```

**Vantagem**: Cada arquivo protege SEU próprio nome automaticamente!

### Caso 2: Nome da Empresa Sempre Igual

```
Preferências: Configure "ACME Corporation"

Arquivos:
  ├─ Invoice_12345.docx    → Protege "ACME Corporation" (das preferências)
  ├─ PO_67890.docx         → Protege "ACME Corporation" (das preferências)
  └─ Contract_2024.docx    → Protege "ACME Corporation" (das preferências)
```

**Vantagem**: Configure uma vez, funciona para todos os arquivos!

### Caso 3: Combinado (Melhor dos Dois Mundos)

```
Preferências: Configure "ACME Corporation" (nome padrão)

Arquivos:
  ├─ Invoice_ACME_Corp_12345.docx          → Protege "ACME Corp" (do arquivo)
  ├─ PO_Sasol_Mozambique_67890.docx        → Protege "Sasol Mozambique" (do arquivo)
  └─ Contract_Generic_2024.docx            → Protege "ACME Corporation" (das preferências)
```

**Vantagem**: Flexibilidade máxima!

## 💡 Dicas de Nomenclatura

### ✅ Recomendado

```
TipoDoc_NomeDaEmpresa_Informação.docx

Exemplos:
- PO_Sasol_Mozambique_Limitada_31628809.docx
- Contrato_ACME_Corporation_2024_Q1.docx
- Invoice_Vale_Mocambique_SA_Jan2024.docx
- WO_ABC_Company_Ltd_12345.docx
```

### ⚙️ Estrutura Recomendada

```
[Tipo]_[Empresa]_[Empresa_Parte2]_[Info].docx
  ↓         ↓            ↓           ↓
Remove  Extrai       Extrai      Remove se número
```

## 🚀 Como o Claude Recebe

Quando você traduz um arquivo `Contrato_ACME_Corporation_2024.docx`, o Claude recebe:

```
🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
⛔ COMPANY NAME - NEVER TRANSLATE THIS NAME ⛔
🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
PROTECTED COMPANY NAME: ACME Corporation

ABSOLUTE RULE - HIGHEST PRIORITY:
1. When you find 'ACME Corporation' in ANY text, keep it EXACTLY as is
2. NEVER translate, adapt, change, or modify 'ACME Corporation'
3. 'ACME Corporation' MUST appear IDENTICAL in the translated text
4. This applies to ALL occurrences of 'ACME Corporation'
5. Even if translating from English to Portuguese, 'ACME Corporation' stays unchanged
6. This rule OVERRIDES all other translation rules

EXAMPLE:
  Original: "Welcome to ACME Corporation"
  Translation: "Bem-vindo à ACME Corporation" ← EXACT COPY
🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
```

## ⚠️ Importante

1. **Funciona em TODOS os fluxos**:
   - ✅ Tradução de arquivo único
   - ✅ Tradução em batch (múltiplos arquivos)
   - ✅ Tradução com threading (pastas)

2. **Funciona com nomes divididos**:
   - Token 1: "ACME" → NÃO traduz
   - Token 2: "Corporation" → NÃO traduz
   - Token 3: "ACME Corporation Services" → NÃO traduz "ACME Corporation"

3. **Sem configuração necessária**:
   - Basta nomear o arquivo corretamente
   - Sistema extrai automaticamente
   - Claude protege automaticamente

## 📊 Testes Recomendados

1. **Teste Simples**:
   - Arquivo: `Test_MyCompany_Ltd_2024.docx`
   - Conteúdo: "Welcome to MyCompany Ltd"
   - Resultado esperado: "Bem-vindo à MyCompany Ltd" ✓

2. **Teste Com Nome Dividido**:
   - Arquivo: `PO_ABC_Corporation_12345.docx`
   - Conteúdo com tokens separados: "ABC" e "Corporation"
   - Resultado esperado: Ambos não traduzidos ✓

3. **Teste Fallback**:
   - Arquivo: `Generic_2024.docx` (não extrai nome)
   - Preferências: "ACME Corp" configurado
   - Resultado esperado: Protege "ACME Corp" das preferências ✓

---

**Implementação**: [src/ui.py](src/ui.py#L902-L933) - Método `_extract_company_name_from_filename`

**Uso Automático**: Todos os 3 endpoints de tradução aplicam automaticamente!
