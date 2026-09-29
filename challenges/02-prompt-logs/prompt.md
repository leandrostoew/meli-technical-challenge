# Prompt

Cole na IA apenas o bloco abaixo. Em seguida, cole o log bruto. O bloco não depende de nenhum outro arquivo.

```text
Você analisa um trecho de log bruto de infraestrutura. Leia somente o que estiver no trecho. Não invente horário, interface, endereço, comando, causa ou efeito que a linha não mostre.

Tarefa:
1. Identifique mensagens de erro, falhas e comportamentos anômalos.
2. Preserve a ordem temporal.
3. Em cada mensagem relevante, informe o horário, o código da mensagem e a interface ou VLAN, quando esses dados existirem na linha.
4. Explique de forma objetiva o que o evento indica.
5. Separe causa possível de efeito ou consequência. Correlacione eventos do mesmo episódio. Em especial, trate a reconvergência do Spanning Tree como um único episódio.
6. Não trate a sequência BLOCKING, LISTENING, LEARNING e FORWARDING como falhas independentes. Ela é a passagem normal de uma porta nessa reconvergência.
7. Para cada problema relevante, sugira uma ação simples e prática.
8. Quando o trecho não bastar para confirmar a causa, escreva isso com clareza.
9. Feche com uma conclusão curta sobre o cenário.

Formato da resposta:
- Resumo, em poucas linhas.
- Eventos, na ordem do log. Para cada um: horário, código, interface ou VLAN, o que indica, se é causa possível ou efeito, e a ação simples. Agrupe no mesmo item as linhas que forem um único episódio.
- Conclusão curta.

Log bruto:
```
