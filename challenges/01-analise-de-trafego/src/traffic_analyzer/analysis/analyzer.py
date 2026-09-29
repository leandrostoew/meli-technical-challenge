"""Estatísticas de uma captura já gravada no SQLite.

Não importa Scapy e não lê interface de rede. A entrada são as linhas de
`packets` da sessão pedida.

Tráfego de um IP:

    traffic_bytes = soma de size_bytes dos pacotes associados a esse IP

Top 5: traffic_bytes decrescente. Empate: endereço IP em ordem alfabética
crescente. A mesma regra vale para origem (`src_ip`) e destino (`dst_ip`).

Protocolos: quantidade de pacotes, não de bytes. Ordem: quantidade
decrescente e, no empate, o nome do protocolo em ordem alfabética crescente.
O nome é o que o parser gravou: TCP, UDP, ICMP ou OTHER(<número>).

Quadros só contabilizados em `ignored_non_ip` não têm linha em `packets` e
não entram nestas contas.
"""

from __future__ import annotations

from dataclasses import dataclass

from traffic_analyzer.persistence.repository import PacketRepository, StoredPacket

_TOP_LIMIT = 5


@dataclass(frozen=True)
class ProtocolCount:
    """Quantidade de pacotes armazenados de um protocolo."""

    protocol: str
    packet_count: int


@dataclass(frozen=True)
class IpTraffic:
    """Volume de um IP na sessão, em bytes."""

    ip: str
    traffic_bytes: int


@dataclass(frozen=True)
class TrafficStatistics:
    """As quatro estatísticas do PDF para uma captura."""

    capture_id: int
    total_packets: int
    packets_by_protocol: tuple[ProtocolCount, ...]
    top_sources: tuple[IpTraffic, ...]
    top_destinations: tuple[IpTraffic, ...]


def analyze_capture(repository: PacketRepository, capture_id: int) -> TrafficStatistics:
    """Lê os pacotes da captura no SQLite e devolve as estatísticas."""
    return _from_packets(capture_id, repository.list_packets(capture_id))


def _from_packets(capture_id: int, packets: list[StoredPacket]) -> TrafficStatistics:
    by_protocol: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_destination: dict[str, int] = {}

    for packet in packets:
        by_protocol[packet.protocol] = by_protocol.get(packet.protocol, 0) + 1
        by_source[packet.src_ip] = by_source.get(packet.src_ip, 0) + packet.size_bytes
        by_destination[packet.dst_ip] = by_destination.get(packet.dst_ip, 0) + packet.size_bytes

    return TrafficStatistics(
        capture_id=capture_id,
        total_packets=len(packets),
        packets_by_protocol=_rank_protocols(by_protocol),
        top_sources=_rank_ips(by_source),
        top_destinations=_rank_ips(by_destination),
    )


def _rank_protocols(counts: dict[str, int]) -> tuple[ProtocolCount, ...]:
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return tuple(ProtocolCount(protocol=name, packet_count=count) for name, count in ordered)


def _rank_ips(totals: dict[str, int]) -> tuple[IpTraffic, ...]:
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return tuple(
        IpTraffic(ip=ip, traffic_bytes=total) for ip, total in ordered[:_TOP_LIMIT]
    )
