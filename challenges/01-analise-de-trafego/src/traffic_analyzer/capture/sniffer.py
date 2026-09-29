"""Captura pacotes de uma interface com Scapy.

Este módulo só lê a interface e entrega cada quadro ao callback. Não grava
SQL e não calcula estatísticas. Quem chama o callback, em geral o `ingest`,
decide o que persistir.

`packet_limit` conta callbacks que devolvem True (pacote aceito). Quadros
recusados, com retorno False, não consomem esse limite. Duração e quantidade
não são usadas juntas: a CLI aprovada trata os dois limites como exclusivos.
"""

from __future__ import annotations

import errno
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from scapy.interfaces import get_if_list
from scapy.sendrecv import sniff

from traffic_analyzer.errors import (
    CaptureFailedError,
    CapturePermissionError,
    InterfaceNotFoundError,
    InvalidArgumentError,
)

logger = logging.getLogger(__name__)

PacketCallback = Callable[[Any], bool | None]


@dataclass(frozen=True)
class CaptureRun:
    """Resumo da leitura. Não inclui conteúdo de pacote."""

    interface: str
    packets_seen: int
    packets_stored: int
    packets_ignored: int
    interrupted: bool


def capture_packets(
    interface: str,
    on_packet: PacketCallback,
    *,
    packet_limit: int | None = None,
    duration_seconds: float | None = None,
) -> CaptureRun:
    """Lê a interface até o limite, a duração ou Ctrl+C.

    Ctrl+C encerra a leitura e devolve `interrupted=True`. A exceção não sobe,
    para quem chamou poder fechar a sessão no SQLite em seguida.
    """
    name = _validate_interface(interface)
    _validate_limits(packet_limit, duration_seconds)

    seen = 0
    stored = 0
    ignored = 0
    interrupted = False
    processing_error: BaseException | None = None

    def _on_each(packet: Any) -> None:
        nonlocal seen, stored, ignored, processing_error
        seen += 1
        try:
            accepted = on_packet(packet)
        except BaseException as exc:
            processing_error = exc
            return None
        if accepted is True:
            stored += 1
        elif accepted is False:
            ignored += 1
        return None

    def _stop(_packet: Any) -> bool:
        if processing_error is not None:
            return True
        if packet_limit is None:
            return False
        return stored >= packet_limit

    logger.info("Início da captura na interface %s.", name)
    try:
        sniff(
            iface=name,
            prn=_on_each,
            stop_filter=_stop,
            timeout=duration_seconds,
            store=False,
            promisc=False,
            chainCC=True,
        )
    except KeyboardInterrupt:
        interrupted = True
        logger.info("Captura interrompida por Ctrl+C na interface %s.", name)
    except Exception as exc:
        logger.error("Erro de captura na interface %s: %s", name, exc)
        if _is_permission_error(exc):
            raise CapturePermissionError(
                f"Sem permissão para capturar na interface {name}."
            ) from exc
        raise CaptureFailedError(f"Falha ao capturar na interface {name}.") from exc
    finally:
        logger.info(
            "Encerramento da captura na interface %s. "
            "processados=%s armazenados=%s ignorados=%s interrompida=%s",
            name,
            seen,
            stored,
            ignored,
            interrupted,
        )

    if processing_error is not None:
        logger.error("Erro ao processar pacote na interface %s.", name)
        raise processing_error

    return CaptureRun(
        interface=name,
        packets_seen=seen,
        packets_stored=stored,
        packets_ignored=ignored,
        interrupted=interrupted,
    )


def _validate_interface(interface: str) -> str:
    if not isinstance(interface, str) or not interface.strip():
        raise InvalidArgumentError("A interface é obrigatória.")
    name = interface.strip()
    if name not in get_if_list():
        logger.error("Interface inexistente: %s.", name)
        raise InterfaceNotFoundError(f"Interface não encontrada: {name}.")
    return name


def _validate_limits(packet_limit: int | None, duration_seconds: float | None) -> None:
    if packet_limit is not None and duration_seconds is not None:
        raise InvalidArgumentError("Informe quantidade ou duração, não as duas.")
    if packet_limit is not None and (
        isinstance(packet_limit, bool) or not isinstance(packet_limit, int) or packet_limit <= 0
    ):
        raise InvalidArgumentError("A quantidade de pacotes precisa ser um inteiro maior que zero.")
    if duration_seconds is not None and (
        isinstance(duration_seconds, bool)
        or not isinstance(duration_seconds, (int, float))
        or duration_seconds <= 0
    ):
        raise InvalidArgumentError("A duração precisa ser um número de segundos maior que zero.")


def _is_permission_error(exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return True
    return isinstance(exc, OSError) and exc.errno in (errno.EPERM, errno.EACCES)
