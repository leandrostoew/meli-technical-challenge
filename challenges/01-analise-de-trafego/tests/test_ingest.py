"""Ingestão sem interface real: IPv4 é gravado; ARP e IPv6 só incrementam o contador."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from scapy.layers.inet import IP, TCP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP

from traffic_analyzer.capture.ingest import ingest
from traffic_analyzer.persistence.repository import PacketRepository

_WHEN = datetime(2026, 9, 29, 18, 0, 1, tzinfo=timezone.utc)


@pytest.fixture
def repository(tmp_path: Path):
    repo = PacketRepository(tmp_path / "traffic.db")
    yield repo
    repo.close()


def test_ipv4_e_armazenado(repository: PacketRepository) -> None:
    capture_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")
    packet = IP(src="192.0.2.10", dst="198.51.100.20") / TCP()

    stored = ingest(packet, repository, capture_id, captured_at=_WHEN)

    assert stored is True
    packets = repository.list_packets(capture_id)
    assert len(packets) == 1
    assert packets[0].protocol == "TCP"
    assert packets[0].src_ip == "192.0.2.10"
    assert packets[0].dst_ip == "198.51.100.20"
    assert packets[0].size_bytes == len(packet[IP])
    capture = repository.get_last_capture()
    assert capture is not None
    assert capture.ignored_non_ip == 0


def test_arp_nao_e_armazenado_e_incrementa_contador(repository: PacketRepository) -> None:
    capture_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")

    stored = ingest(ARP(), repository, capture_id, captured_at=_WHEN)

    assert stored is False
    assert repository.list_packets(capture_id) == []
    capture = repository.get_last_capture()
    assert capture is not None
    assert capture.ignored_non_ip == 1


def test_ipv6_nao_interrompe_e_nao_grava(repository: PacketRepository) -> None:
    capture_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")
    packet = IPv6(src="2001:db8::1", dst="2001:db8::2")

    stored = ingest(packet, repository, capture_id, captured_at=_WHEN)

    assert stored is False
    assert repository.list_packets(capture_id) == []
    capture = repository.get_last_capture()
    assert capture is not None
    assert capture.ignored_non_ip == 1
