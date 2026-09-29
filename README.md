# Meli

Avaliação técnica para o processo seletivo do Mercado Livre. O enunciado está em [`docs/desafio-mercado-livre.pdf`](docs/desafio-mercado-livre.pdf). O que não estiver nesse PDF aparece neste repositório como decisão nossa.

O prazo escrito no PDF é de 2 dias para os dois challenges. Eles ficam em pastas separadas. Um não implementa o outro.

## Challenges

| Challenge | O que entrega | Onde está |
| --- | --- | --- |
| 01 — Análise de tráfego | Aplicação em Python: CLI, captura com Scapy, SQLite, estatísticas, testes e execução em Docker. | [`challenges/01-analise-de-trafego`](challenges/01-analise-de-trafego/README.md) |
| 02 — Prompt de logs | Prompt reutilizável para uma IA ler um log bruto, o exemplo transcrito do PDF e a resposta esperada. | [`challenges/02-prompt-logs`](challenges/02-prompt-logs/README.md) |

## Estrutura

```text
.
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

## Por onde começar

1. Leia o PDF.
2. Para o Challenge 01, siga o [guia de execução](challenges/01-analise-de-trafego/README.md). A suíte automatizada, a partir dessa pasta:

```bash
cd challenges/01-analise-de-trafego
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```

3. Para o Challenge 02, abra o [README do prompt](challenges/02-prompt-logs/README.md), cole o bloco de [`prompt.md`](challenges/02-prompt-logs/prompt.md) na IA e, em seguida, o log de exemplo.

## Documentação

- Leitura do enunciado: [`docs/analise-do-desafio.md`](docs/analise-do-desafio.md)
- Fluxo do Challenge 01 e artefatos do Challenge 02: [`docs/arquitetura.md`](docs/arquitetura.md)
- Decisões técnicas: [`docs/decisoes/README.md`](docs/decisoes/README.md)
