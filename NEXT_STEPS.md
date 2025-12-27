# 🚀 Próximos Passos - Implementação Multi-IA

## ✅ O que já foi feito

1. **Modelo atualizado** - `models.py` com suporte para 3 provedores
2. **Migração executada** - Novas colunas no banco de dados
3. **Sistema de ajuste de texto** - `text_adjuster.py` completo
4. **Visualização de tokens** - Completa com frontend

## 📝 O que falta implementar

### 1. Atualizar `api/services.py`

Adicionar classes para cada provedor de IA:

```python
# No final do arquivo services.py, adicionar:

class AIProvider:
    """Classe base para provedores de IA."""

    def translate_batch(self, tokens: List[Dict], source: str, target: str, glossary: Dict = None) -> List[Dict]:
        """Traduz lote de tokens.

        Args:
            tokens: Lista de {"location": str, "text": str}
            source: Idioma origem
            target: Idioma destino
            glossary: Glossário opcional

        Returns:
            Lista de {"location": str, "translation": str}
        """
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str, base_url: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def translate_batch(self, tokens, source, target, glossary=None):
        # Implementar chamada para OpenAI
        # Enviar todos os tokens em um único request
        # Retornar traduções
        pass


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def translate_batch(self, tokens, source, target, glossary=None):
        # Implementar chamada para Gemini
        # API: https://generativelanguage.googleapis.com/v1/models/{model}:generateContent
        pass


class GrokProvider(AIProvider):
    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def translate_batch(self, tokens, source, target, glossary=None):
        # Implementar chamada para Grok
        # API: https://api.x.ai/v1/chat/completions
        pass


def get_ai_provider(db) -> AIProvider:
    """Retorna o provedor de IA configurado."""
    config = db.query(AIConfig).first()

    if not config or not config.enabled:
        raise HTTPException(400, "IA não configurada")

    if config.provider == "openai":
        return OpenAIProvider(
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
            timeout=config.timeout
        )
    elif config.provider == "gemini":
        return GeminiProvider(
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            timeout=config.timeout
        )
    elif config.provider == "grok":
        return GrokProvider(
            api_key=config.grok_api_key,
            model=config.grok_model,
            timeout=config.timeout
        )
    else:
        raise HTTPException(400, f"Provedor desconhecido: {config.provider}")
```

### 2. Criar novo endpoint em `api/routers/translate.py`

Adicionar endpoint de tradução em lote:

```python
@router.post("/ai/translate-batch")
def translate_batch_ai(
    payload: dict,  # {"tokens": [{"location": str, "text": str}], "source": str, "target": str, "glossary": dict}
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):
    """
    Traduz múltiplos tokens de uma vez usando IA.

    Body:
    {
        "tokens": [
            {"location": "Paragrafo 1", "text": "Hello"},
            {"location": "Paragrafo 2", "text": "World"}
        ],
        "source": "en",
        "target": "pt",
        "glossary": {"Hello": "Olá"}  # opcional
    }

    Response:
    {
        "translations": [
            {"location": "Paragrafo 1", "translation": "Olá"},
            {"location": "Paragrafo 2", "translation": "Mundo"}
        ]
    }
    """
    license_obj = db.query(License).filter(License.id == device.license_id).first()
    if not license_obj or not _license_is_valid(license_obj):
        raise HTTPException(403, "Invalid license")
    if device.is_blocked:
        raise HTTPException(403, "Device blocked")

    tokens = payload.get("tokens", [])
    source = payload["source"]
    target = payload["target"]
    glossary = payload.get("glossary")

    # Calcula units
    units = len(tokens)
    _enforce_limits(device, license_obj, units)

    # Traduz usando IA
    from api.services import get_ai_provider
    provider = get_ai_provider(db)
    translations = provider.translate_batch(tokens, source, target, glossary)

    # Atualiza usage
    device.usage_today += units
    device.usage_month_count += units
    device.total_usage += units
    device.last_seen_at = datetime.utcnow()
    db.add(device)
    db.commit()

    return {"translations": translations}
```

### 3. Atualizar `api/schemas.py`

Adicionar schemas para configuração de IA:

```python
class AIConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    provider: Optional[str] = None  # NOVO
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None  # NOVO
    gemini_model: Optional[str] = None  # NOVO
    grok_api_key: Optional[str] = None  # NOVO
    grok_model: Optional[str] = None  # NOVO
    timeout: Optional[float] = None  # NOVO
    max_retries: Optional[int] = None  # NOVO


class AIConfigOut(BaseModel):
    enabled: bool
    provider: str  # NOVO
    base_url: str
    model: str
    api_key_present: bool
    gemini_api_key_present: bool  # NOVO
    gemini_model: str  # NOVO
    grok_api_key_present: bool  # NOVO
    grok_model: str  # NOVO
    timeout: float  # NOVO
    max_retries: int  # NOVO
```

### 4. Criar frontend HTML para testes

