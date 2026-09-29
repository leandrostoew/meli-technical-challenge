# Challenge 01 — Análise de tráfego

Aplicação de linha de comando que captura pacotes IPv4 de uma interface, grava os metadados em SQLite e imprime as estatísticas no terminal. O mesmo comando roda no host e no container.

Fonte: [`../../docs/desafio-mercado-livre.pdf`](../../docs/desafio-mercado-livre.pdf). As escolhas que o PDF não fixa estão em [`../../docs/decisoes/README.md`](../../docs/decisoes/README.md).

## Objetivo

**Requisito do PDF.** Capturar pacotes de uma interface especificada, guardar IP de origem, IP de destino, protocolo e tamanho, persistir em banco e exibir o total, a quantidade por protocolo e o top 5 de origem e de destino.

A linguagem é Python. O script também roda em Docker.

## Arquitetura

```text
interface informada na CLI
→ Scapy sniff (promisc=False)
→ ingest
   → IPv4 gravado em SQLite
   → quadro sem IPv4 só incrementa ignored_non_ip
→ analyzer
→ relatório no terminal
```

O código está em `src/traffic_analyzer/`. O fluxo completo está em [`../../docs/arquitetura.md`](../../docs/arquitetura.md).

## Pré-requisitos

- Python 3.12
- Docker e Docker Compose, para a execução em container
- Permissão de socket bruto na captura. A aplicação não eleva privilégio e não chama `sudo`

Na validação manual em Linux, essa permissão foi concedida ao processo por fora da aplicação. Sem ela, a CLI termina com código 3.

## Instalação

A partir da raiz do repositório:

```bash
cd challenges/01-analise-de-trafego
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` fixa Scapy 2.7.0 e pytest 9.1.1. A imagem Docker instala só o Scapy. O pytest fica no ambiente do host. O diretório `.venv` não entra no Git.

## Testes

**Decisão nossa.** O PDF não pede testes.

```bash
cd challenges/01-analise-de-trafego
.venv/bin/python -m pytest
```

A suíte cobre parser, repositório, ingestão, analyzer, sniffer simulado, CLI, relatório e o texto do Dockerfile e do compose. Nenhum teste abre interface de rede nem constrói a imagem.

## CLI

O lançador é `traffic-analyzer`. A interface é sempre o argumento `--interface`. Troque `NOME` pelo nome da interface dessa máquina. Na validação em Linux Mint o nome usado foi `wlp3s0`. Esse nome não é padrão do programa.

`--count` é o máximo de pacotes IPv4 armazenados. `--duration` é a duração em segundos. Os dois juntos são recusados. Sem nenhum dos dois, a captura segue até Ctrl+C.

O padrão de `--db` é `data/traffic.db`. O diretório do arquivo precisa existir. A aplicação não cria essa pasta. `data/` já vem no repositório.

```bash
cd challenges/01-analise-de-trafego
.venv/bin/python traffic-analyzer capture --interface NOME --count 10
.venv/bin/python traffic-analyzer capture --interface NOME --duration 10
.venv/bin/python traffic-analyzer capture --interface NOME
.venv/bin/python traffic-analyzer report
```

`report` reexibe a sessão mais recente do banco. `--capture-id` escolhe outra sessão. `--db` aponta outro arquivo, no `capture` e no `report`.

Ctrl+C encerra a leitura, grava `ended_at`, conserva os pacotes já armazenados e mostra o relatório do que foi gravado. O código de saída é 0.

### Códigos de saída

| Código | Situação |
| --- | --- |
| 0 | Captura concluída, ou interrompida com Ctrl+C, com relatório |
| 1 | Falha inesperada de captura |
| 2 | Argumento inválido ou interface inexistente |
| 3 | Sem permissão para capturar |
| 4 | Erro de persistência |

No código 3 a mensagem diz que a captura requer permissão adequada e que a aplicação não eleva privilégio.

## Docker

**Requisito do PDF:** o script roda em Docker.

**Decisão nossa:** a imagem usa a CLI como entrypoint. O compose usa a rede do host, acrescenta `CAP_NET_RAW` e `CAP_NET_ADMIN`, deixa `privileged: false` e monta `./data` em `/app/data`. Não há `sudo` na imagem. A interface continua só em `--interface`. `promisc=False` permanece no sniffer.

```bash
cd challenges/01-analise-de-trafego
docker compose build
docker compose run --rm traffic-analyzer capture --interface NOME --count 10
docker compose run --rm traffic-analyzer capture --interface NOME --duration 10
docker compose run --rm traffic-analyzer report
```

O banco padrão no host é `challenges/01-analise-de-trafego/data/traffic.db`. Dentro do container o mesmo arquivo é `/app/data/traffic.db`.

A configuração validada usa as duas capabilities. Sem `CAP_NET_RAW` e `CAP_NET_ADMIN`, a CLI termina com código 3. O processo do container é o root da imagem, porque essas capabilities valem para ele. O arquivo SQLite criado por esse processo fica com o dono desse usuário.

## Decisões

Estas escolhas não estão escritas no PDF. O relatório deixa a primeira explícita.

- Só IPv4 entra nas estatísticas e na tabela `packets`. ARP e IPv6 incrementam `ignored_non_ip`. O total exibido é o de pacotes IPv4 armazenados.
- `size_bytes` é o comprimento da camada IPv4 lida.
- Tráfego, no top 5, é a soma de `size_bytes`. Origem agrupa `src_ip`. Destino agrupa `dst_ip`.
- `promisc=False`. A captura não pede o modo promíscuo.

O schema, com as tabelas `captures` e `packets`, está em `src/traffic_analyzer/persistence/repository.py`.
