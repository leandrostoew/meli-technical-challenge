"""Estatísticas sobre SQLite temporário. Nenhuma interface de rede é aberta."""

from pathlib import Path

import pytest

from traffic_analyzer.analysis.analyzer import analyze_capture
from traffic_analyzer.persistence.repository import PacketRepository

_WHEN = "2026-09-29T18:00:00.000Z"


@pytest.fixture
def repository(tmp_path: Path):
    repo = PacketRepository(tmp_path / "traffic.db")
    yield repo
    repo.close()


def _capture(repository: PacketRepository, interface: str = "eth0") -> int:
    return repository.create_capture(interface, _WHEN)


def _packet(
    repository: PacketRepository,
    capture_id: int,
    src_ip: str,
    dst_ip: str,
    protocol: str,
    size_bytes: int,
) -> None:
    repository.insert_packet(
        capture_id=capture_id,
        captured_at="2026-09-29T18:00:01.000Z",
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=protocol,
        size_bytes=size_bytes,
    )


def test_captura_sem_pacotes(repository: PacketRepository) -> None:
    capture_id = _capture(repository)

    stats = analyze_capture(repository, capture_id)

    assert stats.capture_id == capture_id
    assert stats.total_packets == 0
    assert stats.packets_by_protocol == ()
    assert stats.top_sources == ()
    assert stats.top_destinations == ()


