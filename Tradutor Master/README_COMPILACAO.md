# 📦 Guia de Compilação - Tradutor Master

## 🎯 Opções de Compilação

Existem **2 scripts** disponíveis para gerar o executável:

### 1. `gerar_exe.bat` - Arquivo Único
- ✅ **Vantagem**: Um único arquivo `.exe`
- ⚠️ **Desvantagem**: Mais lento para iniciar (descompacta na memória)
- 📦 **Tamanho**: ~150-200 MB
- 🎯 **Uso**: Distribuição simples

### 2. `gerar_exe_completo.bat` - Pasta com Dependências
- ✅ **Vantagem**: Inicia mais rápido
- ✅ **Vantagem**: Mais fácil de atualizar
- ⚠️ **Desvantagem**: Precisa distribuir pasta inteira
- 📦 **Tamanho**: ~200-250 MB (pasta)
- 🎯 **Uso**: Instalação local ou rede

---

## 🚀 Como Compilar

### Passo 1: Preparar Ambiente
```bash
cd "Tradutor Master"
```

### Passo 2: Escolher Script
**Opção A - Arquivo Único:**
```bash
gerar_exe.bat
```

**Opção B - Pasta Completa:**
```bash
gerar_exe_completo.bat
```

### Passo 3: Aguardar
- ⏱️ Tempo estimado: 3-5 minutos
- 📊 O script mostra o progresso

### Passo 4: Resultado
**Arquivo único:**
- 📁 Localização: `dist\TradutorMaster.exe`

**Pasta completa:**
- 📁 Localização: `dist\TradutorMaster\`
- 🔗 Atalho criado: `TradutorMaster.lnk`

---

## 📋 Requisitos

### Obrigatórios
- ✅ Python 3.10+
- ✅ Ambiente virtual (`.venv`) configurado
- ✅ Todas as dependências instaladas (`requirements.txt`)

### Verificar Instalação
```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Verificar módulos
pip list
```

---

## 🐛 Solução de Problemas

### Erro: "Ambiente virtual não encontrado"
**Solução:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Erro: "PyInstaller não encontrado"
**Solução:**
```bash
.venv\Scripts\activate
pip install pyinstaller
```

### Erro: "Módulo não encontrado ao executar .exe"
**Solução:**
Adicione o módulo faltante no script `.bat`:
```batch
--hidden-import=nome_do_modulo ^
```

### Executável muito grande
**Solução:**
Use `gerar_exe_completo.bat` e depois:
```bash
# Comprimir pasta dist\TradutorMaster em ZIP
# Distribuir o ZIP
```

---

## 📦 Distribuição

### Arquivo Único
1. Copie `dist\TradutorMaster.exe`
2. Distribua o arquivo
3. Usuário executa diretamente

### Pasta Completa
1. Copie toda a pasta `dist\TradutorMaster`
2. Distribua a pasta (pode comprimir em ZIP)
3. Usuário descompacta e executa `TradutorMaster.exe`

---

## ⚙️ Personalização

### Adicionar Ícone
1. Crie/obtenha um arquivo `icon.ico`
2. Coloque na pasta raiz
3. O script usará automaticamente

### Incluir Arquivos Extras
Edite o script `.bat` e adicione:
```batch
--add-data "caminho/origem;caminho/destino" ^
```

Exemplo:
```batch
--add-data "config.json;." ^
--add-data "assets;assets" ^
```

### Excluir Módulos Desnecessários
Se algum módulo não for usado, remova do script:
```batch
REM Remova linhas como:
--hidden-import=modulo_nao_usado ^
```

---

## 📊 Comparação de Métodos

| Característica | Arquivo Único | Pasta Completa |
|----------------|---------------|----------------|
| Tamanho | ~150-200 MB | ~200-250 MB |
| Velocidade de Início | Lento (3-5s) | Rápido (1-2s) |
| Distribuição | Simples | Requer pasta |
| Atualização | Substituir .exe | Substituir arquivos |
| Debugging | Difícil | Mais fácil |

---

## 🔧 Comandos Úteis

### Testar Executável
```bash
# Arquivo único
dist\TradutorMaster.exe

# Pasta completa
dist\TradutorMaster\TradutorMaster.exe
```

### Ver Logs de Erro
```bash
# Executar em modo console (para debug)
pyinstaller --onefile --console src/main.py
```

### Recompilar Rápido
```bash
# Usar spec file existente (mais rápido)
pyinstaller TradutorMaster.spec
```

---

## ✅ Checklist de Compilação

Antes de compilar, verifique:

- [ ] Ambiente virtual ativado
- [ ] Todas as dependências instaladas
- [ ] Código testado e funcionando
- [ ] Ícone preparado (opcional)
- [ ] Espaço em disco suficiente (~500 MB)
- [ ] Antivírus desativado temporariamente (pode bloquear PyInstaller)

---

## 💡 Dicas

1. **Primeira compilação**: Use `gerar_exe_completo.bat` para testar
2. **Distribuição final**: Use `gerar_exe.bat` para arquivo único
3. **Desenvolvimento**: Mantenha pasta `dist` para testes rápidos
4. **Produção**: Sempre teste o .exe em máquina limpa antes de distribuir

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs durante compilação
2. Teste em modo console (`--console`)
3. Verifique se todos os módulos estão no `requirements.txt`
4. Consulte documentação do PyInstaller: https://pyinstaller.org
