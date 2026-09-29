# Challenge 02 — Prompt de logs

Fonte: [`../../docs/desafio-mercado-livre.pdf`](../../docs/desafio-mercado-livre.pdf).

## Objetivo

**Requisito do PDF.** Criar um prompt para uma IA analisar um trecho de log bruto de infraestrutura.

A IA deve identificar mensagens de erro, falhas ou comportamentos anômalos, explicar resumidamente o que pode estar acontecendo e sugerir uma solução simples. O PDF cita ChatGPT, Claude, Gemini e outras do mesmo tipo.

## Entregáveis

**Requisito do PDF.** São três:

1. o prompt completo, pronto para colar na IA;
2. um exemplo de trecho de log;
3. a resposta esperada, com a interpretação das mensagens relevantes.

## Como usar

Abra [`prompt.md`](prompt.md) e cole na IA somente o bloco de texto. Em seguida, cole o conteúdo de [`exemplo-de-log.txt`](exemplo-de-log.txt). A leitura esperada desse exemplo está em [`resposta-esperada.md`](resposta-esperada.md).

## Arquivos

| Arquivo | Função |
| --- | --- |
| [`prompt.md`](prompt.md) | Prompt colável |
| [`exemplo-de-log.txt`](exemplo-de-log.txt) | Exemplo de log |
| [`resposta-esperada.md`](resposta-esperada.md) | Interpretação esperada |

O exemplo de log é a transcrição do trecho do PDF, de 16 de maio, 14:01:22 a 14:01:35. A palavra `Unset` no PDF é rótulo do editor, não uma linha do log. As quebras no meio da frase vêm da largura da página e foram reunidas numa linha só.
