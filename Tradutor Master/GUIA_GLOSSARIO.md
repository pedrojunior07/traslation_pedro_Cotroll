# 📚 Guia do Sistema de Glossário CCS JV

## Visão Geral

O sistema de glossário foi criado para garantir traduções precisas e consistentes de termos técnicos, contratuais e específicos nos documentos CCS JV de EN (inglês) para PT (português de Moçambique).

## Como Funciona

### 1. **Glossário Armazenado no Banco de Dados**

Todos os termos técnicos estão armazenados na tabela `token_dictionary` do MySQL:
- **term**: Termo original (inglês)
- **translation**: Tradução (português)
- **source_lang**: Idioma origem (en)
- **target_lang**: Idioma destino (pt)
- **category**: Categoria (termo_contratual, sigla, abreviacao, etc)
- **usage_count**: Contador de uso

### 2. **Aplicação Automática**

O glossário é aplicado automaticamente em AMBOS os motores de tradução:

#### LibreTranslate
- Tradução básica é feita pelo LibreTranslate
- **Pós-processamento** aplica o glossário, substituindo termos incorretos
- Processo inteligente que preserva capitalização (MAIÚSCULAS, Minúsculas, etc)

#### Claude AI
- Glossário é incluído no prompt do sistema
- Claude recebe instruções RIGOROSAS para aplicar o glossário com prioridade máxima
- Termos são ordenados por tamanho (maiores primeiro) para capturar frases completas

## Como Importar o Glossário

### Opção 1: Importar para MySQL (Recomendado)

```bash
python import_ccs_glossary.py
# Escolha opção 1
```

Isso irá:
1. Conectar ao banco MySQL
2. Importar ~100 termos do glossário CCS JV
3. Criar/atualizar termos na tabela `token_dictionary`

### Opção 2: Exportar para CSV

```bash
python import_ccs_glossary.py
# Escolha opção 2
```

Cria arquivo `glossario_ccs_jv_en_pt.csv` para referência ou backup.

## Termos Incluídos

### Categorias

- **termo_contratual**: Purchaser, Supplier, Subcontractor, Agreement, etc
- **sigla**: VAT→IVA, TAX ID→NUIT, HSE→SSA, etc
- **abreviacao**: Tel. No.→Tel., E-mail address→E-mail, etc
- **documento**: Purchase Order, Work Order, Letter of Acceptance, etc
- **termo_financeiro**: Invoicing→Faturação, Base Amount→Valor Base, etc
- **termo_operacional**: Job→Projeto, Vendor code→Código do Fornecedor, etc
- **termo_legal**: Applicable Law, shall be→deverá ser, etc
- **local**: Mozambique→Moçambique, Afungi Site→Obra de Afungi, etc
- **empresa**: CCS JV, TOTAL ENERGIES, etc
- **expressao_legal**: "in accordance with"→"em conformidade com", etc

### Exemplos de Traduções Corretas

| Original | Tradução Correta |
|----------|------------------|
| Purchase Order No. 31628809 | Ordem de Compra n.º 31628809 |
| TAX ID: 401015418 | NUIT: 401015418 |
| Tel. No.: +258843118753 | Tel.: +258843118753 |
| Vendor code: 172248 | Código do Fornecedor: 172248 |
| PROVISION OF MEDICAL SERVICES | PROVISÃO DOS SERVIÇOS MÉDICOS |
| Our reference: Work Order No. 31628809 | Nossa referência: Ordem de Serviço n.º 31628809 |
| Technical office: Darain S. | Gabinete técnico: Darain S. |
| Scheduled Commencement Date | Data de Início Agendada |
| Authorized Representatives | Representantes Autorizados |
| MOZAMBIQUE | MOÇAMBIQUE |

## Verificando se o Glossário Está Ativo

### No Console

Ao iniciar o Tradutor Master, você verá:

```
✓ Glossário carregado para LibreTranslate: 103 termos
```

Durante a tradução:

```
  ✓ Glossário aplicou 15 substituições
```

### No Código

```python
from src.libretranslate_client import LibreTranslateClient
from src.database import Database

# Carregar glossário do banco
db = Database()
glossary = db.get_dictionary("en", "pt")

# Criar cliente com glossário
client = LibreTranslateClient(glossary=glossary)

# Traduzir (glossário é aplicado automaticamente)
result = client.translate("Purchase Order No. 123", "en", "pt")
# Resultado: "Ordem de Compra n.º 123" (não "Ordem de Compra Não. 123")
```

