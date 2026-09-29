# Meli

Solução em preparação para o processo seletivo do Mercado Livre.

O enunciado está em [`docs/desafio-mercado-livre.pdf`](docs/desafio-mercado-livre.pdf). Esse PDF é a fonte dos requisitos. O que não estiver nele aparece neste repositório como decisão nossa.

O prazo escrito no PDF é de 2 dias para os dois challenges. O Challenge 01 captura com Scapy, grava em SQLite, calcula as estatísticas, exibe o relatório pela CLI e roda em Docker. O Challenge 02 segue sem o prompt escrito.

## Challenges

| Challenge | O que é | Onde está |
| --- | --- | --- |
| 01 — Análise de tráfego | Aplicação que captura pacotes de uma interface, guarda os pacotes em banco e exibe estatísticas. O script roda em Docker. | [`challenges/01-analise-de-trafego`](challenges/01-analise-de-trafego/README.md) |
| 02 — Prompt de logs | Prompt para uma IA ler um log bruto, apontar erros, falhas ou comportamentos anômalos, explicar o que pode estar acontecendo e sugerir uma solução simples. | [`challenges/02-prompt-logs`](challenges/02-prompt-logs/README.md) |

Os dois challenges ficam em pastas separadas. Um não implementa o outro.

## Estrutura

```text
.
├── .github/workflows/
├── challenges/
│   ├── 01-analise-de-trafego/
│   └── 02-prompt-logs/
├── docs/
│   ├── desafio-mercado-livre.pdf
│   ├── analise-do-desafio.md
│   ├── arquitetura.md
│   └── decisoes/
├── .gitignore
└── README.md
```

## Como navegar

- Requisitos do PDF, em leitura nossa: [`docs/analise-do-desafio.md`](docs/analise-do-desafio.md)
- Fluxo do Challenge 01: [`docs/arquitetura.md`](docs/arquitetura.md)
- Decisões já registradas e o que continua em aberto: [`docs/decisoes/README.md`](docs/decisoes/README.md)
- Challenge 01: [`challenges/01-analise-de-trafego/README.md`](challenges/01-analise-de-trafego/README.md)
- Challenge 02: [`challenges/02-prompt-logs/README.md`](challenges/02-prompt-logs/README.md)
