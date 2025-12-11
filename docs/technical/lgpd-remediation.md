# Guia de Remoção de Dados Sensíveis do Histórico Git

Este guia descreve como remover permanentemente o arquivo `data/raw/exemplo.json` (e outros arquivos sensíveis) de todo o histórico do repositório. Isso é necessário para conformidade com a LGPD, pois commits antigos ainda contêm os dados originais.

> [!WARNING]
> **Atenção**: Este procedimento reescreve o histórico do Git. Isso significa que os IDs dos commits (hashes) mudarão. Se você trabalha em equipe, todos precisarão clonar o repositório novamente após este processo.

## Pré-requisitos

Você precisará da ferramenta `git-filter-repo`. Ela requer Python instalado.

```bash
pip install git-filter-repo
```

## Passo a Passo

### 1. Backup (Opcional, mas recomendado)
Faça uma cópia da pasta do seu projeto para outro local antes de começar.

### 2. Executar a Limpeza
Abra o terminal na raiz do projeto e execute o seguinte comando para remover o arquivo `data/raw/exemplo.json` de todos os commits:

```bash
git filter-repo --path data/raw/exemplo.json --invert-paths --force
```

*   `--path data/raw/exemplo.json`: Especifica o arquivo a ser processado.
*   `--invert-paths`: Diz ao git para manter tudo *exceto* o arquivo especificado.
*   `--force`: Necessário se o repositório não for um clone fresco.

### 3. Forçar o Envio para o GitHub
Como o histórico mudou, você precisará forçar o push para o repositório remoto:

```bash
git push origin --force --all
git push origin --force --tags
```

## Verificação
Após o processo, verifique se o arquivo não existe mais no histórico:

```bash
git log --all -- data/raw/exemplo.json
```
Este comando não deve retornar nada.

## Observação sobre o GitHub
Mesmo após remover do histórico, referências "órfãs" podem permanecer no cache do GitHub por algum tempo. Se os dados forem extremamente críticos, entre em contato com o suporte do GitHub para solicitar a limpeza dos caches de "dangling commits".
