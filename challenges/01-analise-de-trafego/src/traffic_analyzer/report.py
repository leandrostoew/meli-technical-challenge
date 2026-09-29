"""Texto do relatório no terminal.

Não captura pacotes e não grava no banco. Recebe a sessão, as estatísticas
e os contadores da leitura.
"""

from __future__ import annotations

from datetime import datetime

from traffic_analyzer.analysis.analyzer import IpTraffic, ProtocolCount, TrafficStatistics
from traffic_analyzer.persistence.repository import Capture

_IPV4_NOTE = (
    "Total de pacotes corresponde aos pacotes IPv4 armazenados. "
    "Quadros sem IPv4 são contabilizados separadamente como ignorados."
)


def render_report(
    *,
    stats: TrafficStatistics,
    session: Capture,
    db_path: str,
    packets_seen: int,
    packets_stored: int,
    packets_ignored: int,
    interrupted: bool,
) -> str:
    """Monta o relatório de uma captura já encerrada ou interrompida."""
    lines = [
        f"Interface: {session.interface}",
        f"Status: {_status(interrupted, session.ended_at)}",
        f"SQLite: {db_path}",
    ]
    duration = _duration(session.started_at, session.ended_at)
    if duration is not None:
        lines.append(f"Duração: {duration}")
    lines.extend(
        [
            f"Processados: {packets_seen}",
            f"Armazenados: {packets_stored}",
            f"Ignorados: {packets_ignored}",
            "",
            f"Total de pacotes: {stats.total_packets}",
            _IPV4_NOTE,
            "",
            "Pacotes por protocolo:",
            *_protocol_lines(stats.packets_by_protocol),
            "",
            "Top 5 IPs de origem por tráfego (bytes):",
            *_ip_lines(stats.top_sources),
            "",
            "Top 5 IPs de destino por tráfego (bytes):",
            *_ip_lines(stats.top_destinations),
        ]
    )
    return "\n".join(lines)


def _status(interrupted: bool, ended_at: str | None) -> str:
    if interrupted:
        return "interrompida"
    if ended_at is None:
        return "em andamento"
    return "concluída"


def _duration(started_at: str, ended_at: str | None) -> str | None:
    if ended_at is None:
        return None
    start = _parse_utc(started_at)
    end = _parse_utc(ended_at)
    if start is None or end is None:
        return None
    seconds = (end - start).total_seconds()
    if seconds < 0:
        return None
    return f"{seconds:.3f} s"


def _parse_utc(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _protocol_lines(items: tuple[ProtocolCount, ...]) -> list[str]:
    if not items:
        return ["(nenhum)"]
    return [f"{item.protocol}  {item.packet_count}" for item in items]


def _ip_lines(items: tuple[IpTraffic, ...]) -> list[str]:
    if not items:
        return ["(nenhum)"]
    return [f"{index}  {item.ip}  {item.traffic_bytes}" for index, item in enumerate(items, start=1)]
