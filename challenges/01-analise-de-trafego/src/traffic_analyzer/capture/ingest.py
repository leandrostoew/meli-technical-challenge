"""Decide se um quadro já lido é gravado ou só contado.

Não abre interface e não chama `sniff`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from traffic_analyzer.parsing.parser import parse_ipv4
from traffic_analyzer.persistence.repository import PacketRepository


def ingest(
    packet: Any,
    repository: PacketRepository,
    capture_id: int,
    *,
    captured_at: datetime | None = None,
) -> bool:
    """Grava o IPv4. Sem camada IPv4, incrementa `ignored_non_ip` e segue.

    Devolve True quando uma linha foi inserida em `packets`.
    """
    parsed = parse_ipv4(packet, captured_at=captured_at)
    if parsed is None:
        repository.increment_ignored_non_ip(capture_id)
        return False

    repository.insert_packet(
        capture_id=capture_id,
        captured_at=parsed.captured_at,
        src_ip=parsed.src_ip,
        dst_ip=parsed.dst_ip,
        protocol=parsed.protocol,
        size_bytes=parsed.size_bytes,
    )
    return True
