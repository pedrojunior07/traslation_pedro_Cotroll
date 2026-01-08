# 🔧 Como Mudar o Modelo Claude

## 🚨 Problema: JSON com Erros

Se você está vendo muitos erros de JSON como:

```json
{
  "location": "T467",
  "translation": ""  ← VAZIO!
}
```

Ou outros erros repetidos, o modelo **Haiku 3.5** pode estar gerando JSONs malformados.

## ✅ Solução: Mudar para Sonnet 3.5

O **Sonnet 3.5** é mais preciso e gera menos erros de JSON.

### Como Mudar

**Opção 1: Usar o script automático** (MAIS FÁCIL)

1. Feche o Tradutor Master se estiver aberto
2. Execute: `MUDAR_MODELO.bat`
3. Escolha a opção **1** (Sonnet 3.5)
4. Confirme com **s**
5. Reinicie o Tradutor Master

**Opção 2: Manualmente**

1. Feche o Tradutor Master
2. Abra o arquivo: `C:\Users\{seu_usuario}\.tradutor_master\config.json`
3. Mude a linha:
   ```json
   "claude_model": "claude-3-5-haiku-20241022"
   ```
   Para:
   ```json
   "claude_model": "claude-3-5-sonnet-20241022"
   ```
4. Salve o arquivo
5. Reinicie o Tradutor Master

## 📊 Comparação de Modelos

| Modelo | Precisão | Velocidade | Custo | Erros JSON |
|--------|----------|------------|-------|------------|
| **Sonnet 3.5** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Médio | Raros |
| **Haiku 3.5** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Baixo | Frequentes |
| **Opus 4** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Alto | Muito raros |

### Recomendação

Para tradução de documentos contratuais/técnicos: **USE SONNET 3.5**

- ✅ Melhor equilíbrio entre precisão e velocidade
- ✅ Poucos erros de JSON
- ✅ Custo razoável
- ✅ Tradução de alta qualidade

## 🛠️ Correções Automáticas Implementadas

Mesmo com erros, o sistema agora tem **9 tipos de auto-correção**:

1. ✅ Aspas triplas escapadas erradas
2. ✅ Aspas duplas escapadas duplicadas
3. ✅ Aspas simples ao invés de duplas
4. ✅ Vírgulas faltantes entre objetos
5. ✅ Ponto e vírgula antes de chave
6. ✅ Caracteres de controle inválidos
7. ✅ Caracteres extras após aspas
8. ✅ Aspas não escapadas dentro de valores
9. ✅ **NOVO**: Traduções vazias removidas automaticamente

### Exemplo da Correção Automática

Se o Claude retornar:
```json
{
  "location": "T467",
  "translation": ""
}
```

O sistema automaticamente:
1. Remove a tradução vazia
2. Marca como faltante: `[ERRO: Tradução faltando para T467]`
3. Continua com o resto do documento

## 📝 Logs de Correção

Quando houver correção automática, você verá:

```
⚠️ 1 traduções vazias removidas automaticamente
✅ JSON corrigido automaticamente: aspas triplas → aspas simples
```

## 🎯 Como Usar o Script

```bash
# Windows
MUDAR_MODELO.bat

# Ou diretamente
.venv\Scripts\python.exe mudar_modelo_claude.py
```

### Saída do Script

```
================================================================================
🔧 MUDAR MODELO CLAUDE - Tradutor Master
================================================================================

📌 Modelo atual: claude-3-5-haiku-20241022

Modelos disponíveis:

1. Claude 3.5 Sonnet (Mais Preciso)
   ID: claude-3-5-sonnet-20241022
   Modelo mais preciso, melhor para tradução. Menos erros JSON.

2. Claude 3.5 Haiku (Mais Rápido)
   ID: claude-3-5-haiku-20241022
   Modelo mais rápido e barato, mas pode ter mais erros JSON.

3. Claude Opus 4 (Mais Inteligente)
   ID: claude-opus-4-20250514
   Modelo mais avançado, excelente precisão, mas mais caro.

Digite o número do modelo que deseja usar (ou 'q' para sair): 1

🔄 Mudando de:
   claude-3-5-haiku-20241022
   ↓
   Claude 3.5 Sonnet (Mais Preciso) (claude-3-5-sonnet-20241022)

Confirmar mudança? (s/n): s
✅ Modelo alterado com sucesso!
   Reinicie o Tradutor Master para usar o novo modelo.
```

## ⚠️ IMPORTANTE

Depois de mudar o modelo, você DEVE **reiniciar o Tradutor Master** para que a mudança tenha efeito!

---

**Resumo**: Se estiver cansado de erros JSON, mude para **Sonnet 3.5**! 🎉
