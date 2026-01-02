# 🚀 Próximos Passos - Implementação do Glossário CCS JV

## ✅ O que foi feito

1. **Script de Importação do Glossário** ([import_ccs_glossary.py](import_ccs_glossary.py))
   - 103 termos EN→PT completos
   - Categorias: termos contratuais, siglas, abreviações, locais, empresas, expressões legais
   - Suporte para importação MySQL ou exportação CSV

2. **Sistema de Pós-Processamento** ([src/glossary_processor.py](src/glossary_processor.py))
   - Aplica glossário após tradução do LibreTranslate
   - Preserva capitalização (MAIÚSCULAS, Minúsculas, etc)
   - Ordena termos por tamanho (frases completas antes de palavras)
   - Rastreia substituições realizadas

3. **Integração com LibreTranslate** ([src/libretranslate_client.py](src/libretranslate_client.py))
   - Carrega glossário automaticamente do banco de dados
   - Aplica pós-processamento em todas as traduções
   - Mostra estatísticas de substituições no console

4. **Integração com Claude** ([src/claude_client.py](src/claude_client.py))
   - Prompt melhorado com instruções RIGOROSAS para aplicar glossário
   - Glossário formatado de forma clara com prioridade MÁXIMA
   - Exemplos práticos de aplicação

5. **Integração com UI** ([src/ui.py](src/ui.py))
   - Carregamento automático do glossário ao iniciar
   - Suporte para atualização dinâmica ao mudar idiomas

6. **Documentação Completa** ([GUIA_GLOSSARIO.md](GUIA_GLOSSARIO.md))
   - Como funciona o sistema
   - Como importar e gerenciar termos
   - Troubleshooting
   - Exemplos práticos

---

## 📋 Próximos Passos (FAÇA NESTA ORDEM)

### Passo 1: Importar Glossário para o Banco de Dados

```bash
# Executar script de importação
python import_ccs_glossary.py

# Escolher opção: 1 (Importar para MySQL)
```

**O que acontece:**
- Conecta ao MySQL (102.211.186.44:3306)
- Importa/atualiza 103 termos na tabela `token_dictionary`
- Mostra estatísticas por categoria

**Se der erro de conexão:**
1. Verificar se MySQL está rodando
2. Verificar credenciais em `src/config_manager.py`
3. Testar conexão manualmente

### Passo 2: Verificar Importação

```bash
python -c "from src.database import Database; db = Database(); print(f'Termos: {len(db.get_dictionary(\"en\", \"pt\"))}')"
```

**Resultado esperado:**
```
Termos: 103
```

### Passo 3: Testar Processador de Glossário

```bash
python src/glossary_processor.py
```

**Resultado esperado:**
- Mostra textos originais
- Aplica glossário
- Mostra substituições realizadas

### Passo 4: Iniciar Tradutor Master

```bash
python src/main.py
```

**Verificar no console:**
```
✓ Glossário carregado para LibreTranslate: 103 termos
```

**Se não aparecer:**
1. Verificar se banco de dados conectou corretamente
2. Verificar se há termos para `en→pt`
3. Revisar logs de erro

### Passo 5: Testar Tradução com Documento Real

1. Abrir Tradutor Master
2. Selecionar arquivo de teste (ex: Work Order 31628809)
3. **DESMARCAR** "Usar Claude IA" (vamos testar apenas LibreTranslate + Glossário)
4. **MARCAR** "Usar Dicionário"
5. Traduzir arquivo

**Verificar no console durante tradução:**
```
  ✓ Glossário aplicou 15 substituições
```

**No documento traduzido, procurar:**
- "Purchase Order" → "Ordem de Compra" ✅
- "TAX ID" → "NUIT" ✅
- "Tel. No." → "Tel." ✅
- "Vendor code" → "Código do Fornecedor" ✅
- "MOZAMBIQUE" → "MOÇAMBIQUE" ✅

### Passo 6: Comparar Qualidade (Antes vs Depois)

**Criar 2 traduções do mesmo documento:**

1. **SEM Glossário** (para comparação):
   - Desmarcar "Usar Dicionário"
   - Traduzir documento
   - Salvar como `documento_SEM_glossario.docx`

2. **COM Glossário**:
   - Marcar "Usar Dicionário"
   - Traduzir mesmo documento
   - Salvar como `documento_COM_glossario.docx`

**Comparar manualmente:**
- Abrir ambos os documentos
- Procurar termos técnicos
- Verificar precisão e consistência

### Passo 7: Ajustar Glossário (Se Necessário)

**Se encontrar termos incorretos:**

1. Identificar termo problemático
2. Adicionar ao glossário:

```python
from src.database import Database

db = Database()
db.add_dictionary_term(
    term="Technical Office",  # Termo original
    translation="Gabinete Técnico",  # Tradução correta
    source="en",
    target="pt",
    category="termo_operacional"
)
```

3. Reiniciar Tradutor Master para recarregar glossário
4. Traduzir documento novamente

### Passo 8: Testar com Claude (Opcional)

Se tiver API key do Claude:

