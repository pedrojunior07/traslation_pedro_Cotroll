# Guia do Usuário - Tradutor Master Desktop

## 📱 Introdução

Bem-vindo ao **Tradutor Master Desktop**! Este aplicativo permite traduzir documentos mantendo sua formatação original, com controle de qualidade e proteção de termos técnicos.

---

## 🚀 Primeiros Passos

### 1. Instalação

1. Certifique-se de ter Python 3.10+ instalado
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie o aplicativo:
   ```bash
   python src/main.py
   ```

### 2. Primeira Configuração

Ao abrir o aplicativo pela primeira vez, você verá:

```
┌─────────────────────────────────────┐
│     Tradutor Master Desktop         │
└─────────────────────────────────────┘

┌── API e Licença ───────────────────┐
│ Base URL: http://127.0.0.1:8000    │
│ Licença: ___________________       │
│ Device ID: SEU_COMPUTADOR          │
│ Nome dispositivo: ____________     │
│                                    │
│ [Registrar Dispositivo]            │
└────────────────────────────────────┘
```

**Passo a passo:**

1. **Base URL**: Insira o endereço do servidor da API
   - Local: `http://127.0.0.1:8000`
   - Rede: `http://192.168.1.100:8000`
   - Internet: `https://api.tradutormaster.com`

2. **Licença**: Insira a chave de licença fornecida
   - Formato: `ABC123XYZ456`
   - Obtida com o administrador do sistema

3. **Device ID**: Identificador único do seu dispositivo
   - Gerado automaticamente com nome do computador
   - Pode ser personalizado

4. **Nome dispositivo**: Nome amigável (opcional)
   - Ex: "Computador do João", "Notebook Escritório"

5. Clique em **"Registrar Dispositivo"**

✅ Se tudo estiver correto, você verá:
- Status da licença: "Ativa"
- Dias restantes
- Quota disponível

---

## 📄 Traduzindo Documentos

### Modo: Arquivo Único

Use este modo para traduzir um único arquivo rapidamente.

1. Marque a opção ☑️ **"Arquivo Único"**
2. Clique em **"Selecionar Arquivo"**
3. Escolha o arquivo (DOCX, PPTX, XLSX, TXT ou PDF)
4. Selecione idiomas:
   - **De:** Idioma original
   - **Para:** Idioma destino
5. Clique em **"Traduzir"**

O arquivo traduzido será salvo no mesmo diretório com sufixo `_translated`.

**Exemplo:**
```
documento.docx  →  documento_translated.docx
```

---

### Modo: Lote (Múltiplos Arquivos)

Use este modo para traduzir vários arquivos de uma vez.

1. Desmarque ☐ **"Arquivo Único"**
2. **Pasta de Entrada**: Clique em "..." e selecione pasta com arquivos originais
3. **Pasta de Saída**: Clique em "..." e selecione onde salvar traduções
4. Clique em **"Carregar Arquivos"**
5. Visualize a lista de arquivos encontrados
6. (Opcional) Configure opções avançadas
7. Clique em **"Traduzir"**

**Opções:**
- ☑️ **Skip Existing**: Pula arquivos já traduzidos
- ☑️ **AI Evaluate**: Usa IA para identificar termos não-traduzíveis
- ☑️ **AI Glossary**: Cria glossário automático
- ☑️ **AI Translate**: Usa tradução com IA (mais lento, mais preciso)

**Progresso:**
```
Arquivos: 3/10
Arquivo: documento.docx
ETA: 5m 23s
[████████░░░░░░░░░░] 45%
```

---

## ⚙️ Opções Avançadas

### AI Evaluate ⭐

Usa inteligência artificial para identificar termos que **não devem** ser traduzidos:
- Nomes próprios (NASA, Google, Microsoft)
- Siglas técnicas (API, SQL, HTTP)
- Marcas registradas
- Códigos e identificadores

**Como funciona:**
1. Antes de traduzir, todos os textos são enviados para a IA
2. A IA marca termos não-traduzíveis
3. Esses termos são protegidos durante a tradução
4. Resultado: tradução mais precisa

**Quando usar:**
- ✅ Documentação técnica
- ✅ Manuais com muitos termos específicos
- ✅ Textos com nomes de produtos
- ❌ Textos simples sem termos técnicos (economiza quota)

---

### AI Glossary