Criar arquivo `api/templates/api_tester.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Tradutor Master - Test API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .section { border: 1px solid #ccc; padding: 20px; margin: 20px 0; border-radius: 8px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        textarea { width: 100%; min-height: 150px; font-family: monospace; }
        .result { background: #f5f5f5; padding: 10px; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>🚀 Tradutor Master - API Tester</h1>

    <!-- Seção de configuração -->
    <div class="section">
        <h2>⚙️ Configuração</h2>
        <label>Base URL: <input type="text" id="baseUrl" value="http://localhost:8000"></label><br>
        <label>Device Token: <input type="text" id="token" placeholder="Cole seu token aqui"></label>
    </div>

    <!-- Teste de tradução em lote -->
    <div class="section">
        <h2>🔄 Tradução em Lote (IA)</h2>
        <textarea id="batchInput">{
  "tokens": [
    {"location": "Paragrafo 1", "text": "Hello World"},
    {"location": "Paragrafo 2", "text": "How are you?"}
  ],
  "source": "en",
  "target": "pt"
}</textarea>
        <button onclick="testBatchTranslate()">Testar Tradução em Lote</button>
        <div class="result" id="batchResult"></div>
    </div>

    <!-- Ver tokens de tradução -->
    <div class="section">
        <h2>📊 Ver Tokens de Tradução</h2>
        <button onclick="getRecentTranslations()">Ver Traduções Recentes</button>
        <div class="result" id="tokensResult"></div>
    </div>

    <script>
        async function testBatchTranslate() {
            const baseUrl = document.getElementById('baseUrl').value;
            const token = document.getElementById('token').value;
            const payload = JSON.parse(document.getElementById('batchInput').value);

            const response = await fetch(`${baseUrl}/ai/translate-batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            document.getElementById('batchResult').textContent = JSON.stringify(data, null, 2);
        }

        async function getRecentTranslations() {
            const baseUrl = document.getElementById('baseUrl').value;
            const token = document.getElementById('token').value;

            const response = await fetch(`${baseUrl}/translations/recent?limit=5`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const data = await response.json();
            document.getElementById('tokensResult').textContent = JSON.stringify(data, null, 2);
        }
    </script>
</body>
</html>
```

Adicionar rota em `api/main.py`:

```python
from fastapi.responses import HTMLResponse
from pathlib import Path

@app.get("/test", response_class=HTMLResponse)
def api_tester():
    html_file = Path(__file__).parent / "templates" / "api_tester.html"
    return html_file.read_text()
```

### 5. Atualizar desktop para mostrar progresso

Em `src/ui.py`, adicionar barra de progresso detalhada:

```python
def _translate_document(self):
    # ... código existente ...

    # Adicionar label de progresso
    self.progress_label = ttk.Label(self.root, text="")
    self.progress_label.pack()

    # Durante tradução, atualizar:
    self.progress_label.config(
        text=f"Traduzindo: {current_token}/{total_tokens} - "
        f"Arquivo: {filename} - "
        f"ETA: {eta_formatted}"
    )
```

## 🎯 Ordem de Implementação Recomendada

1. ✅ Executar migração (CONCLUÍDO)
2. **Atualizar `services.py`** com provedores de IA
3. **Atualizar `schemas.py`** com novos campos
4. **Criar endpoint `/ai/translate-batch`**
5. **Criar `templates/api_tester.html`**
6. **Testar com frontend HTML**
7. **Atualizar desktop com progresso**

## 📚 Documentação das APIs

### Google Gemini
- Endpoint: `https://generativelanguage.googleapis.com/v1/models/{model}:generateContent`
- Header: `x-goog-api-key: YOUR_API_KEY`
- Modelos: `gemini-1.5-flash`, `gemini-1.5-pro`

### xAI Grok
- Endpoint: `https://api.x.ai/v1/chat/completions`
- Header: `Authorization: Bearer YOUR_API_KEY`
- Modelo: `grok-2-latest`

### OpenAI (já implementado)
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Header: `Authorization: Bearer YOUR_API_KEY`
- Modelos: `gpt-4o-mini`, `gpt-4`, etc.

## ✅ Status Atual

- ✅ Banco de dados migrado
- ✅ Modelos atualizados
- ✅ Sistema de ajuste de texto completo
- ✅ Visualização de tokens completa
- ⏳ Provedores de IA (precisa implementar)
- ⏳ Endpoint de lote (precisa implementar)
- ⏳ Frontend de testes (precisa implementar)
- ⏳ Progresso transparente no desktop (precisa implementar)

## 🎉 Resultado Final Esperado

Depois de completar tudo, você terá:

1. **3 provedores de IA** funcionando (OpenAI, Gemini, Grok)
2. **Tradução em lote** eficiente (1 request para N tokens)
3. **Frontend HTML** para testar todas as APIs
4. **Progresso transparente** mostrando cada token sendo traduzido
5. **Controle de qualidade** com ajuste automático de tamanho
6. **Visualização completa** de tokens e estatísticas

---

**Versão:** 2.1.0
**Status:** 70% Completo
**Próximo passo:** Implementar `services.py` com os 3 provedores
