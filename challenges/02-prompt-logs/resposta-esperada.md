# Resposta esperada

Interpretação do log em [`exemplo-de-log.txt`](exemplo-de-log.txt), de 16 de maio, 14:01:22 a 14:01:35. O trecho não comprova uma causa raiz única.

## Resumo

Em cerca de 13 segundos o switch registra a queda de `Gi1/0/1`, uma reconvergência do Spanning Tree na VLAN 10, um duplex incompatível em `Gi1/0/2`, uma violação de port-security em `Gi1/0/5` e uma configuração feita a partir de `192.168.1.5`. A queda da porta e a mudança de topologia ficam próximas no tempo. O log não prova que uma causou a outra. Duplex, port-security e a configuração são registros distintos.

## Eventos

### Queda de Gi1/0/1

- 14:01:22.123, `%LINK-3-UPDOWN`, interface `GigabitEthernet1/0/1`: o link físico foi para down.
- 14:01:22.125, `%LINEPROTO-5-UPDOWN`, a mesma interface: o protocolo de linha também foi para down, 2 ms depois.

As duas linhas descrevem a mesma perda de conectividade. O log não mostra cabo, vizinho, erro de CRC nem o motivo da queda.

Ação: verificar o cabo, o módulo e o estado operacional de `Gi1/0/1`, e o equipamento do outro lado.

### Reconvergência da VLAN0010

Isto é um episódio, não cinco falhas separadas.

- 14:01:23.101, `%SPANTREE-5-TOPO_CHANGE`, VLAN `VLAN0010`: o switch recebeu um aviso de mudança de topologia, cerca de 1 s depois da queda de `Gi1/0/1`.
- 14:01:23.105, `%SPANTREE-6-PORTSTATE`, `Gi1/0/3`: a porta saiu de FORWARDING e entrou em BLOCKING.
- 14:01:24.001, 14:01:26.003 e 14:01:28.005, `%SPANTREE-6-PORTSTATE`, `Gi1/0/4`: a porta percorreu BLOCKING, LISTENING, LEARNING e FORWARDING. Essa sequência é a reconvergência da porta, não quatro incidentes.
- 14:01:28.006, `%SPANTREE-5-ROOTCHANGE`, VLAN `VLAN0010`: a raiz passou a ser `00e0.b6ff.ee11`, com custo 19, pela porta `Gi1/0/4`.

A queda de `Gi1/0/1` pode estar relacionada a essa mudança, porque os horários se sucedem. O trecho não prova essa causa: não diz qual era a raiz anterior nem se `Gi1/0/1` era a porta em direção a ela.

Ação: confirmar se a nova raiz `00e0.b6ff.ee11` é a ponte esperada para a VLAN 10 e se `Gi1/0/4` deve ser o caminho. Só depois olhar se a queda de `Gi1/0/1` explica a troca.

### Duplex incompatível em Gi1/0/2

- 14:01:30.000, `%CDP-4-DUPLEX_MISMATCH`, `GigabitEthernet1/0/2` em full e `SW-Backup GigabitEthernet0/1` em half.

É uma anomalia independente da reconvergência. Os dois lados do enlace estão com duplex diferente. O log não mostra perda de pacote nem qual lado está configurado de forma errada.

Ação: deixar os dois lados no mesmo duplex, de preferência autonegociação, ou full nos dois se a negociação estiver desligada.

### Violação de port-security em Gi1/0/5

- 14:01:32.500, `%PORT_SECURITY-2-PSECURE_VIOLATION`, interface `GigabitEthernet1/0/5`.

Houve uma violação de segurança na porta. O trecho não mostra o MAC que provocou o evento, o limite configurado nem se a porta foi desabilitada.

Ação: ver na porta qual MAC excedeu a política e qual é o modo de violação. Não assumir que a interface caiu.

### Configuração a partir de 192.168.1.5

- 14:01:35.500, `%SYS-5-CONFIG_I`: configurado a partir do console por `vty0 (192.168.1.5)`.

Alguém aplicou configuração por essa sessão. O log registra a origem e não mostra o comando.

Ação: identificar o responsável por `192.168.1.5` e comparar a configuração com a alteração autorizada.

## Conclusão

Há uma queda de link em `Gi1/0/1`, uma reconvergência da VLAN 10 com nova raiz pela `Gi1/0/4`, um duplex divergente com `SW-Backup` e uma violação de port-security em `Gi1/0/5`. A configuração via VTY fica registrada, sem o conteúdo. O trecho aponta onde olhar. Não fecha a causa da queda nem liga, por si só, os quatro assuntos.