Cria um glossário automático de termos técnicos:
- Identifica termos importantes
- Sugere traduções ou mantém original
- Aplica consistência em todo o documento

**Exemplo de glossário:**
```
API        → API
Database   → Banco de Dados
Cache      → Cache
Login      → Login
```

**Quando usar:**
- ✅ Documentos longos com termos repetidos
- ✅ Séries de documentos relacionados
- ✅ Padronização de traduções
- ❌ Documentos curtos ou únicos

---

### AI Translate

Usa o modelo de IA (OpenAI GPT) para traduzir:
- Considera contexto completo
- Usa glossário se disponível
- Tradução mais natural e precisa

**Vantagens:**
- ✅ Qualidade superior
- ✅ Entende contexto
- ✅ Preserva tom e estilo

**Desvantagens:**
- ❌ Mais lento (3-5x)
- ❌ Consome mais quota
- ❌ Requer configuração de OpenAI

**Quando usar:**
- ✅ Documentos importantes
- ✅ Textos para publicação
- ✅ Conteúdo de marketing
- ❌ Rascunhos ou documentos internos

---

## 📊 Visualizando Traduções ⭐ NOVO

### Tabela de Tokens

Acesse informações detalhadas de suas traduções:

1. Clique em **"Ver Tokens"** no menu
2. Selecione uma tradução da lista
3. Visualize todos os tokens:

```
┌─────────────────────────────────────────────────────────────┐
│ Traduções Recentes                                          │
├─────┬────────────┬────────┬─────────┬─────────┬────────────┤
│ ID  │ Data/Hora  │ Origem │ Destino │ Tokens  │ Chars Orig │
├─────┼────────────┼────────┼─────────┼─────────┼────────────┤
│ 123 │ 2025-12-25 │   en   │   pt    │   15    │    450     │
│ 122 │ 2025-12-24 │   en   │   es    │    8    │    220     │
└─────┴────────────┴────────┴─────────┴─────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Detalhes dos Tokens                                         │
├──────────────┬──────────────┬──────────┬───────┬───────────┤
│ Localização  │ Original     │ Traduzido│ Ratio │ Truncado  │
├──────────────┼──────────────┼──────────┼───────┼───────────┤
│ Paragrafo 1  │ Hello World  │ Olá Mundo│  0.82 │    Não    │
│ Tabela 1 L1C1│ Very long... │ Texto... │  1.06 │    Sim ⚠️ │
└──────────────┴──────────────┴──────────┴───────┴───────────┘
```

**Informações exibidas:**
- **Localização**: Onde o token está no documento
- **Original**: Texto original (truncado para exibição)
- **Traduzido**: Texto traduzido
- **Len Orig / Len Trad**: Comprimentos
- **Ratio**: Razão traduzido/original
- **Truncado**: Se foi cortado por exceder limite
- **Avisos**: Mensagens de alerta

**Cores:**
- 🟡 Amarelo: Token foi truncado
- 🔴 Vermelho: Token com avisos

---

### Estatísticas ⭐ NOVO

Veja estatísticas gerais de suas traduções:

```
┌─────────────────────────────────────┐
│ Estatísticas Gerais de Tradução     │
├─────────────────────────────────────┤
│ Total de Tokens Traduzidos:  1,523  │
│ Total de Caracteres Originais: 45,678│
│ Total de Caracteres Traduzidos: 52,341│
│ Razão Média de Tamanho:      1.15x  │
│ Tokens Truncados:               23  │
└─────────────────────────────────────┘
```

**Interpretação:**
- **Razão 1.15x**: Textos traduzidos são 15% maiores que originais
- **23 tokens truncados**: 23 vezes o texto foi cortado por exceder limite

---

## 🎯 Controle de Qualidade ⭐ NOVO

### Problema: Texto Traduzido Extrapola Limites

**Sintomas:**
- Texto sai das margens
- Texto vai para próxima página
- Células de tabela muito cheias
- Formas de slide com overflow

**Solução Automática Implementada:**

O sistema agora possui:

1. **Detecção de Crescimento**
   - Compara tamanho original vs traduzido
   - Calcula razão de crescimento
   - Gera avisos se exceder 20%

2. **Truncamento Inteligente**
   - Corta texto que exceder limite
   - Tenta quebrar em espaços
   - Adiciona "..." para indicar corte
   - Limite padrão: 150% do original

3. **Ajuste de Fonte** (opcional)
   - Reduz tamanho da fonte automaticamente
   - Mantém texto legível (mínimo 70% do original)
   - Disponível para DOCX e PPTX