def test_total_ignora_quadros_sem_linha(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    _packet(repository, capture_id, "192.0.2.1", "198.51.100.1", "TCP", 40)
    _packet(repository, capture_id, "192.0.2.2", "198.51.100.2", "UDP", 20)
    repository.increment_ignored_non_ip(capture_id)
    repository.increment_ignored_non_ip(capture_id)
    repository.increment_ignored_non_ip(capture_id)

    stats = analyze_capture(repository, capture_id)

    assert stats.total_packets == 2


def test_contagem_por_protocolo_usa_o_nome_gravado(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    _packet(repository, capture_id, "192.0.2.1", "198.51.100.1", "TCP", 10)
    _packet(repository, capture_id, "192.0.2.1", "198.51.100.1", "TCP", 10)
    _packet(repository, capture_id, "192.0.2.2", "198.51.100.2", "UDP", 10)
    _packet(repository, capture_id, "192.0.2.2", "198.51.100.2", "UDP", 10)
    _packet(repository, capture_id, "192.0.2.3", "198.51.100.3", "ICMP", 10)
    _packet(repository, capture_id, "192.0.2.4", "198.51.100.4", "OTHER(47)", 10)

    stats = analyze_capture(repository, capture_id)
    counts = [(item.protocol, item.packet_count) for item in stats.packets_by_protocol]

    assert counts == [("TCP", 2), ("UDP", 2), ("ICMP", 1), ("OTHER(47)", 1)]


def test_soma_de_bytes_nao_e_contagem_nem_maximo(repository: PacketRepository) -> None:
    """Três origens em que contagem, máximo e soma produziriam ordens diferentes.

    ip-soma: um pacote de 200. Soma 200. Contagem 1. Máximo 200.
    ip-contagem: quatro pacotes de 30. Soma 120. Contagem 4. Máximo 30.
    ip-maximo: um pacote de 90. Soma 90. Contagem 1. Máximo 90.

    Soma: 200, 120, 90.
    Contagem: ip-contagem primeiro.
    Máximo: 200, 90, 120.
    """
    capture_id = _capture(repository)
    _packet(repository, capture_id, "ip-soma", "dst-a", "TCP", 200)
    for _ in range(4):
        _packet(repository, capture_id, "ip-contagem", "dst-b", "UDP", 30)
    _packet(repository, capture_id, "ip-maximo", "dst-c", "ICMP", 90)

    stats = analyze_capture(repository, capture_id)
    ranking = [(item.ip, item.traffic_bytes) for item in stats.top_sources]

    assert ranking == [("ip-soma", 200), ("ip-contagem", 120), ("ip-maximo", 90)]
    assert stats.top_sources[1].traffic_bytes == 30 + 30 + 30 + 30


def test_top5_origem_agrupa_src_ip(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    _packet(repository, capture_id, "10.0.0.1", "198.51.100.1", "TCP", 100)
    _packet(repository, capture_id, "10.0.0.1", "198.51.100.2", "TCP", 50)
    _packet(repository, capture_id, "10.0.0.2", "198.51.100.1", "UDP", 10)

    stats = analyze_capture(repository, capture_id)

    assert [(item.ip, item.traffic_bytes) for item in stats.top_sources] == [
        ("10.0.0.1", 150),
        ("10.0.0.2", 10),
    ]


def test_top5_destino_agrupa_dst_ip(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    _packet(repository, capture_id, "192.0.2.1", "198.51.100.8", "TCP", 100)
    _packet(repository, capture_id, "192.0.2.2", "198.51.100.8", "UDP", 10)
    _packet(repository, capture_id, "192.0.2.1", "198.51.100.9", "TCP", 40)

    stats = analyze_capture(repository, capture_id)

    assert [(item.ip, item.traffic_bytes) for item in stats.top_destinations] == [
        ("198.51.100.8", 110),
        ("198.51.100.9", 40),
    ]


def test_menos_de_cinco_ips(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    _packet(repository, capture_id, "10.0.0.2", "198.51.100.2", "TCP", 20)
    _packet(repository, capture_id, "10.0.0.1", "198.51.100.1", "TCP", 50)

    sources = analyze_capture(repository, capture_id).top_sources

    assert len(sources) == 2
    assert [item.ip for item in sources] == ["10.0.0.1", "10.0.0.2"]


def test_exatamente_cinco_ips(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    for index, size in enumerate((50, 40, 30, 20, 10), start=1):
        _packet(repository, capture_id, f"10.0.0.{index}", "198.51.100.1", "TCP", size)

    sources = analyze_capture(repository, capture_id).top_sources

    assert [item.traffic_bytes for item in sources] == [50, 40, 30, 20, 10]
    assert len(sources) == 5


def test_mais_de_cinco_ips_descarta_o_menor(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    for index, size in enumerate((60, 50, 40, 30, 20, 10), start=1):
        _packet(repository, capture_id, f"10.0.0.{index}", "198.51.100.1", "TCP", size)

    sources = analyze_capture(repository, capture_id).top_sources
    ips = [item.ip for item in sources]

    assert ips == ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]
    assert "10.0.0.6" not in ips
    assert [item.traffic_bytes for item in sources] == [60, 50, 40, 30, 20]


def test_empate_de_bytes_ordena_o_ip(repository: PacketRepository) -> None:
    capture_id = _capture(repository)
    _packet(repository, capture_id, "10.0.0.9", "198.51.100.9", "TCP", 500)
    _packet(repository, capture_id, "10.0.0.1", "198.51.100.1", "UDP", 500)
    _packet(repository, capture_id, "10.0.0.5", "198.51.100.5", "ICMP", 100)

    stats = analyze_capture(repository, capture_id)

    assert [(item.ip, item.traffic_bytes) for item in stats.top_sources] == [
        ("10.0.0.1", 500),
        ("10.0.0.9", 500),
        ("10.0.0.5", 100),
    ]
    assert [(item.ip, item.traffic_bytes) for item in stats.top_destinations] == [
        ("198.51.100.1", 500),
        ("198.51.100.9", 500),
        ("198.51.100.5", 100),
    ]


def test_capturas_diferentes_nao_se_misturam(repository: PacketRepository) -> None:
    first = _capture(repository, "eth0")
    second = _capture(repository, "eth1")
    _packet(repository, first, "1.1.1.1", "8.8.8.8", "TCP", 9999)
    _packet(repository, second, "2.2.2.2", "1.1.1.1", "UDP", 10)
    _packet(repository, second, "2.2.2.2", "1.1.1.1", "UDP", 5)

    stats = analyze_capture(repository, second)

    assert stats.capture_id == second
    assert stats.total_packets == 2
    assert [(item.ip, item.traffic_bytes) for item in stats.top_sources] == [("2.2.2.2", 15)]
    assert [(item.ip, item.traffic_bytes) for item in stats.top_destinations] == [("1.1.1.1", 15)]
    assert [(item.protocol, item.packet_count) for item in stats.packets_by_protocol] == [("UDP", 2)]
