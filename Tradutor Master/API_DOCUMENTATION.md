# API Documentation - Tradutor Master

## Base URL
```
http://localhost:8000
```

## Authentication

A API usa JWT (JSON Web Tokens) para autenticação. Existem dois tipos de tokens:

1. **User Token**: Para administradores (acesso web)
2. **Device Token**: Para dispositivos clientes (app desktop)

### Headers
```http
Authorization: Bearer {token}
```

---

## Endpoints

### 1. Autenticação e Dispositivos

#### Registrar Dispositivo
```http
POST /devices/register
```

**Body:**
```json
{
  "license_key": "ABC123XYZ456",
  "device_id": "DEVICE001",
  "device_name": "Meu Computador" // opcional
}
```

**Response (200 OK):**
```json
{
  "device_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `403` - Licença inválida ou expirada
- `403` - Limite de dispositivos atingido
- `400` - Dados inválidos

---

### 2. Tradução

#### Tradução Simples
```http
POST /translate
Authorization: Bearer {device_token}
```

**Body:**
```json
{
  "text": "Hello World",
  "source": "en",
  "target": "pt",
  "units": 1  // opcional, padrão 1
}
```

**Response (200 OK):**
```json
{
  "translatedText": "Olá Mundo"
}
```

**Errors:**
- `403` - Licença inválida ou dispositivo bloqueado
- `403` - Quota excedida
- `400` - Parâmetros inválidos

---

#### Tradução com IA (OpenAI)
```http
POST /ai/translate
Authorization: Bearer {device_token}
```

**Body:**
```json
{
  "text": "Hello World",
  "source": "en",
  "target": "pt",
  "glossary": {  // opcional
    "World": "Mundo"
  },
  "units": 1
}
```

**Response (200 OK):**
```json
{
  "translatedText": "Olá Mundo"
}
```

**Notas:**
- Requer configuração de OpenAI na tabela `ai_config`
- Usa contexto e glossário para melhor qualidade
- Mais lento que tradução simples

---

#### Avaliar Traduzibilidade (IA)
```http
POST /ai/evaluate
Authorization: Bearer {device_token}
```

**Body:**
```json
{
  "texts": ["Hello", "NASA", "API"],
  "source": "en",
  "target": "pt"
}
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "text": "Hello",
      "translatable": true,
      "reason": "Palavra comum"
    },
    {
      "text": "NASA",
      "translatable": false,
      "reason": "Nome próprio - sigla"
    },
    {
      "text": "API",
      "translatable": false,
      "reason": "Termo técnico comum"
    }
  ]
}
```

---

#### Construir Glossário (IA)
```http
POST /ai/glossary
Authorization: Bearer {device_token}
```

**Body:**
```json
{
  "texts": ["Hello World", "API Gateway", "Database"],
  "source": "en",
  "target": "pt"
}
```

**Response (200 OK):**
```json
{
  "glossary": {
    "API": "API",
    "Gateway": "Gateway",
    "Database": "Banco de Dados"
  }
}
```

---

### 3. Tokens de Tradução ⭐ NOVO

#### Listar Traduções Recentes com Tokens
```http
GET /translations/recent?limit=10
Authorization: Bearer {device_token}
```

**Query Parameters:**
- `limit` (int): Número de traduções (1-100), padrão 10

**Response (200 OK):**
```json
[
  {
    "id": 123,
    "device_id": 1,
    "source": "en",
    "target": "pt",
    "original_text": "Hello",
    "translated_text": "Olá",
    "units": 1,
    "created_at": "2025-12-25T10:30:00",
    "tokens": [
      {
        "id": 456,
        "location": "Paragrafo 1",
        "original_text": "Hello",
        "translated_text": "Olá",
        "original_length": 5,
        "translated_length": 3,
        "was_truncated": false,
        "size_ratio": 0.6,
        "units": 1,
        "warnings": [],
        "created_at": "2025-12-25T10:30:00"
      }
    ]
  }
]
```

---

#### Obter Tokens de uma Tradução
```http
GET /translation/{translation_log_id}/tokens
Authorization: Bearer {device_token}
```

**Path Parameters:**
- `translation_log_id` (int): ID do log de tradução

**Response (200 OK):**
```json
[
  {
    "id": 456,
    "location": "Paragrafo 1",
    "original_text": "Hello World",
    "translated_text": "Olá Mundo",
    "original_length": 11,
    "translated_length": 9,
    "was_truncated": false,
    "size_ratio": 0.82,
    "units": 1,
    "warnings": [],
    "created_at": "2025-12-25T10:30:00"
  },
  {
    "id": 457,
    "location": "Tabela 1 L1C1",
    "original_text": "Very long text that was truncated",
    "translated_text": "Texto muito longo que foi trunc...",
    "original_length": 33,
    "translated_length": 35,
    "was_truncated": true,
    "size_ratio": 1.06,
    "units": 1,
    "warnings": [
      "Texto traduzido (52 chars) excede limite (35 chars) em 17 caracteres",
      "Texto truncado para 35 caracteres"
    ],
    "created_at": "2025-12-25T10:30:00"
  }
]
```

**Errors:**
- `404` - Tradução não encontrada
- `403` - Acesso negado (não pertence ao dispositivo)

---

#### Estatísticas de Tokens
```http
GET /tokens/statistics
Authorization: Bearer {device_token}
```

**Response (200 OK):**
```json
{
  "total_tokens": 1523,
  "total_original_chars": 45678,
  "total_translated_chars": 52341,
  "average_size_ratio": 1.15,
  "truncated_count": 23
}
```

**Descrição dos Campos:**
- `total_tokens`: Total de tokens traduzidos pelo dispositivo
- `total_original_chars`: Total de caracteres nos textos originais
- `total_translated_chars`: Total de caracteres nos textos traduzidos
- `average_size_ratio`: Razão média (traduzido/original)
- `truncated_count`: Quantidade de tokens que foram truncados

---

### 4. Quotas e Uso

#### Consultar Uso Atual
```http
GET /usage
Authorization: Bearer {device_token}
```

**Response (200 OK):**
```json
{
  "device_id": 1,
  "license_id": 1,
  "usage_today": 45,
  "usage_today_date": "2025-12-25",
  "usage_month_count": 320,
  "usage_month_month": 12,
  "usage_month_year": 2025,
  "total_usage": 1523,
  "quota_type": "TRANSLATIONS",
  "quota_limit": 500,
  "quota_period": "DAILY",
  "quota_remaining": 455,
  "license_active": true,
  "license_expires_at": "2026-12-25T00:00:00"
}
```

---

#### Consumir Quota Manualmente
```http
POST /quota/consume
Authorization: Bearer {device_token}
```

**Body:**
```json
{
  "units": 10
}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "usage_today": 55,
  "usage_month_count": 330,
  "total_usage": 1533
}
```

**Uso:**
- Para reservar quota antes de operações longas
- Para consumir quota de operações customizadas

---

### 5. Idiomas

#### Listar Idiomas Disponíveis
```http
GET /languages
Authorization: Bearer {device_token}
```

**Response (200 OK):**
```json
[
  {
    "code": "en",
    "name": "English"
  },
  {
    "code": "pt",
    "name": "Portuguese"
  },
  {
    "code": "es",
    "name": "Spanish"
  }
]
```

---

### 6. Admin - Dispositivos

#### Listar Dispositivos de uma Licença
```http
GET /admin/devices?license_id={license_id}
Authorization: Bearer {user_token}
```

**Query Parameters:**
- `license_id` (int, opcional): Filtrar por licença

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "license_id": 1,
    "device_id": "DEVICE001",
    "device_name": "Meu Computador",
    "is_blocked": false,
    "last_seen_at": "2025-12-25T10:30:00",
    "usage_today": 45,
    "usage_today_date": "2025-12-25",
    "usage_month_count": 320,
    "usage_month_month": 12,
    "usage_month_year": 2025,
    "total_usage": 1523,
    "created_at": "2025-01-01T00:00:00"
  }
]
```

