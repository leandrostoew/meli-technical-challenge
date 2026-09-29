# Challenge 01 — Análise de tráfego

A aplicação captura pacotes IPv4, grava em SQLite e exibe o relatório no terminal. O mesmo comando roda no host e em Docker. Este README separa requisito do PDF, decisão nossa e o que já está implementado.

Fonte: [`../../docs/desafio-mercado-livre.pdf`](../../docs/desafio-mercado-livre.pdf).

## Objetivo

**Requisito do PDF.** Desenvolver uma aplicação que capture pacotes de uma interface de rede especificada, armazene esses pacotes e exiba estatísticas básicas do tráfego.

## Requisitos

**Requisito do PDF.**

Captura:

- capturar pacotes de uma interface de rede especificada;
- usar uma biblioteca ou ferramenta adequada (o PDF cita Scapy em Python como exemplo);
- guardar de cada pacote o IP de origem, o IP de destino, o protocolo e o tamanho.

Estatísticas:

- número total de pacotes capturados;
- número de pacotes por protocolo (o PDF cita TCP e UDP como exemplo);
- top 5 IPs de origem com mais tráfego;
- top 5 IPs de destino com mais tráfego.

Armazenamento:

- persistir os pacotes capturados em um banco de dados.

Execução:

- o script deverá ser executado em Docker.

Entrega e avaliação:

- a aplicação captura pacotes e exibe as estatísticas;
- a documentação explica como configurar, executar e usar;
- as escolhas ficam justificadas (o PDF cita schema da base e informações do script como exemplos);
- a entrega é o código junto com a documentação.

## Tecnologias previstas

| Item | Origem | Estado |
| --- | --- | --- |
| Linguagem de preferência, preferencialmente Python | requisito do PDF, com preferência explícita | Python 3.12, implementado |
| Biblioteca de captura; Scapy citado como exemplo | requisito do PDF cita o exemplo | Scapy 2.7.0, `sniff` implementado |
| Docker | requisito do PDF | imagem funcional, rede do host e capabilities |
| Banco de dados | requisito do PDF, produto não nomeado | SQLite implementado |
| Testes automatizados | decisão nossa | pytest, sem interface real |
| GitHub | decisão nossa | repositório local, sem pipeline |

## Arquitetura

O fluxo implementado está em [`../../docs/arquitetura.md`](../../docs/arquitetura.md):

```text
Interface de rede
→ captura de pacotes
→ extração dos campos
→ persistência
→ análise estatística
→ apresentação dos resultados
```

Os módulos estão em `src/traffic_analyzer/`. Captura, parser, ingestão, SQLite, analyzer, CLI, relatório e Docker estão implementados.

## Captura

**Requisito do PDF:** ler pacotes de uma interface especificada e extrair IP de origem, IP de destino, protocolo e tamanho.

**Decisão nossa, implementada:** `sniff` lê a interface informada na CLI, com `promisc=False`. O parser guarda só IPv4. ARP e IPv6 incrementam `ignored_non_ip`. Não há nome de interface fixo no código.

## Armazenamento

**Requisito do PDF:** os pacotes capturados vão para um banco de dados.

**Decisão nossa:** SQLite, só metadados, tabelas `captures` e `packets`, com os índices da especificação aprovada. O schema está em `src/traffic_analyzer/persistence/repository.py`.

## Estatísticas

**Requisito do PDF:** total de pacotes, quantidade por protocolo, top 5 de origem e top 5 de destino.

**Decisão nossa, implementada:** tráfego é a soma de `size_bytes`. O analyzer calcula as quatro estatísticas e o relatório as exibe. `size_bytes` é o comprimento da camada IPv4 lida.

## Execução em Docker

**Requisito do PDF:** o script roda em Docker.

**Decisão nossa, implementada:** a imagem `python:3.12` instala Scapy 2.7.0 e usa a CLI como entrypoint (`python -m traffic_analyzer`). O compose liga a rede do host, acrescenta `CAP_NET_RAW` e `CAP_NET_ADMIN`, deixa `privileged: false` e monta `./data` em `/app/data`. Não há `sudo` na imagem. A interface não está fixada no compose: entra em `--interface`. `promisc=False` continua no sniffer.

`requirements.txt` declara Scapy 2.7.0 e pytest 9.1.1. A imagem instala só o Scapy. O pytest fica no ambiente de testes do host.

## Testes

**Decisão nossa.** O PDF não pede testes. A suíte cobre parser, repositório, ingestão, analyzer, sniffer simulado, CLI, relatório e o texto do Dockerfile e do compose. Nenhum teste automático abre interface de rede nem constrói a imagem. A captura real continua em `tests/manual_capture_wlp3s0.py`, fora do pytest.

## Documentação

**Requisito do PDF:** explicar como configurar, executar e usar, e justificar as decisões.

A documentação desta etapa é este README, a [análise](../../docs/analise-do-desafio.md), a [arquitetura](../../docs/arquitetura.md) e as [decisões](../../docs/decisoes/README.md). O schema já está no repositório SQLite.

## Como executar

O diretório do arquivo SQLite precisa existir. A aplicação não cria essa pasta e não chama `sudo`.

No host, a captura precisa de permissão de socket bruto. Na validação em Linux Mint isso foi feito elevando o processo por fora da aplicação. Sem essa permissão, a CLI termina com mensagem clara e código 3.

```bash
cd challenges/01-analise-de-trafego
sudo .venv/bin/python traffic-analyzer capture --interface wlp3s0 --count 10 --db /tmp/meli-cli.db
.venv/bin/python traffic-analyzer report --db /tmp/meli-cli.db
```

`--count` é o máximo de pacotes IPv4 armazenados. `--duration` é a duração em segundos. Os dois juntos são recusados. Sem nenhum dos dois, a captura segue até Ctrl+C. Ctrl+C grava `ended_at`, conserva os pacotes já gravados e mostra o relatório parcial.

O padrão de `--db` é `data/traffic.db`.

### Docker

O diretório `data/` já existe no repositório. O banco padrão fica em `data/traffic.db` no host, que o container vê como `/app/data/traffic.db`.

```bash
cd challenges/01-analise-de-trafego
docker compose build
docker compose run --rm traffic-analyzer capture --interface wlp3s0 --count 10
docker compose run --rm traffic-analyzer report
```

`--count` e `--duration` funcionam como na CLI do host. Sem os dois, a captura segue até Ctrl+C. Troque `wlp3s0` pelo nome da interface dessa máquina.

A configuração validada usa `CAP_NET_RAW` e `CAP_NET_ADMIN`. Sem essas duas capabilities, a mesma CLI termina com código 3 e avisa que a captura requer permissão adequada. O container não chama `sudo`.
