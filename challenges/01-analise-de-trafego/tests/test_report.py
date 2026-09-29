"""Relatório em texto, sem captura e sem banco."""

from traffic_analyzer.analysis.analyzer import IpTraffic, ProtocolCount, TrafficStatistics
from traffic_analyzer.persistence.repository import Capture
from traffic_analyzer.report import render_report


def _session(**overrides: object) -> Capture:
    data: dict[str, object] = {
        "id": 3,
        "interface": "wlp3s0",
        "started_at": "2026-09-29T18:31:34.000Z",
        "ended_at": "2026-09-29T18:31:36.250Z",
        "ignored_non_ip": 3,
    }
    data.update(overrides)
    return Capture(
        id=int(data["id"]),
        interface=str(data["interface"]),
        started_at=str(data["started_at"]),
        ended_at=None if data["ended_at"] is None else str(data["ended_at"]),
        ignored_non_ip=int(data["ignored_non_ip"]),
    )


def _stats() -> TrafficStatistics:
    return TrafficStatistics(
        capture_id=3,
        total_packets=10,
        packets_by_protocol=(
            ProtocolCount("UDP", 6),
            ProtocolCount("TCP", 4),
        ),
        top_sources=(IpTraffic("192.168.2.118", 4200), IpTraffic("192.168.2.1", 800)),
        top_destinations=(IpTraffic("8.8.8.8", 3000),),
    )


def test_relatorio_traz_os_campos_obrigatorios() -> None:
    text = render_report(
        stats=_stats(),
        session=_session(),
        db_path="/tmp/meli-wlp3s0.db",
        packets_seen=13,
        packets_stored=10,
        packets_ignored=3,
        interrupted=False,
    )

    assert "Interface: wlp3s0" in text
    assert "Status: concluída" in text
    assert "Total de pacotes: 10" in text
    assert "UDP  6" in text
    assert "TCP  4" in text
    assert "Top 5 IPs de origem por tráfego (bytes):" in text
    assert "1  192.168.2.118  4200" in text
    assert "Top 5 IPs de destino por tráfego (bytes):" in text
    assert "1  8.8.8.8  3000" in text
    assert "Ignorados: 3" in text
    assert "Processados: 13" in text
    assert "Armazenados: 10" in text
    assert "SQLite: /tmp/meli-wlp3s0.db" in text
    assert "Duração: 2.250 s" in text
    assert (
        "Total de pacotes corresponde aos pacotes IPv4 armazenados. "
        "Quadros sem IPv4 são contabilizados separadamente como ignorados."
    ) in text


def test_relatorio_interrompido_nao_mostra_duracao_sem_fim() -> None:
    text = render_report(
        stats=TrafficStatistics(1, 0, (), (), ()),
        session=_session(ended_at=None, ignored_non_ip=0),
        db_path="data/traffic.db",
        packets_seen=0,
        packets_stored=0,
        packets_ignored=0,
        interrupted=True,
    )

    assert "Status: interrompida" in text
    assert "Duração:" not in text
    assert "(nenhum)" in text
