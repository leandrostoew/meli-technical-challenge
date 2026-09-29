"""Parser IPv4 com pacotes Scapy em memória. Nenhuma interface é aberta."""

from datetime import datetime, timezone

import pytest
from scapy.layers.inet import ICMP, IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP
from scapy.packet import Raw

from traffic_analyzer.errors import InvalidArgumentError
from traffic_analyzer.parsing.parser import parse_ipv4

_WHEN = datetime(2026, 9, 29, 18, 0, 0, tzinfo=timezone.utc)
_SRC = "192.0.2.10"
_DST = "198.51.100.20"


def _ipv4(proto_layer=None, *, proto: int | None = None, payload: bytes = b""):
    packet = IP(src=_SRC, dst=_DST)
    if proto is not None:
        packet.proto = proto
    if proto_layer is not None:
        packet = packet / proto_layer
    if payload:
        packet = packet / Raw(load=payload)
    return packet


def test_tcp_extrai_ips_protocolo_e_tamanho() -> None:
    packet = _ipv4(TCP(), payload=b"abc")
    parsed = parse_ipv4(packet, captured_at=_WHEN)

    assert parsed is not None
    assert parsed.src_ip == _SRC
    assert parsed.dst_ip == _DST
    assert parsed.protocol == "TCP"
    assert parsed.size_bytes == len(packet[IP])
    assert parsed.captured_at == "2026-09-29T18:00:00.000Z"


def test_udp_e_identificado_como_udp() -> None:
    parsed = parse_ipv4(_ipv4(UDP()), captured_at=_WHEN)

    assert parsed is not None
    assert parsed.protocol == "UDP"


def test_icmp_e_identificado_como_icmp() -> None:
    parsed = parse_ipv4(_ipv4(ICMP()), captured_at=_WHEN)

    assert parsed is not None
    assert parsed.protocol == "ICMP"


def test_protocolo_desconhecido_vira_other() -> None:
    parsed = parse_ipv4(_ipv4(proto=47), captured_at=_WHEN)

    assert parsed is not None
    assert parsed.protocol == "OTHER(47)"
    assert parsed.src_ip == _SRC
    assert parsed.dst_ip == _DST
    assert parsed.size_bytes == len(IP(src=_SRC, dst=_DST, proto=47))


def test_arp_nao_tem_camada_ipv4() -> None:
    assert parse_ipv4(ARP(), captured_at=_WHEN) is None


def test_ipv6_nao_tem_camada_ipv4() -> None:
    packet = IPv6(src="2001:db8::1", dst="2001:db8::2")
    assert parse_ipv4(packet, captured_at=_WHEN) is None


def test_horario_sem_fuso_e_recusado() -> None:
    packet = _ipv4(TCP())
    with pytest.raises(InvalidArgumentError):
        parse_ipv4(packet, captured_at=datetime(2026, 9, 29, 18, 0, 0))


def test_valor_que_nao_e_pacote_e_recusado() -> None:
    with pytest.raises(InvalidArgumentError):
        parse_ipv4("nao-e-pacote", captured_at=_WHEN)
