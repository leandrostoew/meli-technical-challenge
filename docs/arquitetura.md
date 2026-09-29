# Arquitetura

O Challenge 01 está implementado até a CLI, o relatório e o Docker. O banco, o schema, a captura e o formato da saída já foram escolhidos; ver [`decisoes/README.md`](decisoes/README.md).

## Challenge 01

**Requisito do PDF:** capturar pacotes de uma interface, guardar IP de origem, IP de destino, protocolo e tamanho, persistir em banco e exibir total, pacotes por protocolo e top 5 de origem e de destino.

**Decisão nossa, implementada:** a ordem abaixo é a da aplicação.

```text
Interface de rede
        │
        ▼
CLI  capture --interface
        │
        ▼
Scapy sniff  (promisc=False, store=False)
        │
        ▼
Ingest → parser IPv4
        │
        ├── IPv4 → SQLite packets
        └── sem IPv4 → ignored_non_ip
        │
        ▼
Analyzer
  total de pacotes IPv4
  pacotes por protocolo
  top 5 origem e destino por soma de size_bytes
        │
        ▼
Relatório no terminal
```

`size_bytes` é o comprimento da camada IPv4 lida. Essa cadeia roda na CLI do host e no container. O compose usa a rede do host, `CAP_NET_RAW`, `CAP_NET_ADMIN` e o volume `./data` para o SQLite. Não usa `--privileged` nem `sudo`.

## Challenge 02

Não há aplicação nem fluxo de execução. A entrega são três arquivos:

1. o prompt colável;
2. o exemplo de log transcrito do PDF;
3. a resposta esperada da IA.

Eles estão em [`../challenges/02-prompt-logs`](../challenges/02-prompt-logs/README.md). O prompt não depende desse exemplo.
