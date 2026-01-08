# Solução: Erro "Ordinal 380 could not be located"

## 🔴 Problema

```
Ordinal 380 could not be located in the dynamic link library
C:\...\Tradutor Master.exe
```

Este erro ocorre quando há incompatibilidade de DLLs do Python no executável.

---

## ✅ Solução Rápida (RECOMENDADA)

Use o script de build seguro:

```bash
build_exe_safe.bat
```

Este script:
- ✅ Atualiza PyInstaller para última versão
- ✅ Limpa cache antigo
- ✅ Gera executável em **pasta** (mais estável que arquivo único)
- ✅ Inclui todas as DLLs necessárias corretamente

**Resultado:** `dist\Tradutor Master\Tradutor Master.exe`

---

## 🔧 Outras Soluções

### Solução 1: Usar Versão em Pasta

Em vez de `--onefile`, use `--onedir`:

```bash
build_exe_folder.bat
```

**Por que funciona?**
- Versão em pasta não compacta DLLs
- Evita conflitos de ordinal
- Mais estável

### Solução 2: Atualizar PyInstaller

```bash
.venv\Scripts\activate
pip install --upgrade pyinstaller
```

Depois execute novamente o build.

### Solução 3: Limpar Cache

```bash
# Limpar cache do PyInstaller
rmdir /s /q %LOCALAPPDATA%\pyinstaller

# Limpar builds anteriores
rmdir /s /q build
rmdir /s /q dist
```

Depois execute novamente o build.

### Solução 4: Usar --noupx

Já incluído nos scripts atualizados:

```bash
pyinstaller --noupx ...
```

O UPX pode causar problemas com DLLs.

---

## 📋 Checklist de Troubleshooting

- [ ] Usar `build_exe_safe.bat` (MELHOR OPÇÃO)
- [ ] Atualizar PyInstaller: `pip install --upgrade pyinstaller`
- [ ] Limpar cache: `rmdir /s /q %LOCALAPPDATA%\pyinstaller`
- [ ] Usar versão em pasta em vez de arquivo único
- [ ] Verificar se Python 3.8+ está instalado
- [ ] Reinstalar dependências: `pip install -r requirements.txt`

---

## 🎯 Qual Script Usar?

| Script | Tipo | Quando Usar |
|--------|------|-------------|
| `build_exe_safe.bat` | **Pasta** | ✅ **PRIMEIRO TESTE** - Mais estável |
| `build_exe_folder.bat` | Pasta | Se safe.bat não funcionar |
| `build_exe.bat` | Arquivo único | Só se pasta funcionar |

---

## ⚠️ Por Que Versão em Pasta é Melhor?

**Vantagens:**
- ✅ Mais estável (sem erros de DLL)
- ✅ Inicia mais rápido
- ✅ Fácil de debugar
- ✅ Sem problemas de ordinal

**Desvantagem:**
- ❌ Precisa distribuir pasta inteira (não só 1 arquivo)

**Solução:** Compacte em ZIP para distribuir

---

## 🚀 Comando Definitivo

Execute este comando se tudo falhar:

```bash
.venv\Scripts\activate
pip install --upgrade pyinstaller
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q %LOCALAPPDATA%\pyinstaller
build_exe_safe.bat
```

---

## 📝 Detalhes Técnicos

### O que é "Ordinal 380"?

- Ordinal = Número de uma função em uma DLL
- Erro indica que Python está procurando função que não existe
- Geralmente causado por:
  - DLLs de versões diferentes do Python
  - Compactação incorreta pelo PyInstaller
  - Cache corrompido do PyInstaller

### Por que `--onefile` causa mais problemas?

- `--onefile` compacta TUDO em um executável
- Ao executar, extrai DLLs para pasta temporária
- Pode extrair versões erradas ou corrompidas
- `--onedir` mantém DLLs separadas = mais confiável

---

## ✅ Resultado Esperado

Após usar `build_exe_safe.bat`:

```
dist\
└── Tradutor Master\
    ├── Tradutor Master.exe    ← Execute este
    ├── _internal\             ← DLLs e dependências
    │   ├── python312.dll
    │   ├── ... (muitos arquivos)
    └── config.json (se existir)
```

**Como distribuir:**
1. Compacte a pasta `Tradutor Master` em ZIP
2. Envie o ZIP
3. Usuário descompacta e executa `Tradutor Master.exe`

---

## 🆘 Ainda com Erro?

Se mesmo assim der erro:

1. Verifique versão do Python:
   ```bash
   python --version
   ```
   Deve ser 3.8 ou superior

2. Reinstale dependências:
   ```bash
   pip uninstall -y pyinstaller
   pip install pyinstaller==6.3.0
   ```

3. Execute com console para ver erros:
   - Remova `--noconsole` do script
   - Veja mensagens de erro detalhadas

4. Teste no ambiente virtual:
   ```bash
   .venv\Scripts\activate
   python src/main.py
   ```
   Se funcionar aqui, problema é no build

---

**Última atualização:** 2026-01-02
