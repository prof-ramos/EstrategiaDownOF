# 🔒 Política de Segurança

## Versões Suportadas

Apenas a versão mais recente recebe atualizações de segurança:

| Versão | Suportada          | Status            |
| ------ | ------------------ | ----------------- |
| 2.0.x  | :white_check_mark: | Ativa             |
| < 2.0  | :x:                | Não suportada     |

## 🚨 Reportando uma Vulnerabilidade

**Por favor, NÃO reporte vulnerabilidades de segurança através de issues públicas.**

### Processo de Reporte

1. **Envie um email para**: `prof.ramos@example.com`
2. **Inclua**:
   - Descrição detalhada da vulnerabilidade
   - Passos para reproduzir
   - Impacto potencial
   - Versão afetada
   - Sugestão de correção (se houver)

3. **Aguarde resposta** em até 48 horas

### O que Esperar

- **Confirmação** do recebimento em 48h
- **Avaliação** da vulnerabilidade em 7 dias
- **Correção** e release em até 30 dias (dependendo da severidade)
- **Crédito** no CHANGELOG e release notes (se desejar)

## 🛡️ Considerações de Segurança Conhecidas

### 1. SSL/TLS Verification Desabilitado

**Status**: ⚠️ Conhecido

**Localização**: `main.py:66`, `async_downloader.py:180`

```python
SESSION.verify = False  # Desabilita verificação SSL
```

**Razão**: Compatibilidade com certificados SSL problemáticos em algumas instituições.

**Mitigação**:
- Apenas para uso pessoal
- Não transmite dados sensíveis além de cookies de sessão
- Planejamos adicionar flag `--verify-ssl` em versão futura

**Recomendação**: Use apenas em redes confiáveis.

### 2. Armazenamento de Cookies em Texto Plano

**Status**: ⚠️ Conhecido

**Localização**: `cookies.json`

**Detalhes**: Cookies de sessão são salvos em JSON não criptografado.

**Mitigação**:
- Arquivo incluído em `.gitignore`
- Permissões de arquivo restritas (600 recomendado)
- Cookies expiram após logout/timeout do servidor

**Planejado**: Implementar criptografia de cookies em v2.1.0

**Ação do Usuário**:
```bash
# Proteger arquivo de cookies
chmod 600 cookies.json
```

### 3. Sanitização de Paths

**Status**: ✅ Parcialmente Mitigado

**Localização**: `main.py:100-106`

**Detalhes**: Nomes de arquivos são sanitizados, mas path traversal ainda é possível.

**Mitigação Atual**:
```python
def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos (mas não previne path traversal)."""
    # Remove <, >, :, ", /, \, |, ?, *, ., ,
    # Substitui espaços e - por _
```

**Planejado**: Validação adicional de paths em v2.1.0

### 4. Command Injection em FFmpeg

**Status**: ⚠️ Baixo Risco

**Localização**: `compress_videos.py`

**Detalhes**: Argumentos são passados para subprocess FFmpeg.

**Mitigação**:
- Usa lista de argumentos (não shell=True)
- Validação de paths de entrada
- Apenas aceita arquivos .mp4

**Código Seguro**:
```python
cmd = [
    'ffmpeg',
    '-i', str(video_file),  # Validado como Path
    '-c:v', codec,          # Enum de valores fixos
    # ... outros args seguros
]
subprocess.run(cmd, shell=False)  # shell=False previne injection
```

### 5. Dependências com Vulnerabilidades

**Status**: ✅ Monitorado

**Ferramentas**:
- `safety check` em CI/CD
- Dependabot habilitado
- Atualizações semanais

**Ação Automática**: PRs de atualização de segurança são criados automaticamente.

## 🔐 Boas Práticas de Uso

### Para Usuários

1. **Mantenha atualizado**:
   ```bash
   git pull origin main
   pip install -r requirements.txt --upgrade
   ```

2. **Proteja seus cookies**:
   ```bash
   chmod 600 cookies.json
   ```

3. **Use em redes confiáveis**:
   - Evite WiFi público ao fazer login
   - Prefira VPN se usar rede pública

4. **Revise permissões de arquivos**:
   ```bash
   # Downloads devem ter permissões restritas
   chmod -R 700 ~/Downloads/Cursos
   ```

5. **Delete cookies após uso**:
   ```bash
   # Se não for usar por tempo prolongado
   rm cookies.json
   ```

### Para Desenvolvedores

1. **Execute security checks**:
   ```bash
   make security
   ```

2. **Use pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Revise dependências**:
   ```bash
   safety check
   pip-audit  # Alternativa moderna
   ```

4. **Não commite segredos**:
   ```bash
   # Já configurado em .pre-commit-config.yaml
   detect-secrets scan
   ```

## 📋 Checklist de Segurança para PRs

Antes de submeter um PR que toca código sensível:

- [ ] Validação de inputs do usuário
- [ ] Sanitização de paths/filenames
- [ ] Não usa `shell=True` em subprocess
- [ ] Não loga informações sensíveis
- [ ] Trata exceções apropriadamente
- [ ] Atualiza dependências se necessário
- [ ] Executa `make security` sem warnings críticos
- [ ] Documenta considerações de segurança no PR

## 🔍 Scan de Segurança Automatizado

O projeto usa as seguintes ferramentas em CI:

| Ferramenta | Propósito | Frequência |
|------------|-----------|------------|
| Bandit | SAST Python | Todo PR |
| Safety | Vuln. Dependencies | Todo PR |
| Trivy | Container Scanning | Todo PR |
| CodeQL | Análise semântica | Semanal |
| Dependabot | Dep. Updates | Diária |

## 🚀 Roadmap de Segurança

### v2.1.0 (Próxima Release)

- [ ] Criptografia de cookies (AES-256)
- [ ] Flag `--verify-ssl` para validação SSL
- [ ] Validação rigorosa de path traversal
- [ ] Rate limiting configurável
- [ ] Audit log de downloads

### v2.2.0 (Futuro)

- [ ] Autenticação 2FA
- [ ] Vault de credenciais (keyring)
- [ ] Assinatura digital de releases
- [ ] SBOM (Software Bill of Materials)

## 📞 Contato

- **Email de Segurança**: prof.ramos@example.com
- **PGP Key**: [Link para chave pública]
- **Resposta**: 48 horas para confirmação

## 📜 Disclosure Policy

Seguimos **Responsible Disclosure**:

1. Reporte privado → Confirmação (48h)
2. Correção desenvolvida → Review (7 dias)
3. Release de segurança → Público (30 dias)
4. Disclosure completo → CVE (se aplicável)

**Créditos**: Pesquisadores de segurança são creditados (com permissão) em:
- CHANGELOG.md
- Release notes
- Security advisories

---

**Última atualização**: 2026-01-01
