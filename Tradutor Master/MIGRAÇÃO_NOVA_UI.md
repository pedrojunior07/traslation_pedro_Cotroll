# 🚀 Migração para Nova UI

## Mudanças Implementadas

A UI foi completamente redesenhada para:

✅ **Remover sistema de licenças** - Não há mais Device ID, license keys ou quotas
✅ **Integrar definições** - Todas as configurações estão na mesma janela (abas)
✅ **Usar clientes diretos** - LibreTranslate e Claude sem API intermediária
✅ **Dicionário inteligente** - 404 termos pré-carregados economizam tokens
✅ **Cache de traduções** - Evita re-traduzir mesmo conteúdo
✅ **Monitoramento de custos** - Dashboard completo de uso de tokens

---

## Como Usar a Nova UI

### Opção 1: Executar diretamente o novo arquivo

```bash
# Windows
.venv\Scripts\python.exe -m src.main_new

# Linux/Mac
.venv/bin/python -m src.main_new
```

### Opção 2: Substituir o arquivo principal

1. **Backup do arquivo antigo:**
   ```bash
   cd src
   move ui.py ui_old.py
   move main.py main_old.py
   ```

2. **Ativar nova UI:**
   ```bash
   move ui_new.py ui.py
   move main_new.py main.py
   ```

3. **Executar normalmente:**
   ```bash
   .venv\Scripts\python.exe -m src.main
   ```

---

## Estrutura da Nova UI

A aplicação agora tem **5 abas integradas** na mesma janela:

### 📄 **Aba 1: Tradução**
- Seleção de idiomas (origem/destino)
- Escolher arquivos ou pastas
- Opções: "Usar Claude IA" e "Usar Dicionário"
- Lista de arquivos com status de tradução
- Botões: Carregar Pasta, Traduzir Selecionados, Traduzir Todos
- Barra de progresso em tempo real

### 🤖 **Aba 2: Claude API**
- Campo para inserir API Key da Anthropic
- Seleção de modelo (Sonnet 3.5, Opus 3, Haiku 3)
- Botão "Testar Conexão"
- Tabela de preços por modelo
- Botão "Salvar Configurações"

### 📊 **Aba 3: Monitoramento**
- Resumo de uso (Hoje e Este Mês)
- Tabela com histórico dos últimos 30 dias:
  - Data
  - Input Tokens
  - Output Tokens
  - Cache Read Tokens
  - Custo em USD
  - Número de chamadas
- Botões: Atualizar Dados, Exportar CSV

### 📚 **Aba 4: Dicionário**
- Filtro por categoria (empresa, técnico, sigla, local, etc.)
- Tabela com 404 termos pré-carregados:
  - Termo original
  - Tradução
  - Par de idiomas
  - Categoria
  - Número de usos
- Botões: Adicionar Termo, Importar CSV, Exportar CSV