---

#### Atualizar Dispositivo
```http
PATCH /admin/devices/{device_id}
Authorization: Bearer {user_token}
```

**Body:**
```json
{
  "is_blocked": false
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "is_blocked": false,
  ...
}
```

---

#### Uso de um Dispositivo
```http
GET /usage/device/{device_id}
Authorization: Bearer {user_token}
```

**Response:** Mesmo formato que `GET /usage`

---

#### Uso de uma Licença
```http
GET /usage/license/{license_id}
Authorization: Bearer {user_token}
```

**Response (200 OK):**
```json
[
  {
    "device_id": 1,
    "usage_today": 45,
    ...
  },
  {
    "device_id": 2,
    "usage_today": 30,
    ...
  }
]
```

---

### 7. Admin - Tokens de Tradução

#### Obter Tokens (Admin)
```http
GET /admin/translation/{translation_log_id}/tokens
Authorization: Bearer {user_token}
```

**Response:** Mesmo formato que endpoint de dispositivo, mas sem restrição de ownership

---

### 8. Health Check

#### Verificar Status da API
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

## Códigos de Status HTTP

| Código | Significado |
|--------|-------------|
| 200 | Sucesso |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Acesso negado / Quota excedida / Licença inválida |
| 404 | Recurso não encontrado |
| 422 | Erro de validação |
| 500 | Erro interno do servidor |