**Configuração:**

Por padrão, o sistema está configurado para:
- ✅ Permitir até 50% de crescimento
- ✅ Truncar se exceder
- ❌ Ajuste de fonte (desabilitado por padrão)

Para alterar, contacte o administrador ou modifique `translator.py`.

---

### Avisos Comuns

#### ⚠️ "Texto traduzido cresceu 45% em relação ao original"
**Significado:** Tradução ficou muito maior que original
**Ação:** Nenhuma, apenas informativo
**Impacto:** Pode afetar layout

#### ⚠️ "Texto truncado para 150 caracteres"
**Significado:** Texto foi cortado porque ficou muito grande
**Ação:** Revisar tradução manualmente
**Impacto:** Informação pode ter sido perdida

#### ⚠️ "Fonte reduzida de 12.0pt para 10.5pt"
**Significado:** Fonte foi reduzida para caber texto
**Ação:** Verificar se ficou legível
**Impacto:** Texto menor, mas completo

---

## 📈 Monitoramento de Quota

### Indicadores de Uso

No topo da interface, você vê:

```
┌────────────────────────────────────────┐
│ Uso: 245/500 (Diário)                  │
│ Dias restantes: 45                     │
│ Licença: Ativa                         │
└────────────────────────────────────────┘
```

**Informações:**
- **Uso**: Consumo atual / Limite (Período)
- **Dias restantes**: Até expiração da licença
- **Status**: Ativa, Expirada ou Bloqueada

### Tipos de Quota

#### DIÁRIA
- Reseta todos os dias à meia-noite
- Ideal para uso diário controlado
- **Exemplo:** 500 traduções por dia

#### MENSAL
- Reseta no dia 1 de cada mês
- Flexível para picos de uso
- **Exemplo:** 10.000 traduções por mês

#### TOTAL
- Nunca reseta, conta total
- Para licenças com limite fixo
- **Exemplo:** 50.000 traduções (lifetime)

#### ILIMITADA (NONE)
- Sem limites
- Para licenças premium
- Apenas controla expiração

---

## 🔧 Solução de Problemas

### Erro: "Licença Inválida"

**Causas:**
- Chave de licença incorreta
- Licença expirada
- Licença desativada

**Soluções:**
1. Verifique se digitou a chave corretamente
2. Contacte administrador para verificar status
3. Renove a licença se expirou

---

### Erro: "Quota Excedida"

**Causas:**
- Atingiu o limite diário/mensal/total
- Dispositivo foi bloqueado

**Soluções:**
1. **Quota Diária**: Aguarde até amanhã
2. **Quota Mensal**: Aguarde próximo mês
3. **Quota Total**: Renove ou compre nova licença
4. Contacte administrador para aumentar limite

---

### Erro: "Limite de Dispositivos Atingido"

**Causas:**
- Licença já tem número máximo de dispositivos registrados

**Soluções:**
1. Remova um dispositivo antigo (via admin)
2. Compre licença com mais dispositivos
3. Use um dispositivo já registrado

---

### Tradução com Qualidade Ruim

**Possíveis causas e soluções:**

| Problema | Solução |
|----------|---------|
| Termos técnicos traduzidos | Ative "AI Evaluate" |
| Nomes próprios traduzidos | Ative "AI Evaluate" |
| Tradução literal demais | Ative "AI Translate" |
| Inconsistência de termos | Use "AI Glossary" |
| Texto sem sentido | Verifique idiomas selecionados |

---

### Arquivo Não Carrega

**Formatos suportados:**
- ✅ .docx (não .doc)
- ✅ .pptx, .ppsx (não .ppt)
- ✅ .xlsx, .xlsm (não .xls)
- ✅ .txt
- ✅ .pdf

**Se o arquivo não carregar:**
1. Verifique a extensão
2. Tente abrir o arquivo no aplicativo nativo
3. Se estiver corrompido, repare antes
4. Converta formatos antigos (.doc → .docx)

---

### Aplicativo Travou Durante Tradução

**O que fazer:**
1. Aguarde alguns minutos (pode estar processando)
2. Verifique conexão com a API
3. Feche e reabra o aplicativo
4. Arquivos já traduzidos não serão refeitos (se "Skip Existing" ativo)

---

## 💡 Dicas e Melhores Práticas

