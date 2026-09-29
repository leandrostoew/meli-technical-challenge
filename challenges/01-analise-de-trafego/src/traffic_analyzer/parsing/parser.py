"""Extrai IP de origem, IP de destino, protocolo e tamanho de um pacote IPv4.

Pacote sem a camada IPv4 do Scapy devolve `None`. Quem chama decide o contador
`ignored_non_ip`. Esta função não grava nada e não interrompe o fluxo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from scapy.layers.inet import IP

from traffic_analyzer.errors import InvalidArgumentError

_TCP = 6
_UDP = 17
_ICMP = 1


@dataclass(frozen=True)
class ParsedPacket:
    """Campos de um IPv4 aceito. `size_bytes` é o comprimento da camada IPv4 lida."""

    src_ip: str
    dst_ip: str
    protocol: str
    size_bytes: int
    captured_at: str


def protocol_name(ip_proto: int) -> str:
    """Nome estável do protocolo IP: TCP, UDP, ICMP ou OTHER(número)."""
    if ip_proto == _TCP:
        return "TCP"
    if ip_proto == _UDP:
        return "UDP"
    if ip_proto == _ICMP:
        return "ICMP"
    return f"OTHER({ip_proto})"


def parse_ipv4(packet: Any, *, captured_at: datetime | None = None) -> ParsedPacket | None:
    """Devolve o registro IPv4, ou `None` quando o quadro não tem camada IP.

    `captured_at` ausente usa o relógio UTC. Valor informado precisa ter fuso.
    """
    if packet is None or not hasattr(packet, "haslayer"):
        raise InvalidArgumentError("O pacote precisa ser um pacote Scapy.")
    if not packet.haslayer(IP):
        return None

    ip_layer = packet[IP]
    moment = captured_at if captured_at is not None else datetime.now(timezone.utc)
    return ParsedPacket(
        src_ip=str(ip_layer.src),
        dst_ip=str(ip_layer.dst),
        protocol=protocol_name(int(ip_layer.proto)),
        size_bytes=len(ip_layer),
        captured_at=_format_utc(moment),
    )


def _format_utc(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise InvalidArgumentError("captured_at precisa informar o fuso horário.")
    text = moment.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    return text.replace("+00:00", "Z")