---

## Tipos de Quota

| Tipo | Descrição |
|------|-----------|
| DAILY | Limite diário (reseta todo dia às 00:00) |
| MONTHLY | Limite mensal (reseta no dia 1 de cada mês) |
| TOTAL | Limite total (nunca reseta) |
| NONE | Sem limite |

---

## Formato de Localização de Tokens

### DOCX
- Parágrafo: `"Paragrafo {número}"`
- Célula de tabela: `"Tabela {t} L{linha}C{coluna}"`

**Exemplos:**
- `"Paragrafo 1"` - Primeiro parágrafo
- `"Tabela 1 L2C3"` - Tabela 1, Linha 2, Coluna 3

### PPTX
- `"Slide {s} Forma {f}"`

**Exemplo:**
- `"Slide 1 Forma 3"` - Terceira forma do primeiro slide

### XLSX
- `"{sheet}!R{linha}C{coluna}"`

**Exemplo:**
- `"Sheet1!R5C3"` - Planilha Sheet1, Linha 5, Coluna 3

### TXT
- `"Linha {número}"`

**Exemplo:**
- `"Linha 10"` - Décima linha

---

## Exemplos de Uso

### Python

#### Registrar Dispositivo
```python
import requests

response = requests.post(
    "http://localhost:8000/devices/register",
    json={
        "license_key": "ABC123",
        "device_id": "MY_DEVICE",
        "device_name": "My Computer"
    }
)

token = response.json()["device_token"]
```

#### Traduzir Texto
```python
response = requests.post(
    "http://localhost:8000/translate",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "text": "Hello World",
        "source": "en",
        "target": "pt"
    }
)

translation = response.json()["translatedText"]
print(translation)  # "Olá Mundo"
```

#### Ver Tokens de Tradução
```python
response = requests.get(
    "http://localhost:8000/translations/recent?limit=5",
    headers={"Authorization": f"Bearer {token}"}
)

for translation in response.json():
    print(f"Tradução {translation['id']}:")
    for token in translation['tokens']:
        print(f"  {token['location']}: {token['original_text']} -> {token['translated_text']}")
        if token['was_truncated']:
            print(f"    ⚠️ TRUNCADO")
```

---

### JavaScript

```javascript
// Registrar dispositivo
const registerResponse = await fetch('http://localhost:8000/devices/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    license_key: 'ABC123',
    device_id: 'MY_DEVICE',
    device_name: 'My Computer'
  })
});

const { device_token } = await registerResponse.json();

// Traduzir
const translateResponse = await fetch('http://localhost:8000/translate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${device_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    text: 'Hello World',
    source: 'en',
    target: 'pt'
  })
});

const { translatedText } = await translateResponse.json();
console.log(translatedText); // "Olá Mundo"
```

---

### cURL

```bash
# Registrar dispositivo
curl -X POST http://localhost:8000/devices/register \
  -H "Content-Type: application/json" \
  -d '{"license_key":"ABC123","device_id":"MY_DEVICE"}'

# Traduzir (substitua TOKEN pelo device_token)
curl -X POST http://localhost:8000/translate \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello World","source":"en","target":"pt"}'

# Ver traduções recentes
curl -X GET "http://localhost:8000/translations/recent?limit=5" \
  -H "Authorization: Bearer TOKEN"

# Estatísticas de tokens
curl -X GET http://localhost:8000/tokens/statistics \
  -H "Authorization: Bearer TOKEN"
```

---

## Rate Limiting

A API não implementa rate limiting HTTP, mas usa o sistema de quotas baseado em licenças:

- Cada requisição de tradução consome unidades da quota
- Limite é verificado antes de processar
- Dispositivo é bloqueado automaticamente se exceder
- Quotas resetam automaticamente (DAILY/MONTHLY)

---

## Webhooks

Não implementado atualmente. Planejado para versão futura.

---

## Versionamento

A API atualmente não usa versionamento. Todas as mudanças são backwards-compatible quando possível.

---

## Swagger UI

Documentação interativa disponível em:
```
http://localhost:8000/docs
```

ReDoc disponível em:
```
http://localhost:8000/redoc
```

---

**Versão da API:** 2.0.0
**Última atualização:** Dezembro 2025
