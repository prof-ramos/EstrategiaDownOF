# 🤝 Guia de Contribuição

Obrigado por considerar contribuir com o **EstrategiaDownOF**! Este documento fornece diretrizes para contribuir com o projeto.

## 📋 Índice

- [Código de Conduta](#código-de-conduta)
- [Como Posso Contribuir?](#como-posso-contribuir)
- [Setup de Desenvolvimento](#setup-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Processo de Pull Request](#processo-de-pull-request)
- [Reportando Bugs](#reportando-bugs)
- [Sugerindo Melhorias](#sugerindo-melhorias)

## 📜 Código de Conduta

Este projeto e todos que participam dele são regidos por um código de conduta de respeito mútuo. Ao participar, espera-se que você mantenha esse padrão.

## 🚀 Como Posso Contribuir?

### 1. Reportar Bugs
Encontrou um bug? Ajude-nos criando uma issue detalhada.

### 2. Sugerir Melhorias
Tem ideias para novas funcionalidades? Abra uma issue de feature request.

### 3. Melhorar Documentação
Documentação clara é essencial. Contribuições para README, docstrings e comentários são bem-vindas.

### 4. Escrever Código
Correções de bugs, novas features e otimizações são sempre bem-vindas!

## 💻 Setup de Desenvolvimento

### Pré-requisitos

- Python 3.9 ou superior
- Git
- Google Chrome ou Microsoft Edge
- FFmpeg (opcional, para compressão de vídeos)

### Configuração do Ambiente

```bash
# 1. Fork o repositório no GitHub

# 2. Clone seu fork
git clone https://github.com/SEU-USUARIO/EstrategiaDownOF.git
cd EstrategiaDownOF

# 3. Adicione o repositório original como upstream
git remote add upstream https://github.com/prof-ramos/EstrategiaDownOF.git

# 4. Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# 5. Instale dependências de desenvolvimento
make install-dev
# OU manualmente:
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install

# 6. Verifique que tudo está funcionando
make test
```

### Estrutura do Projeto

```
EstrategiaDownOF/
├── main.py                 # Entry point principal
├── async_downloader.py     # Sistema de downloads assíncronos
├── download_database.py    # Sistema de tracking SQLite
├── compress_videos.py      # Compressão de vídeos com FFmpeg
├── ui.py                   # Interface CLI
├── test_*.py              # Testes unitários
├── requirements.txt        # Dependências de produção
├── requirements-dev.txt    # Dependências de desenvolvimento
├── pyproject.toml         # Configuração do projeto
└── README.md              # Documentação principal
```

## 📝 Padrões de Código

### Style Guide

Seguimos o [PEP 8](https://peps.python.org/pep-0008/) com algumas customizações:

- **Line length**: 120 caracteres
- **Formatação**: Usamos `black` para formatação automática
- **Linting**: Usamos `ruff` para análise estática
- **Type hints**: Obrigatórios para funções públicas
- **Docstrings**: Em português (pt-BR), formato Google

### Exemplo de Docstring

```python
def download_file(url: str, path: str, timeout: int = 120) -> bool:
    """Baixa um arquivo da URL especificada.

    Args:
        url: URL completa do arquivo a ser baixado.
        path: Caminho local onde o arquivo será salvo.
        timeout: Tempo máximo de espera em segundos (padrão: 120).

    Returns:
        True se o download foi bem-sucedido, False caso contrário.

    Raises:
        RequestException: Se houver erro de rede.
        IOError: Se houver erro ao salvar o arquivo.

    Example:
        >>> download_file("https://example.com/file.pdf", "/tmp/file.pdf")
        True
    """
    # Implementação...
```

### Comandos Úteis

```bash
# Formatar código
make format

# Executar linters
make lint

# Executar testes
make test

# Executar pre-commit hooks
make pre-commit

# Ver todos os comandos disponíveis
make help
```

## 🔄 Processo de Pull Request

### Antes de Criar o PR

1. **Crie uma branch** a partir de `main`:
   ```bash
   git checkout -b feature/nome-da-feature
   # OU
   git checkout -b fix/nome-do-bug
   ```

2. **Faça suas alterações** seguindo os padrões de código.

3. **Adicione testes** para novas funcionalidades:
   ```bash
   # Crie test_nova_feature.py
   pytest test_nova_feature.py -v
   ```

4. **Execute os testes**:
   ```bash
   make test
   ```

5. **Formate e lint o código**:
   ```bash
   make format
   make lint
   ```

6. **Atualize a documentação** se necessário.

7. **Commit suas mudanças**:
   ```bash
   git add .
   git commit -m "feat: adiciona feature X"
   ```

   Seguimos [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - Nova funcionalidade
   - `fix:` - Correção de bug
   - `docs:` - Mudanças na documentação
   - `style:` - Formatação, sem mudança de código
   - `refactor:` - Refatoração de código
   - `test:` - Adição ou correção de testes
   - `chore:` - Atualizações de build, configs, etc.

8. **Push para seu fork**:
   ```bash
   git push origin feature/nome-da-feature
   ```

### Criando o Pull Request

1. Vá para o GitHub e crie um Pull Request
2. Preencha o template de PR com:
   - Descrição clara das mudanças
   - Issues relacionadas (se houver)
   - Screenshots (para mudanças visuais)
   - Checklist de review

3. Aguarde o review e CI checks

### Checklist de PR

- [ ] Código formatado com `black`
- [ ] Linting passou (`ruff`, `mypy`)
- [ ] Testes adicionados/atualizados
- [ ] Todos os testes passando
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado (para features)
- [ ] Commits seguem Conventional Commits
- [ ] Pre-commit hooks passando

## 🐛 Reportando Bugs

Ao reportar um bug, inclua:

### Informações do Ambiente
- SO (macOS, Linux, Windows)
- Versão do Python
- Versão do projeto

### Reprodução
- Passos para reproduzir o bug
- Comportamento esperado vs. observado
- Logs/mensagens de erro

### Template de Issue

```markdown
## Descrição do Bug
[Descrição clara e concisa do bug]

## Passos para Reproduzir
1. Execute comando X
2. Observe comportamento Y
3. Erro Z ocorre

## Comportamento Esperado
[O que deveria acontecer]

## Comportamento Observado
[O que realmente acontece]

## Ambiente
- SO: macOS 14.0
- Python: 3.11.5
- Versão: 2.0.0

## Logs
```
[Cole os logs aqui]
```
```

## 💡 Sugerindo Melhorias

Para sugerir novas features:

1. **Verifique** se já não existe uma issue similar
2. **Abra uma issue** com:
   - Descrição clara da feature
   - Motivação/caso de uso
   - Exemplos de uso esperado
   - Possíveis implementações

## 🧪 Escrevendo Testes

### Estrutura de Teste

```python
import pytest
from async_downloader import DownloadIndex

def test_download_index_marks_completed():
    """Testa que DownloadIndex marca arquivos como completos corretamente."""
    # Arrange
    index = DownloadIndex("/tmp/test")
    file_path = "/tmp/test/file.pdf"

    # Act
    index.mark_completed(file_path)

    # Assert
    assert index.is_completed(file_path)
```

### Executando Testes

```bash
# Todos os testes
make test

# Testes específicos
pytest test_download_database.py::test_mark_downloaded -v

# Com coverage
make test

# Apenas testes rápidos
pytest -m "not slow"
```

## 📚 Recursos Adicionais

- [Python Style Guide (PEP 8)](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

## ❓ Dúvidas?

- Abra uma [Discussion](https://github.com/prof-ramos/EstrategiaDownOF/discussions)
- Envie um email para: [seu-email]

---

**Obrigado por contribuir! 🎉**
