"""Linha de comando do Challenge 01.

Orquestra a sessão, a captura, a ingestão, a análise e o relatório.
Não eleva privilégio e não chama sudo.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from traffic_analyzer.analysis.analyzer import analyze_capture
from traffic_analyzer.capture.ingest import ingest
from traffic_analyzer.capture.sniffer import CaptureRun, capture_packets
from traffic_analyzer.errors import (
    CaptureFailedError,
    CaptureNotFoundError,
    CapturePermissionError,
    DatabaseError,
    InterfaceNotFoundError,
    InvalidArgumentError,
    PacketRejectedError,
)
from traffic_analyzer.persistence.repository import PacketRepository
from traffic_analyzer.report import render_report

_DEFAULT_DB = "data/traffic.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="traffic-analyzer",
        description="Captura tráfego IPv4 de uma interface e exibe estatísticas.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    capture = commands.add_parser("capture", help="Captura pacotes e exibe o relatório.")
    capture.add_argument("--interface", required=True, help="Nome da interface de rede.")
    capture.add_argument("--count", type=int, help="Máximo de pacotes IPv4 armazenados.")
    capture.add_argument("--duration", type=float, help="Duração máxima, em segundos.")
    capture.add_argument("--db", default=_DEFAULT_DB, help=f"Arquivo SQLite. Padrão: {_DEFAULT_DB}")

    report = commands.add_parser("report", help="Reexibe o relatório de uma captura gravada.")
    report.add_argument("--db", default=_DEFAULT_DB, help=f"Arquivo SQLite. Padrão: {_DEFAULT_DB}")
    report.add_argument("--capture-id", type=int, help="Sessão a exibir. Padrão: a mais recente.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Executa a CLI e devolve o código de saída."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 2
    if args.command == "capture":
        return _run_capture(args)
    return _run_report(args)


def _run_capture(args: argparse.Namespace) -> int:
    limit_error = _validate_capture_limits(args.count, args.duration)
    if limit_error is not None:
        _error(limit_error)
        return 2
    try:
        repository = PacketRepository(args.db)
    except DatabaseError as exc:
        _error(str(exc))
        return 4

    try:
        session_id = repository.create_capture(args.interface, _utc_now())
        try:
            result = capture_packets(
                args.interface,
                lambda packet: ingest(packet, repository, session_id),
                packet_limit=args.count,
                duration_seconds=args.duration,
            )
        finally:
            repository.finish_capture(session_id, _utc_now())
        _emit(repository, result, args.db, session_id)
        return 0
    except InterfaceNotFoundError as exc:
        _error(str(exc))
        return 2
    except InvalidArgumentError as exc:
        _error(str(exc))
        return 2
    except CapturePermissionError as exc:
        _error(
            f"{exc} A captura requer permissão adequada no sistema. "
            "A aplicação não eleva privilégio."
        )
        return 3
    except CaptureFailedError as exc:
        _error(str(exc))
        return 1
    except (DatabaseError, PacketRejectedError, CaptureNotFoundError) as exc:
        _error(str(exc))
        return 4
    finally:
        repository.close()


def _run_report(args: argparse.Namespace) -> int:
    try:
        repository = PacketRepository(args.db)
    except DatabaseError as exc:
        _error(str(exc))
        return 4
    try:
        if args.capture_id is None:
            session = repository.get_last_capture()
        else:
            session = repository.get_capture(args.capture_id)
        if session is None:
            _error("Nenhuma captura encontrada nesse banco.")
            return 2
        stats = analyze_capture(repository, session.id)
        text = render_report(
            stats=stats,
            session=session,
            db_path=str(Path(args.db)),
            packets_seen=stats.total_packets + session.ignored_non_ip,
            packets_stored=stats.total_packets,
            packets_ignored=session.ignored_non_ip,
            interrupted=False,
        )
        print(text)
        return 0
    except DatabaseError as exc:
        _error(str(exc))
        return 4
    finally:
        repository.close()


def _emit(repository: PacketRepository, result: CaptureRun, db_path: str, session_id: int) -> None:
    session = repository.get_capture(session_id)
    if session is None:
        raise CaptureNotFoundError(f"Captura {session_id} não encontrada.")
    stats = analyze_capture(repository, session_id)
    print(
        render_report(
            stats=stats,
            session=session,
            db_path=str(Path(db_path)),
            packets_seen=result.packets_seen,
            packets_stored=result.packets_stored,
            packets_ignored=result.packets_ignored,
            interrupted=result.interrupted,
        )
    )


def _validate_capture_limits(count: int | None, duration: float | None) -> str | None:
    if count is not None and duration is not None:
        return "Informe quantidade ou duração, não as duas."
    if count is not None and count <= 0:
        return "A quantidade precisa ser um inteiro maior que zero."
    if duration is not None and duration <= 0:
        return "A duração precisa ser um número de segundos maior que zero."
    return None


def _utc_now() -> str:
    text = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    return text.replace("+00:00", "Z")


def _error(message: str) -> None:
    print(f"erro: {message}", file=sys.stderr)
