# Análise do desafio

Fonte única: [`desafio-mercado-livre.pdf`](desafio-mercado-livre.pdf).

O cabeçalho do PDF está em português e fixa 2 dias para a realização de todos os challenges.

## Challenge 01

**Requisito do PDF.** Desenvolver uma aplicação de análise de tráfego que capture pacotes de uma interface de rede especificada e exiba estatísticas básicas.

### Captura

- Script ou aplicação que capture pacotes de uma interface especificada.
- Biblioteca ou ferramenta adequada. O PDF cita Scapy em Python como exemplo.
- Campos capturados: endereço IP de origem, endereço IP de destino, protocolo e tamanho do pacote.

### Análise

- Número total de pacotes capturados.
- Número de pacotes por protocolo. O PDF cita TCP e UDP como exemplo.
- Top 5 endereços IP de origem com mais tráfego.
- Top 5 endereços IP de destino com mais tráfego.

### Armazenamento

- Os pacotes capturados são armazenados em um banco de dados.
- O PDF não nomeia o banco nem o schema.

### Tecnologias

- Linguagem de preferência do candidato, preferencialmente Python.
- O script deverá ser executado em Docker.

### Avaliação e entrega

- Funcionalidade: capturar pacotes e exibir as estatísticas básicas.
- Documentação de como configurar, executar e usar a aplicação.
- Justificativa das escolhas. O PDF cita, como exemplo, o schema da base e informações relevantes sobre o script.
- Entrega: o código junto com a documentação.

## Challenge 02

**Requisito do PDF.** Criar um prompt para uma IA (o PDF cita ChatGPT, Claude, Gemini e outras) que:

- leia um trecho de log bruto;
- identifique mensagens de erro, falhas ou comportamentos anômalos;
- explique resumidamente o que pode estar acontecendo;
- ofereça uma sugestão de solução simples.

O contexto do PDF é uma equipe de infraestrutura que analisa grandes volumes de logs em busca de falhas, erros ou comportamentos suspeitos.

### O que enviar

1. Um prompt completo, pronto para colar na IA.
2. Um exemplo de trecho de log. Pode ser o fornecido no PDF ou um expandido.
3. Uma resposta esperada da IA, com a interpretação das mensagens relevantes.

O PDF inclui um log de exemplo, de 16 de maio, entre 14:01:22 e 14:01:35. A transcrição está em [`../challenges/02-prompt-logs/exemplo-de-log.txt`](../challenges/02-prompt-logs/exemplo-de-log.txt). A palavra "Unset" no PDF é rótulo de bloco do editor, não uma linha do log.

## O que o PDF não define

Estes pontos não são requisito do Mercado Livre. As escolhas do Challenge 01 já estão em [`decisoes/README.md`](decisoes/README.md):

- banco e schema: SQLite, só metadados, implementado;
- "mais tráfego": soma de `size_bytes`, implementado no analyzer;
- interface de rede: argumento `--interface` da CLI;
- saída: relatório de texto no terminal;
- captura: Scapy `sniff`, implementado;
- módulos: separados em captura, parser, ingestão, repositório, analyzer, CLI e relatório.

A imagem Docker do Challenge 01 está implementada. O exemplo de log do Challenge 02 pode ser o do PDF ou uma expansão; o texto do prompt ainda não foi escrito.
