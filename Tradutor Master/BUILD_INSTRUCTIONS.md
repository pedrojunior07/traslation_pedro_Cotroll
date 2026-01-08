# Instruções para Gerar Executável Windows

## Opção 1: Executável Único (Arquivo .exe único - RECOMENDADO)

Execute o comando:
```bash
build_exe.bat
```

**Resultado:**
- Arquivo único: `dist\Tradutor Master.exe`
- Tamanho: ~150-200 MB
- Mais lento para iniciar (precisa extrair arquivos temporários)
- **Vantagem:** Fácil de distribuir (apenas 1 arquivo)

---

## Opção 2: Executável em Pasta (Mais rápido)

Execute o comando:
```bash
build_exe_folder.bat
```

**Resultado:**
- Pasta: `dist\Tradutor Master\`
- Executável: `dist\Tradutor Master\Tradutor Master.exe`
- Mais rápido para iniciar
- **Vantagem:** Melhor performance
- **Desvantagem:** Precisa distribuir a pasta inteira

---

## Requisitos

1. **Ambiente virtual ativado** (o script ativa automaticamente)
2. **PyInstaller instalado** (o script instala automaticamente)

---

## Processo de Build

O script faz automaticamente:

1. ✅ Ativa o ambiente virtual Python
2. ✅ Instala PyInstaller (se necessário)
3. ✅ Limpa builds anteriores
4. ✅ Cria executável com todas as dependências:
   - Anthropic (Claude API)
   - Requests
   - MySQL Connector
   - pdf2docx
   - python-docx
   - tkinter (interface gráfica)
   - PIL (imagens)

---

## Após o Build

### Testar o Executável:

**Opção 1 (arquivo único):**
```
dist\Tradutor Master.exe
```

**Opção 2 (pasta):**
```
dist\Tradutor Master\Tradutor Master.exe
```

### Distribuir:

**Opção 1:** Enviar apenas `Tradutor Master.exe`

**Opção 2:** Compactar a pasta `dist\Tradutor Master\` inteira em ZIP

---

## Solução de Problemas

### Erro: "Failed to execute script"
- Verifique se todas as dependências estão instaladas no venv
- Execute: `pip install -r requirements.txt`

### Executável muito grande
- Normal! Inclui Python + todas bibliotecas + dependências
- Tamanho típico: 150-200 MB

### Janela do console aparece
- Use a opção `--noconsole` (já incluída nos scripts)

### Falta ícone
- Crie um arquivo `icon.ico` na raiz do projeto
- Ou remova a linha `--icon=icon.ico` do script

---

## Configurações Avançadas

Para customizar o build, edite `build_exe.bat` ou `build_exe_folder.bat`:

- `--onefile`: Gera arquivo único
- `--onedir`: Gera pasta com executável
- `--windowed` / `--noconsole`: Sem janela de console
- `--icon=caminho.ico`: Ícone customizado
- `--add-data "origem;destino"`: Adicionar arquivos extras
- `--hidden-import=modulo`: Forçar inclusão de módulo

---

## Notas Importantes

⚠️ **O executável inclui:**
- Interpretador Python completo
- Todas as bibliotecas instaladas
- Código do tradutor
- Não inclui: Banco de dados MySQL (precisa estar rodando separadamente)

⚠️ **Configurações:**
- O executável usa o arquivo `config.json` na mesma pasta
- Banco de dados MySQL precisa estar acessível
- API keys do Claude precisam estar configuradas

⚠️ **Antivírus:**
- Alguns antivírus podem bloquear executáveis do PyInstaller
- Adicione exceção se necessário

---

## Tamanho Estimado

- **Arquivo único (.exe):** ~180 MB
- **Pasta completa:** ~220 MB (arquivos separados)

---

## Verificação

Após o build, verifique:
```
dist\
├── Tradutor Master.exe          (se usou build_exe.bat)
ou
├── Tradutor Master\             (se usou build_exe_folder.bat)
    ├── Tradutor Master.exe
    ├── _internal\
    └── ... (outros arquivos)
```

✅ Pronto para usar!