1. Configurar API key na aba "🤖 Claude API"
2. **MARCAR** "Usar Claude IA"
3. **MARCAR** "Usar Dicionário"
4. Traduzir documento

**Claude receberá:**
- Glossário completo no prompt
- Instruções rigorosas para aplicá-lo
- Exemplos práticos

### Passo 9: Processar Lote de Documentos

Após confirmar qualidade em arquivo único:

1. Colocar todos os documentos em uma pasta
2. Selecionar pasta de origem e destino
3. Clicar em "⚡ Carregar e Traduzir Pasta Completa"
4. Aguardar processamento

**Monitore:**
- Barra de progresso
- Mensagens de glossário no console
- Taxa de substituições

---

## 🔍 Verificação de Qualidade

### Checklist de Termos Críticos

Após traduzir documento, verificar MANUALMENTE estes termos:

- [ ] "Purchase Order" → "Ordem de Compra"
- [ ] "Work Order" → "Ordem de Serviço"
- [ ] "TAX ID" → "NUIT"
- [ ] "Tel. No." → "Tel."
- [ ] "Vendor code" → "Código do Fornecedor"
- [ ] "Subject" → "Assunto"
- [ ] "Our reference" → "Nossa referência"
- [ ] "Agreement No." → "Acordo n.º"
- [ ] "Technical office" → "Gabinete técnico"
- [ ] "MOZAMBIQUE" → "MOÇAMBIQUE"
- [ ] "Scheduled Commencement Date" → "Data de Início Agendada"
- [ ] "Scheduled Completion Date" → "Data de Conclusão Agendada"
- [ ] "Service Acceptance Paper" → "Documento de Aceitação do Serviço"
- [ ] "Authorized Representatives" → "Representantes Autorizados"
- [ ] "upon completion" → "após a conclusão"

### Se Encontrar Erros

1. **Termo não substituído?**
   - Verificar se termo está no glossário
   - Verificar variação (plural, maiúsculas, etc)
   - Adicionar variações ao glossário se necessário

2. **Tradução incorreta?**
   - Atualizar termo no banco:
     ```sql
     UPDATE token_dictionary
     SET translation = 'Tradução Correta'
     WHERE term = 'Termo Original';
     ```

3. **Substituição indesejada?**
   - Desativar termo:
     ```sql
     UPDATE token_dictionary
     SET is_active = 0
     WHERE term = 'Termo Problemático';
     ```

---

## 📊 Monitoramento

### Ver Estatísticas de Uso

```python
from src.database import Database

db = Database()
terms = db.search_dictionary()

# Top 10 mais usados
sorted_terms = sorted(terms, key=lambda x: x['usage_count'], reverse=True)
for term in sorted_terms[:10]:
    print(f"{term['term']} ({term['usage_count']} usos)")
```

### Exportar Glossário para Backup

```bash
python import_ccs_glossary.py
# Escolher opção 2: Exportar CSV
```

Cria arquivo `glossario_ccs_jv_en_pt.csv` com todos os termos.

---

## 🆘 Troubleshooting

### Problema: Glossário não carrega

**Sintoma:** Console não mostra "✓ Glossário carregado"

**Solução:**
1. Verificar conexão MySQL:
   ```python
   from src.database import Database
   db = Database()
   print(db.test_connection())
   ```

2. Verificar se há termos:
   ```python
   glossary = db.get_dictionary("en", "pt")
   print(len(glossary))
   ```

3. Reimportar glossário:
   ```bash
   python import_ccs_glossary.py
   ```

### Problema: Substituições não aparecem

**Sintoma:** Console não mostra "✓ Glossário aplicou X substituições"

**Causa:** Termos podem não estar presentes no texto OU LibreTranslate já traduziu corretamente

**Verificação:**
```python
from src.glossary_processor import GlossaryProcessor

text = "Purchase Order No. 123"  # Texto traduzido
processor = GlossaryProcessor({"Purchase Order": "Ordem de Compra"})
result, subs = processor.apply_to_text(text)
print(f"Resultado: {result}")
print(f"Substituições: {subs}")
```

### Problema: Performance lenta

**Causa:** Muitos termos no glossário (>500)

**Solução:**
1. Filtrar por categoria relevante apenas
2. Desativar termos raramente usados
3. Usar cache de traduções (já implementado)

---

## 📝 Próximas Melhorias (Futuro)

1. **Interface gráfica para gerenciar glossário**
   - Adicionar/editar/remover termos via UI
   - Importar glossários de clientes diferentes

2. **Detecção automática de novos termos**
   - Identificar termos técnicos não traduzidos
   - Sugerir adição ao glossário

3. **Glossários específicos por projeto**
   - CCS JV
   - TOTAL ENERGIES
   - Kerry Logistics
   - etc

4. **Validação de traduções**
   - Verificar se glossário foi aplicado corretamente
   - Alertar se termos críticos não foram encontrados

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Consultar [GUIA_GLOSSARIO.md](GUIA_GLOSSARIO.md)
2. Verificar logs do console
3. Testar componentes individualmente (database, glossary_processor, etc)

---

**Última atualização:** 2026-01-02
