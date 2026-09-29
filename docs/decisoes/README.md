# Decisões técnicas

**REQUISITO DO PDF** é o que o enunciado pede. **DECISÃO NOSSA** é escolha do projeto. O registro abaixo descreve o que já foi aprovado. Onde a implementação ainda não existe, o status diz isso.

| ID | Tema | Status |
| --- | --- | --- |
| 0001 | Separação dos challenges | aprovado |
| 0002 | Python | aprovado |
| 0003 | Scapy | aprovado |
| 0004 | Docker | requisito do PDF / implementado |
| 0005 | Testes automatizados | decisão nossa / implementado parcialmente |
| 0006 | GitHub | decisão nossa |
| 0007 | SQLite | aprovado |
| 0008 | Métrica de tráfego | aprovado |
| 0009 | IPv4 no escopo inicial | aprovado |
| 0010 | Timestamp UTC | aprovado |
| 0011 | Diretório do SQLite | decisão nossa |

## 0001 — Separação dos challenges

Status: aprovado.

**DECISÃO NOSSA.** Os dois desafios ficam em pastas independentes, para facilitar desenvolvimento, testes e documentação. O Challenge 01 não contém o prompt de logs. O Challenge 02 não contém captura de pacotes.

## 0002 — Python

Status: aprovado.

**DECISÃO NOSSA.** Python foi escolhido porque o PDF permite linguagem de preferência e cita Python como preferência. O Challenge 01 está em Python 3.12.

## 0003 — Scapy

Status: aprovado.

**DECISÃO NOSSA.** O PDF cita Scapy em Python como exemplo de biblioteca adequada para captura. O parser e o `sniff` usam Scapy 2.7.0. A CLI chama `capture_packets`. A imagem Docker instala essa mesma versão e usa a CLI como entrypoint.

## 0004 — Docker

Status: requisito do PDF / implementado.

**REQUISITO DO PDF.** O PDF exige que o script do Challenge 01 seja executado em Docker.

**DECISÃO NOSSA, implementada.** A imagem usa Python 3.12 e Scapy 2.7.0. O entrypoint é `python -m traffic_analyzer`, a CLI já validada. O compose sobe com `network_mode: host`, `CAP_NET_RAW`, `CAP_NET_ADMIN` e `privileged: false`. Não há `sudo` na imagem nem na aplicação. A interface continua sendo o argumento `--interface`. `promisc=False` permanece no sniffer.

O SQLite fica no volume `./data:/app/data`. O caminho padrão `data/traffic.db` aparece no host em `challenges/01-analise-de-trafego/data/traffic.db`. O diretório `data/` já vem no repositório; o repository continua sem criar pastas.

O processo dentro do container é o root da imagem, porque essas capabilities valem para ele. A aplicação não eleva privilégio.

## 0005 — Testes automatizados

Status: decisão nossa / implementado parcialmente.

**DECISÃO NOSSA.** Testes automatizados não são uma exigência explícita do PDF. A suíte cobre parser, persistência, ingestão, analyzer, sniffer simulado, CLI, relatório e o contrato do Dockerfile e do compose. Nenhum teste automático abre interface de rede nem constrói a imagem.

## 0006 — GitHub

Status: decisão nossa.

**DECISÃO NOSSA.** O PDF exige código e documentação, mas não determina que o repositório seja público. O repositório organiza e compartilha a entrega.

## 0007 — SQLite

Status: aprovado.

**REQUISITO DO PDF:** armazenar os pacotes capturados em um banco de dados. O PDF não especifica a tecnologia.

**DECISÃO NOSSA.** SQLite foi escolhido por simplicidade, persistência relacional e ausência de dependência externa. O schema aprovado, com as tabelas `captures` e `packets`, está implementado.

## 0008 — Métrica de tráfego

Status: aprovado.

**REQUISITO DO PDF:** top 5 de IPs de origem e de destino com mais tráfego. O PDF não define como "mais tráfego" é calculado.

**DECISÃO NOSSA.**

```text
traffic_bytes = soma dos bytes dos pacotes associados ao IP
```

Para o top 5 de origem: agrupar por `src_ip` e somar `size_bytes`.

Para o top 5 de destino: agrupar por `dst_ip` e somar `size_bytes`.

`size_bytes` é o comprimento da camada IPv4 lida. O analyzer e o relatório já usam essa soma.

## 0009 — IPv4 no escopo inicial

Status: aprovado.

**DECISÃO NOSSA.** Isso é uma decisão de escopo nossa, não uma exigência explícita do PDF.

A implementação inicial considera pacotes IPv4 para as estatísticas solicitadas. Pacotes sem camada IPv4, incluindo ARP e IPv6, não são armazenados como pacotes analisáveis e incrementam `ignored_non_ip`.

## 0010 — Timestamp UTC

Status: aprovado.

**DECISÃO NOSSA.** Os timestamps são armazenados em UTC, com precisão de milissegundos e formato documentado pela implementação: `YYYY-MM-DDTHH:MM:SS.mmmZ`.

## 0011 — Diretório do SQLite

Status: decisão nossa.

**DECISÃO NOSSA.** O diretório informado para o banco deve existir antes da inicialização. O repository não cria diretórios automaticamente.
