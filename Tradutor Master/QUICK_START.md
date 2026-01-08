# Guia Rápido - Tradutor Master

## 🚀 Para Gerar o Executável

Execute um destes comandos:

### Opção 1: Arquivo Único (Recomendado)
```bash
build_exe.bat
```
Gera: `dist\Tradutor Master.exe` (arquivo único)

### Opção 2: Pasta (Mais Rápido)
```bash
build_exe_folder.bat
```
Gera: `dist\Tradutor Master\Tradutor Master.exe` (pasta com arquivos)

---

## ⚡ Depois do Build

1. **Executar:**
   - Clique duas vezes em `Tradutor Master.exe`

2. **Distribuir:**
   - Envie o arquivo `.exe` (Opção 1)
   - Ou compacte a pasta inteira em ZIP (Opção 2)

---

## ⚙️ Configuração Inicial

1. **MySQL** deve estar rodando (porta 3306)
2. Configure em **Configurações > Definições**:
   - Host MySQL: `102.211.186.44` (ou localhost)
   - Banco: `tradutor_db`
   - API Key do Claude (se usar IA)

3. **Importar Glossário** (opcional):
   ```bash
   .venv\Scripts\python.exe import_ccs_glossary.py
   ```

---

## 📝 Uso Básico

### Traduzir Arquivos:

1. **Aba Tradução**
2. Selecione pasta origem
3. Selecione pasta destino  
4. Escolha idiomas (EN → PT)
5. Clique em **"Traduzir Todos"**

### Progresso:

1. **Janela de Conversão PDF** aparece primeiro
   - Mostra conversão de PDF → tokens
   - Log completo do processo

2. **Janela de Tradução** aparece depois
   - Lado esquerdo: Progresso geral
   - Lado direito: Token sendo traduzido em tempo real

3. **Exportação Automática**
   - Arquivos salvos na pasta destino
   - Formato: `.docx` (sempre)

---

## ✅ Recursos Implementados

- ✅ Tradução com LibreTranslate
- ✅ Tradução com Claude AI
- ✅ Glossário EN→PT (103+ termos CCS JV)
- ✅ Correções PT→PT (40+ regras)
- ✅ Pós-processamento com regex (19 regras)
- ✅ Conversão PDF com progresso visual
- ✅ Tradução batch com visualização token por token
- ✅ Pausa/retomada de tradução
- ✅ Exportação automática

---

## 🔧 Solução de Problemas

### Erro ao executar:
- Verifique MySQL está rodando
- Verifique `config.json` existe

### Janela trava ao converter PDF:
- Resolvido! Agora mostra janela de progresso

### Glossário não funciona:
- Execute `import_ccs_glossary.py` primeiro
- Reinicie o tradutor

---

## 📊 Estrutura de Arquivos

```
Tradutor Master/
├── src/                          # Código fonte
├── dist/                         # Executável gerado aqui
├── build_exe.bat                 # Gerar .exe único
├── build_exe_folder.bat          # Gerar pasta
├── import_ccs_glossary.py        # Importar glossário
├── config.json                   # Configurações
└── requirements.txt              # Dependências Python
```

---

## 💡 Dicas

1. **Primeira vez:** Use `build_exe_folder.bat` (mais rápido para testar)
2. **Distribuição:** Use `build_exe.bat` (arquivo único)
3. **Glossário:** Sempre importe antes de usar
4. **Performance:** Claude é mais preciso, LibreTranslate é mais rápido

---

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique `BUILD_INSTRUCTIONS.md` para detalhes do build
2. Verifique logs no console (se houver)
3. Confira configurações do MySQL

---

**Versão:** 2.0  
**Última atualização:** 2026-01-02
