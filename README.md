# Tradutor Master

Sistema completo de tradução de documentos com controle de licenças, quotas e qualidade de tradução.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Características](#características)
- [Arquitetura](#arquitetura)
- [Instalação](#instalação)
- [Uso](#uso)
- [API](#api)
- [Configuração](#configuração)
- [Desenvolvimento](#desenvolvimento)

---

## 🌟 Visão Geral

O **Tradutor Master** é um sistema cliente-servidor para tradução profissional de documentos, com as seguintes funcionalidades:

### Backend (API FastAPI)
- Sistema de licenças e dispositivos
- Controle de quotas (diária, mensal, total)
- Integração com serviços de tradução
- Integração com OpenAI para IA contextual
- Rastreamento detalhado de tokens traduzidos
- Sistema de controle de qualidade de tradução

### Frontend (Desktop Tkinter)
- Interface gráfica intuitiva
- Tradução em lote de arquivos
- Proteção de tokens não-traduzíveis
- Visualização detalhada de traduções
- Estatísticas de uso em tempo real
- **NOVO:** Sistema de ajuste automático de tamanho de texto
- **NOVO:** Visualização de tabela de tokens com análise

---

## ✨ Características

### Formatos Suportados
- **DOCX** - Documentos Microsoft Word
- **PPTX/PPSX** - Apresentações PowerPoint
- **XLSX/XLSM** - Planilhas Excel
- **TXT** - Arquivos de texto
- **PDF** - Documentos PDF (convertidos para DOCX)

### Controle de Qualidade ⭐ NOVO
- **Ajuste Automático de Tamanho**: Controla que texto traduzido não extrapole limites
- **Truncamento Inteligente**: Corta texto em espaços, não no meio de palavras
- **Ajuste de Fonte**: Opção para reduzir tamanho de fonte automaticamente
- **Avisos Detalhados**: Sistema de avisos para traduções problemáticas
- **Razão de Tamanho**: Monitora crescimento do texto (original vs traduzido)

### Sistema de Tokens ⭐ NOVO
- **Rastreamento Detalhado**: Cada token traduzido é salvo com métricas
- **Tabela de Visualização**: Interface para ver todos os tokens de uma tradução
- **Estatísticas**: Total de caracteres, razão média, tokens truncados
- **Histórico**: Acesso a traduções anteriores com todos os detalhes
- **Avisos**: Sistema de alertas para problemas de tradução

### Proteção de Tokens
- URLs, emails, números, códigos
- Caminhos de arquivo
- Tags HTML/XML
- Detecção com IA de nomes, marcas, IDs

### Sistema de Licenças
- Quotas flexíveis (diária, mensal, total, ilimitada)
- Múltiplos dispositivos por licença
- Data de expiração
- Bloqueio automático ao atingir limite

### Inteligência Artificial
- Tradução contextual com OpenAI
- Construção automática de glossário
- Avaliação de traduzibilidade
- Identificação de entidades não-traduzíveis

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────┐
│          CLIENTE DESKTOP                │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Interface Tkinter (ui.py)       │  │
│  │  - Seleção de arquivos           │  │
│  │  - Configuração de tradução      │  │
│  │  - Visualização de progresso     │  │
│  │  - Tabela de tokens ⭐ NOVO      │  │
│  │  - Estatísticas ⭐ NOVO          │  │
│  └───────────────┬──────────────────┘  │
│                  │                      │
│  ┌───────────────▼──────────────────┐  │
│  │  Processamento de Documentos     │  │
│  │  - Extrator (extractor.py)       │  │
│  │  - Tradutor (translator.py)      │  │
│  │  - Ajustador ⭐ NOVO             │  │
│  │  - Token Guard (token_guard.py)  │  │
│  └───────────────┬──────────────────┘  │
│                  │                      │
│  ┌───────────────▼──────────────────┐  │
│  │  Cliente API (api_client.py)     │  │
│  └───────────────┬──────────────────┘  │
└──────────────────┼──────────────────────┘
                   │ HTTPS
                   │
┌──────────────────▼──────────────────────┐
│             API FastAPI                 │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Routers                         │  │
│  │  - /translate                    │  │
│  │  - /ai/*                         │  │
│  │  - /devices                      │  │
│  │  - /licenses                     │  │
│  │  - /translation_tokens ⭐ NOVO   │  │
│  └───────────────┬──────────────────┘  │
│                  │                      │
│  ┌───────────────▼──────────────────┐  │
│  │  Serviços (services.py)          │  │
│  │  - Tradução externa              │  │
│  │  - OpenAI                        │  │
│  └───────────────┬──────────────────┘  │
│                  │                      │
│  ┌───────────────▼──────────────────┐  │
│  │  Banco de Dados MySQL            │  │
│  │  - users                         │  │
│  │  - licenses                      │  │
│  │  - devices                       │  │
│  │  - translation_logs              │  │
│  │  - translation_tokens ⭐ NOVO    │  │
│  │  - ai_config                     │  │
│  │  - translate_config              │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 📥 Instalação

### Requisitos
- Python 3.10+
- MySQL 5.7+
- Sistema operacional: Windows, Linux ou macOS

### 1. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/traslation_pedro_Cotroll.git
cd traslation_pedro_Cotroll
```

### 2. Instale as Dependências
```bash
pip install -r "Tradutor Master/requirements.txt"
```

### 3. Configure o Banco de Dados

Crie o banco de dados MySQL:
```sql
CREATE DATABASE tradutor_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na pasta `Tradutor Master/api/`:

```env
# Banco de Dados
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=tradutor_db

# JWT
JWT_SECRET=sua_chave_secreta_aqui

# Superadmin
SUPERADMIN_USER=admin
SUPERADMIN_PASSWORD=admin123

# OpenAI (opcional)
OPENAI_API_KEY=sk-...
```

### 5. Execute a Migração para Tokens ⭐ NOVO

```bash
cd "Tradutor Master/api"
python migrate_add_translation_tokens.py
```

### 6. Inicie a API

```bash
cd "Tradutor Master/api"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Inicie o Cliente Desktop

```bash
cd "Tradutor Master/src"
python main.py
```

---

## 🚀 Uso

### Primeiro Acesso

1. **Crie uma Licença** (via API ou interface admin):
   - Acesse `http://localhost:8000/admin`
   - Faça login com credenciais de superadmin
   - Crie uma nova licença com os limites desejados

2. **Registre o Dispositivo**:
   - Abra o aplicativo desktop
   - Insira a URL da API
   - Insira a chave de licença
   - Configure o ID e nome do dispositivo
   - Clique em "Registrar Dispositivo"

### Traduzindo Documentos

#### Modo Arquivo Único
1. Ative a opção "Arquivo Único"
2. Clique em "Selecionar Arquivo"
3. Escolha idioma de origem e destino
4. Clique em "Traduzir"

#### Modo Lote
1. Selecione "Pasta de Entrada"
2. Selecione "Pasta de Saída"
3. Escolha idiomas
4. Configure opções (AI, Glossário, etc.)
5. Clique em "Carregar Arquivos"
6. Clique em "Traduzir"

### Opções Avançadas ⭐ NOVO

#### Controle de Tamanho de Texto
No código, você pode configurar o `translator.py`:

```python
warnings = export_translated_document(
    source_path="documento.docx",
    tokens=tokens,
    output_path="documento_traduzido.docx",
    enable_size_adjustment=True,  # Ativa ajuste de tamanho
    max_length_ratio=1.5,  # Permite até 50% de crescimento
    adjust_font_size=True,  # Reduz fonte se necessário
)
```

#### Visualizar Tabela de Tokens
1. No menu principal, clique em "Ver Tokens" (adicionar ao menu)
2. Selecione uma tradução da lista
3. Visualize todos os tokens com:
   - Localização no documento
   - Texto original e traduzido
   - Comprimentos e razão
   - Status de truncamento
   - Avisos

#### Estatísticas de Tokens
1. Clique em "Estatísticas"
2. Veja:
   - Total de tokens traduzidos
   - Total de caracteres processados
   - Razão média de tamanho
   - Quantidade de tokens truncados

---

## 📡 API

### Endpoints Principais

#### Autenticação
```http
POST /devices/register
Body: {
  "license_key": "ABC123",
  "device_id": "DEVICE001",
  "device_name": "Meu Computador"
}
Response: { "device_token": "..." }
```

#### Tradução
```http
POST /translate
Headers: Authorization: Bearer {device_token}
Body: {
  "text": "Hello World",
  "source": "en",
  "target": "pt",
  "units": 1
}
Response: { "translatedText": "Olá Mundo" }
```

#### Tokens de Tradução ⭐ NOVO
```http
GET /translations/recent?limit=10
Headers: Authorization: Bearer {device_token}
Response: [
  {
    "id": 123,
    "source": "en",
    "target": "pt",
    "created_at": "2025-12-25T10:00:00",
    "tokens": [
      {
        "location": "Paragrafo 1",
        "original_text": "Hello",
        "translated_text": "Olá",
        "original_length": 5,
        "translated_length": 3,
        "was_truncated": false,
        "size_ratio": 0.6,
        "warnings": []
      }
    ]
  }
]
```

```http
GET /translation/{translation_log_id}/tokens
Headers: Authorization: Bearer {device_token}
Response: [array de tokens]
```

```http
GET /tokens/statistics
Headers: Authorization: Bearer {device_token}
Response: {
  "total_tokens": 1523,
  "total_original_chars": 45678,
  "total_translated_chars": 52341,
  "average_size_ratio": 1.15,
  "truncated_count": 23
}
```

#### Uso e Quotas
```http
GET /usage
Headers: Authorization: Bearer {device_token}
Response: {
  "usage_today": 45,
  "usage_month_count": 320,
  "total_usage": 1523,
  "quota_limit": 500,
  "quota_period": "DAILY",
  "quota_remaining": 455
}
```

### Documentação Completa
Acesse `http://localhost:8000/docs` para ver a documentação interativa Swagger.

---

## ⚙️ Configuração

### Configuração da API

A API pode ser configurada via banco de dados na tabela `ai_config` e `translate_config`:

#### OpenAI
```sql
UPDATE ai_config SET
  enabled = TRUE,
  base_url = 'https://api.openai.com/v1',
  model = 'gpt-4o-mini',
  api_key = 'sk-...'
WHERE id = 1;
```

#### Serviço de Tradução
```sql
UPDATE translate_config SET
  base_url = 'http://102.211.186.44/translate',
  timeout = 15.0
WHERE id = 1;
```

### Configuração do Cliente

O cliente salva configurações localmente em um arquivo JSON no diretório do usuário.

### Ajuste de Tamanho de Texto ⭐ NOVO

Personalize o comportamento do ajuste no `text_adjuster.py`:

```python
adjuster = TextAdjuster(
    max_length_ratio=1.5,      # Máximo 50% de crescimento
    enable_truncation=True,     # Trunca se exceder
    truncation_suffix="...",    # Sufixo para indicar truncamento
    enable_warnings=True        # Gera avisos
)
```

---

## 🛠️ Desenvolvimento

### Estrutura de Arquivos

```
Tradutor Master/
├── api/                          # Backend FastAPI
│   ├── main.py                  # Ponto de entrada
│   ├── config.py                # Configurações
│   ├── database.py              # Conexão com BD
│   ├── models.py                # Modelos ORM
│   ├── schemas.py               # Schemas Pydantic
│   ├── security.py              # Autenticação/JWT
│   ├── services.py              # Serviços externos
│   ├── migrate_*.py             # Scripts de migração
│   └── routers/
│       ├── translate.py         # Endpoints de tradução
│       ├── translation_tokens.py # ⭐ NOVO: Endpoints de tokens
│       ├── devices.py
│       ├── licenses.py
│       ├── auth.py
│       └── ...
│
├── src/                          # Cliente Desktop
│   ├── main.py                  # Ponto de entrada
│   ├── ui.py                    # Interface principal
│   ├── api_client.py            # Cliente HTTP
│   ├── extractor.py             # Extração de tokens
│   ├── translator.py            # Exportação de documentos
│   ├── text_adjuster.py         # ⭐ NOVO: Ajuste de tamanho
│   ├── token_viewer.py          # ⭐ NOVO: Visualização de tokens
│   ├── token_guard.py           # Proteção de tokens
│   └── utils.py                 # Utilitários
│
└── requirements.txt              # Dependências
```

### Novos Recursos Implementados ⭐

#### 1. Sistema de Ajuste de Tamanho (`text_adjuster.py`)
- Classe `TextAdjuster` para controlar crescimento de texto
- Método `adjust_text()` que retorna `TextAdjustmentResult`
- Truncamento inteligente que quebra em espaços
- Cálculo de ajuste de tamanho de fonte
- Sistema de avisos configurável

#### 2. Rastreamento de Tokens no Banco (`models.py`)
- Nova tabela `translation_tokens`
- Armazena métricas detalhadas de cada token
- Foreign key para `translation_logs`
- Índices para performance

#### 3. Endpoints de Tokens (`translation_tokens.py`)
- `GET /translations/recent` - Lista traduções com tokens
- `GET /translation/{id}/tokens` - Tokens de uma tradução
- `GET /tokens/statistics` - Estatísticas gerais
- Versões admin com `/admin/...`

#### 4. Interface de Visualização (`token_viewer.py`)
- `TokenViewerWindow` - Janela para ver tokens
- `TokenStatisticsWindow` - Janela de estatísticas
- Treeview com cores para destacar problemas
- Filtros e busca (futuro)

#### 5. Cliente API Melhorado (`api_client.py`)
- Classe `APIClient` orientada a objetos
- Métodos para novos endpoints
- Tratamento de erros consistente

### Adicionando Novas Funcionalidades

#### Backend
1. Crie modelos em `models.py`
2. Adicione schemas em `schemas.py`
3. Implemente endpoints em `routers/`
4. Registre router em `main.py`
5. Crie migração se necessário

#### Frontend
1. Adicione métodos em `api_client.py`
2. Implemente UI em novo arquivo ou `ui.py`
3. Atualize processamento em `translator.py` ou `extractor.py`

---

## 📊 Banco de Dados

### Modelo de Dados ⭐ ATUALIZADO

```sql
users
├── id (PK)
├── username (unique)
├── password_hash
├── is_superadmin
└── is_active

licenses
├── id (PK)
├── key (unique)
├── quota_period (DAILY|MONTHLY|TOTAL|NONE)
├── quota_limit
├── max_devices
├── expires_at
└── is_active

devices
├── id (PK)
├── license_id (FK)
├── device_id (unique per license)
├── usage_today
├── usage_month_count
├── total_usage
├── is_blocked
└── last_seen_at

translation_logs
├── id (PK)
├── device_id (FK)
├── original_text
├── translated_text
├── source / target
├── units
└── created_at

translation_tokens ⭐ NOVO
├── id (PK)
├── translation_log_id (FK)
├── location
├── original_text
├── translated_text
├── original_length
├── translated_length
├── was_truncated
├── size_ratio
├── units
├── warnings (JSON)
└── created_at
```

---

## 🔧 Solução de Problemas

### Problema: Texto Extrapola Limites no Documento Traduzido

**Solução Implementada ⭐:**
- Sistema de ajuste automático de tamanho
- Ative com `enable_size_adjustment=True`
- Configure `max_length_ratio` para controlar crescimento permitido
- Use `adjust_font_size=True` para reduzir fonte automaticamente

### Problema: Não Consigo Ver Detalhes das Traduções

**Solução Implementada ⭐:**
- Nova interface de visualização de tokens
- Execute migração: `python migrate_add_translation_tokens.py`
- Acesse via menu "Ver Tokens"
- Estatísticas disponíveis em "Estatísticas"

### Problema: Licença Expirada
- Verifique data de expiração no admin
- Atualize `expires_at` no banco de dados
- Ou crie nova licença

### Problema: Quota Excedida
- Verifique uso atual: `GET /usage`
- Ajuste `quota_limit` na licença
- Ou aguarde reset (diário/mensal)
- Admin pode desbloquear dispositivo

---

## 📝 Licença

Este projeto é proprietário. Todos os direitos reservados.

---

## 👥 Contribuição

Para contribuir com o projeto:
1. Faça fork do repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Envie pull request

---

## 📞 Suporte

Para suporte, entre em contato através de:
- Email: suporte@tradutormaster.com
- Issues: GitHub Issues

---

## 📈 Roadmap

### Próximas Funcionalidades
- [ ] Interface web para administração
- [ ] Exportação de relatórios de tradução
- [ ] Integração com mais serviços de tradução
- [ ] Sistema de revisão colaborativa
- [ ] App mobile
- [ ] API REST completa para integrações

### Melhorias de Qualidade
- [x] ⭐ Sistema de ajuste de tamanho de texto
- [x] ⭐ Visualização de tabela de tokens
- [x] ⭐ Estatísticas detalhadas de tradução
- [ ] Machine learning para melhorar truncamento
- [ ] Preview de documento traduzido antes de salvar
- [ ] Sugestões de melhoria de tradução

---

**Versão:** 2.0.0 ⭐ NEW
**Data:** Dezembro 2025
**Desenvolvido com:** FastAPI, Tkinter, SQLAlchemy, OpenAI