## Adicionando Novos Termos

### Via Código

```python
from src.database import Database

db = Database()
db.add_dictionary_term(
    term="New Technical Term",
    translation="Novo Termo Técnico",
    source="en",
    target="pt",
    category="termo_tecnico"
)
```

### Via SQL Direto

```sql
INSERT INTO token_dictionary
(term, translation, source_lang, target_lang, category, is_active, usage_count)
VALUES ('New Term', 'Novo Termo', 'en', 'pt', 'termo_tecnico', 1, 0);
```

## Prioridade de Aplicação

O sistema aplica termos do glossário com base no comprimento (maior → menor):

1. **Frases completas**: "Scheduled Commencement Date" aplicado ANTES de "Date"
2. **Termos compostos**: "Purchase Order" aplicado ANTES de "Order"
3. **Palavras individuais**: "Vendor" aplicado por último

Isso garante que termos específicos não sejam quebrados por traduções de palavras individuais.

## Preservação de Formatação

O sistema preserva automaticamente:

- **MAIÚSCULAS**: "MOZAMBIQUE" → "MOÇAMBIQUE"
- **Capitalização**: "Purchase Order" → "Ordem de Compra"
- **minúsculas**: "vendor code" → "código do fornecedor"
- **Números**: "Order No. 123" → "Ordem n.º 123"
- **Pontuação**: "Tel.: +123" → "Tel.: +123"

## Troubleshooting

### Glossário não está sendo aplicado

1. Verificar se banco de dados está conectado:
   ```python
   from src.database import Database
   db = Database()
   print(db.test_connection())  # Deve retornar True
   ```

2. Verificar se há termos no glossário:
   ```python
   glossary = db.get_dictionary("en", "pt")
   print(f"Termos carregados: {len(glossary)}")
   ```

3. Reimportar glossário:
   ```bash
   python import_ccs_glossary.py
   ```

### Traduções ainda incorretas

1. Verificar se termo está no glossário:
   ```python
   glossary = db.get_dictionary("en", "pt")
   print("Purchase Order" in glossary)  # Deve retornar True
   ```

2. Adicionar termo manualmente se ausente
3. Verificar se LibreTranslate está retornando variação diferente do termo

### Performance lenta

O pós-processamento de glossário é rápido (<1ms por texto), mas com muitos termos (>500):
- Considere filtrar por categoria apenas relevante
- Use cache de traduções (já implementado)

## Estatísticas de Uso

Termos mais usados são rastreados automaticamente:

```python
from src.database import Database

db = Database()
terms = db.search_dictionary()

# Ordenar por uso
sorted_terms = sorted(terms, key=lambda x: x['usage_count'], reverse=True)

print("Top 10 termos mais usados:")
for term in sorted_terms[:10]:
    print(f"  {term['term']} → {term['translation']} ({term['usage_count']} usos)")
```

## Manutenção do Glossário

### Backup

```bash
python import_ccs_glossary.py
# Escolha opção 2 para exportar CSV
```

### Desativar termo sem deletar

```sql
UPDATE token_dictionary
SET is_active = 0
WHERE term = 'Old Term';
```

### Ver todos os termos por categoria

```python
from src.database import Database

db = Database()

# Por categoria
terms = db.search_dictionary(category="termo_contratual")
print(f"Termos contratuais: {len(terms)}")

for term in terms:
    print(f"  {term['term']} → {term['translation']}")
```

## Integração com Claude

Quando usar Claude AI (além de LibreTranslate), o glossário é integrado no prompt:

```
================================================================================
GLOSSÁRIO OBRIGATÓRIO - APLICAR COM PRECISÃO TOTAL
================================================================================
ATENÇÃO: Estes termos devem ser traduzidos EXATAMENTE como especificado.
Prioridade MÁXIMA sobre tradução automática.

• Purchase Order → Ordem de Compra
• Work Order → Ordem de Serviço
• TAX ID → NUIT
...
================================================================================
```

Claude recebe instruções RIGOROSAS para aplicar o glossário antes de qualquer tradução automática.

## Conclusão

O sistema de glossário garante que:

✅ Termos técnicos e contratuais sejam traduzidos corretamente
✅ Consistência entre documentos
✅ Conformidade com padrões CCS JV
✅ Preservação de formatação e estrutura
✅ Rastreamento de uso de termos

Para suporte ou dúvidas, consulte a documentação completa ou entre em contato com a equipe técnica.
