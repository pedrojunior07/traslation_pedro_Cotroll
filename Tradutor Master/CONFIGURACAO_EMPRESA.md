# 🏢 Proteção do Nome da Empresa

## ✅ Implementado

Sistema para garantir que o nome da sua empresa NUNCA seja traduzido pelo Claude!

## 🎯 Funcionalidades

### 1️⃣ API Key Local (Por Instalação)
- ✅ Cada instalação tem sua própria API key
- ✅ Salva em `~/.tradutor_master/config.json` (local)
- ✅ **NÃO** salva no banco de dados MySQL
- ✅ Cada usuário usa sua própria chave Anthropic

### 2️⃣ Nome da Empresa Protegido
- ✅ Configure o nome da empresa uma única vez
- ✅ Claude NUNCA traduzirá esse nome
- ✅ Preserva exatamente como aparece no original
- ✅ Funciona em TODOS os documentos

## 📝 Como Configurar

### Passo 1: Abra as Preferências
1. Abra o **Tradutor Master**
2. Clique na aba **"⚙ Preferências"**
3. Procure a seção **"🏢 Proteção de Nome da Empresa"**

### Passo 2: Configure o Nome
1. Digite o nome EXATO da sua empresa
   - Exemplo: `"ACME Corporation"`
   - Exemplo: `"Minha Empresa Lda"`
   - Exemplo: `"Tech Solutions Inc"`

2. Clique em **"Salvar Preferências"**

### Passo 3: Pronto!
- ✅ Agora todas as traduções preservarão o nome da empresa
- ✅ O Claude receberá instrução EXPLÍCITA para não traduzir

## 🔒 Como Funciona

### Na Configuração:
```
📁 ~/.tradutor_master/
  └─ config.json
     {
       "claude_api_key": "sk-ant-api...",  ← Sua chave (local)
       "company_name": "ACME Corporation",  ← Nome da empresa
       ...
     }
```

### Na Tradução:
Quando você traduz um documento, o Claude recebe (EM INGLÊS para máxima clareza):

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

**Por que em inglês?**
- O Claude é treinado principalmente em inglês
- Instruções em inglês são processadas com maior precisão
- Garante que o nome da empresa NÃO seja traduzido no próprio prompt

## 📊 Exemplo Prático

### Documento Original (Inglês):
```
ACME Corporation
123 Main Street, New York

Dear Customer,

Thank you for choosing ACME Corporation for your business needs.
We at ACME Corporation are committed to excellence.

Best regards,
ACME Corporation Team
```

### Tradução (Português):
```
ACME Corporation  ← PRESERVADO!
123 Main Street, Nova York

Prezado Cliente,

Obrigado por escolher a ACME Corporation para suas necessidades empresariais.
Nós da ACME Corporation estamos comprometidos com a excelência.

Atenciosamente,
Equipe ACME Corporation
```

## ⚠️ Importante

### O que é Protegido:
- ✅ Nome exato da empresa
- ✅ Em qualquer posição do texto
- ✅ Com maiúsculas/minúsculas preservadas
- ✅ Em todos os documentos traduzidos

### O que NÃO é Protegido:
- ❌ Variações do nome (configure no dicionário se necessário)
- ❌ Abreviações diferentes (use o dicionário)
- ❌ Nomes de produtos (use o dicionário)

## 💡 Dicas

### Empresa com Múltiplas Variações:
Se sua empresa aparece de formas diferentes, use o **Dicionário**:

**Nome Principal** (Preferências):
```
ACME Corporation
```

**Variações** (Dicionário):
```
ACME Corp → ACME Corp
ACME → ACME
The ACME Corporation → The ACME Corporation
```

### Grupos Empresariais:
Para grupos com várias empresas, liste a principal:

**Preferências**:
```
ACME Holdings
```

**Dicionário**:
```
ACME Corporation → ACME Corporation
ACME Technologies → ACME Technologies
ACME Solutions → ACME Solutions
```

## 🔐 Segurança da API Key

### Onde é Salva:
```
Windows: C:\Users\SeuNome\.tradutor_master\config.json
Linux/Mac: /home/seuNome/.tradutor_master/config.json
```

### Quem tem Acesso:
- ✅ Apenas o usuário do sistema operacional
- ✅ Arquivo local, não compartilhado
- ✅ **NÃO** vai para o banco de dados MySQL
- ✅ Cada instalação tem sua própria chave

### Benefícios:
- ✅ **Privacidade**: Sua chave é só sua
- ✅ **Controle**: Você gerencia seu uso
- ✅ **Segurança**: Não exposta em rede
- ✅ **Independência**: Cada usuário com sua conta Anthropic

## 📋 Checklist de Configuração

- [ ] Abri a aba "⚙ Preferências"
- [ ] Configurei minha API Key do Claude (aba "🤖 Claude API")
- [ ] Digitei o nome da minha empresa em "🏢 Proteção de Nome da Empresa"
- [ ] Cliquei em "Salvar Preferências"
- [ ] Testei traduzindo um documento com o nome da empresa
- [ ] Verifiquei que o nome foi preservado corretamente

## 🎉 Pronto!

Agora você pode traduzir todos os seus documentos com a garantia de que:
- ✅ O nome da empresa está protegido
- ✅ Sua API key é privada e local
- ✅ Claude seguirá as instruções rigorosamente

---

**Arquivos Modificados**:
- [src/config_manager.py](src/config_manager.py) - Adicionado campo `company_name`
- [src/claude_client.py](src/claude_client.py) - Proteção no prompt do Claude
- [src/ui.py](src/ui.py) - Interface de configuração

**Local do Config**:
- `~/.tradutor_master/config.json`