### 1. Organize seus Arquivos
```
📁 Projeto/
├── 📁 originais/
│   ├── documento1.docx
│   ├── documento2.docx
│   └── apresentacao.pptx
└── 📁 traduzidos/
    ├── documento1_translated.docx
    ├── documento2_translated.docx
    └── apresentacao_translated.pptx
```

### 2. Use Modo Lote para Eficiência
- Processe vários arquivos de uma vez
- Ative "Skip Existing" para não refazer traduções
- Economize tempo e quota

### 3. AI Evaluate em Documentação Técnica
- Sempre ative para manuais técnicos
- Protege siglas, nomes de comandos, APIs
- Melhora qualidade significativamente

### 4. Crie Glossário para Projetos
- Use "AI Glossary" no primeiro documento
- Salve os termos para referência
- Mantenha consistência em todos os documentos

### 5. Monitore sua Quota
- Verifique uso regularmente
- Planeje traduções grandes
- Evite surpresas de bloqueio

### 6. Revise Traduções Importantes
- Sempre revise documentos críticos
- Use visualização de tokens para checar qualidade
- Verifique se termos técnicos foram preservados

### 7. Ajuste de Tamanho ⭐
- Para documentos com layout rigoroso, monitore avisos
- Se muitos tokens forem truncados, considere:
  - Simplificar texto original
  - Revisar manualmente
  - Aumentar limite (via código)

---

## 📞 Suporte

### Precisa de Ajuda?

**Suporte Técnico:**
- Email: suporte@tradutormaster.com
- Horário: Seg-Sex 9h-18h

**Documentação:**
- README.md - Visão geral do projeto
- API_DOCUMENTATION.md - Documentação da API
- Este guia - Manual do usuário

**Problemas Conhecidos:**
- Consulte GitHub Issues
- Verifique atualizações

---

## 🔄 Atualizações

### Como Atualizar

1. Baixe nova versão do repositório
2. Instale novas dependências:
   ```bash
   pip install -r requirements.txt --upgrade
   ```
3. Execute migrações se necessário
4. Reinicie o aplicativo

### Changelog

**Versão 2.0.0** ⭐ (Dezembro 2025)
- ➕ Sistema de ajuste de tamanho de texto
- ➕ Visualização de tabela de tokens
- ➕ Estatísticas detalhadas de tradução
- ➕ Controle de qualidade com avisos
- ➕ Rastreamento de tokens no banco
- 🔧 Melhorias de performance
- 🐛 Correções de bugs

**Versão 1.0.0** (Janeiro 2025)
- ✨ Lançamento inicial
- Tradução de múltiplos formatos
- Sistema de licenças
- Integração com OpenAI
- Token Guard

---

## 🎓 Tutorial Passo a Passo Completo

### Cenário: Traduzir Manual Técnico (EN → PT)

**Passo 1:** Configure a aplicação
```
1. Abra Tradutor Master Desktop
2. Insira URL da API: http://localhost:8000
3. Insira sua licença: ABC123XYZ456
4. Clique "Registrar Dispositivo"
5. Confirme: Licença Ativa ✓
```

**Passo 2:** Prepare os arquivos
```
1. Crie pasta: C:\Traducao\Originais
2. Copie arquivos .docx para lá
3. Crie pasta: C:\Traducao\Traduzidos
```

**Passo 3:** Configure tradução
```
1. Pasta de Entrada: C:\Traducao\Originais
2. Pasta de Saída: C:\Traducao\Traduzidos
3. De: English
4. Para: Portuguese
5. ✓ AI Evaluate
6. ✓ AI Glossary
7. ✗ AI Translate (usar tradução rápida)
```

**Passo 4:** Carregue e traduza
```
1. Clique "Carregar Arquivos"
2. Verifique lista (ex: 5 arquivos)
3. Clique "Traduzir"
4. Aguarde conclusão (ETA: 10m)
```

**Passo 5:** Verifique resultado
```
1. Abra arquivos traduzidos
2. Clique "Ver Tokens"
3. Selecione primeira tradução
4. Verifique avisos
5. Se houver truncamentos, revise manualmente
```

**Passo 6:** Revise e finalize
```
1. Abra documentos traduzidos
2. Revise formatação
3. Corrija truncamentos se necessário
4. Salve versão final
```

---

**Versão:** 2.0.0
**Última Atualização:** Dezembro 2025
**Suporte:** suporte@tradutormaster.com