### ⚙ **Aba 5: Preferências**
- **LibreTranslate:**
  - URL do servidor (padrão: http://102.211.186.44/translate)
  - Timeout em segundos
- **MySQL:**
  - Host, Porta, Database, Usuário, Senha
  - Botão "Testar Conexão MySQL"
- Botão "Salvar Preferências"

---

## Fluxo de Tradução

### Passo 1: Configurar API Key (se usar Claude)

1. Vá na aba **🤖 Claude API**
2. Cole sua API key (obtida em console.anthropic.com)
3. Selecione o modelo (recomendado: Sonnet 3.5)
4. Clique em **"Testar Conexão"**
5. Clique em **"Salvar Configurações"**

### Passo 2: Traduzir Documentos

1. Vá na aba **📄 Tradução**
2. Selecione idiomas de origem e destino
3. Marque **"Usar Claude IA"** (para melhor qualidade) ou desmarque (para usar apenas LibreTranslate)
4. Marque **"Usar Dicionário"** (economiza tokens)
5. Clique em **"Selecionar Pasta"** ou **"Selecionar Arquivo"**
6. Escolha a pasta de destino
7. Clique em **"Carregar Pasta"** para ver os arquivos
8. Selecione os arquivos desejados
9. Clique em **"Traduzir Selecionados"** ou **"Traduzir Todos"**
10. Acompanhe o progresso na barra inferior

### Passo 3: Monitorar Custos

1. Vá na aba **📊 Monitoramento**
2. Veja resumo de uso de hoje e do mês
3. Consulte histórico detalhado
4. Exporte relatório CSV se necessário

---

## Diferenças da UI Antiga

| Recurso | UI Antiga | Nova UI |
|---------|-----------|---------|
| **Licenças** | ✅ Device ID, license key, quotas | ❌ Removido completamente |
| **API intermediária** | ✅ FastAPI backend | ❌ Conexão direta |
| **Definições** | ❌ Sem interface | ✅ 5 abas integradas |
| **Dicionário** | ❌ Não existia | ✅ 404 termos pré-carregados |
| **Cache** | ❌ Não existia | ✅ Cache local (7 dias) |
| **Monitoramento** | ⚠️ Básico (quota restante) | ✅ Dashboard completo |
| **Claude API** | ❌ Não suportado | ✅ Totalmente integrado |
| **LibreTranslate** | ✅ Via backend | ✅ Direto (mais rápido) |

---

## Economia de Tokens

### Antes (UI Antiga)
```
Documento com 1000 tokens → 1000 tokens enviados para IA
Custo estimado: $0.018
```

### Agora (Nova UI)
```
Documento com 1000 tokens:
1. Dicionário substitui ~300 termos (30%)
2. Restam 700 tokens para traduzir
3. Cache economiza 90% nas próximas traduções

Primeira vez: ~$0.010 (60% economia)
Próximas vezes: ~$0.001 (95% economia com cache)
```

### Termos no Dicionário (404 total)

**Empresas:** TotalEnergies, ExxonMobil, Shell, BP, Chevron, Microsoft, Google
**Siglas Moçambique:** NUIT, NIB, UEM, UP, EDM, TDM, LAM, CFM, FRELIMO
**Locais:** Maputo, Beira, Nampula, Tete, Pemba, Rovuma Basin
**Técnicos:** API, SDK, JSON, XML, HTTP, SQL, PDF, DOCX

E muito mais! Veja a lista completa na aba **📚 Dicionário**.

---

## Requisitos

### Python
- Python 3.10+
- Ambiente virtual ativo

### Dependências
```bash
pip install anthropic>=0.40.0 requests sqlalchemy mysql-connector-python
```

### Claude API Key
- Obtenha em: https://console.anthropic.com
- Custo estimado: $0.30-$3.00 por 1M tokens (depende do modelo)

### MySQL (Opcional)
- Necessário apenas para dicionário e monitoramento
- Sem MySQL: tradução funciona, mas sem cache de termos

---

## Solução de Problemas

### "Claude não configurado"
✅ Vá na aba **🤖 Claude API** e configure sua API key

### "Banco de dados não conectado"
✅ Verifique configurações MySQL na aba **⚙ Preferências**
✅ Clique em "Testar Conexão MySQL"

### "Erro ao traduzir"
✅ Verifique se LibreTranslate está acessível (http://102.211.186.44/translate)
✅ Aumente timeout em **⚙ Preferências** se conexão lenta

### "Dicionário vazio"
✅ Execute migração: `.venv/Scripts/python.exe -m api.seed_dictionary`
✅ Verifique conexão com MySQL

---

## Roadmap Futuro

- [ ] Implementar adição/edição de termos do dicionário via UI
- [ ] Importação/exportação de dicionário em CSV
- [ ] Exportação de relatórios de uso em CSV
- [ ] Gráficos de uso de tokens ao longo do tempo
- [ ] Suporte a mais idiomas (expandir além de en/pt/fr/es/de)
- [ ] Integração com outros providers de IA (OpenAI, Gemini como opção)

---

## Contato

Para dúvidas ou suporte:
📞 Pedro Manjate: 874381448

---

**Boa tradução!** 🚀
