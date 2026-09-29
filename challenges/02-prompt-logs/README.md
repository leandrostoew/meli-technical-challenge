# Challenge 02 — Prompt de logs

Fonte: [`../../docs/desafio-mercado-livre.pdf`](../../docs/desafio-mercado-livre.pdf).

## Objetivo

**Requisito do PDF.** Criar um prompt para uma IA analisar um trecho de log bruto de infraestrutura.

A IA deve identificar mensagens de erro, falhas ou comportamentos anômalos, explicar resumidamente o que pode estar acontecendo e sugerir uma solução simples. O PDF cita ChatGPT, Claude, Gemini e outras do mesmo tipo.

Não há aplicação, banco nem Docker neste challenge.

## O que cada arquivo é

| Arquivo | Função |
| --- | --- |
| [`prompt.md`](prompt.md) | Prompt completo. Cole na IA somente o bloco de texto. Ele não cita o exemplo de 16 de maio e serve para outro log bruto. |
| [`exemplo-de-log.txt`](exemplo-de-log.txt) | Log usado na entrega. É a transcrição do exemplo do PDF, de 16 de maio, 14:01:22 a 14:01:35, sem linhas inventadas. |
| [`resposta-esperada.md`](resposta-esperada.md) | Interpretação esperada das mensagens desse exemplo. |

A palavra `Unset` no PDF é rótulo do editor, não uma linha do log. As quebras no meio da frase vêm da largura da página e foram reunidas numa linha só.

## Como reproduzir

1. Abra [`prompt.md`](prompt.md) e copie só o bloco.
2. Cole o bloco na IA.
3. Em seguida, cole o conteúdo de [`exemplo-de-log.txt`](exemplo-de-log.txt).
4. Compare a resposta com [`resposta-esperada.md`](resposta-esperada.md).

Para outro log, repita os passos 1 e 2 e cole o trecho novo no lugar do exemplo. A resposta esperada deste repositório vale para o log do PDF, não para um trecho diferente.
