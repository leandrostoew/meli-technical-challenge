"""Repositório SQLite das sessões e dos pacotes IPv4.

O schema guarda metadados. O quadro bruto não é persistido.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from traffic_analyzer.errors import (
    CaptureNotFoundError,
    DatabaseError,
    InvalidArgumentError,
    PacketRejectedError,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS captures (
    id               INTEGER PRIMARY KEY,
    interface        TEXT    NOT NULL,
    started_at       TEXT    NOT NULL,
    ended_at         TEXT,
    ignored_non_ip   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS packets (
    id            INTEGER PRIMARY KEY,
    capture_id    INTEGER NOT NULL REFERENCES captures(id),
    captured_at   TEXT    NOT NULL,
    src_ip        TEXT    NOT NULL,
    dst_ip        TEXT    NOT NULL,
    protocol      TEXT    NOT NULL,
    size_bytes    INTEGER NOT NULL CHECK (size_bytes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_packets_capture_protocol
    ON packets (capture_id, protocol);
CREATE INDEX IF NOT EXISTS idx_packets_capture_src
    ON packets (capture_id, src_ip);
CREATE INDEX IF NOT EXISTS idx_packets_capture_dst
    ON packets (capture_id, dst_ip);
"""


@dataclass(frozen=True)
class Capture:
    """Uma execução da captura."""

    id: int
    interface: str
    started_at: str
    ended_at: str | None
    ignored_non_ip: int


@dataclass(frozen=True)
class StoredPacket:
    """Uma linha de `packets`."""

    id: int
    capture_id: int
    captured_at: str
    src_ip: str
    dst_ip: str
    protocol: str
    size_bytes: int


class PacketRepository:
    """Abre um arquivo SQLite, cria o schema e grava sessões e pacotes."""

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._conn = self._connect()
        self._initialize()

    def __enter__(self) -> PacketRepository:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def create_capture(self, interface: str, started_at: str) -> int:
        """Cria a sessão e devolve o id. A interface vem do chamador, não de um valor fixo."""
        interface = _required_text(interface, "A interface é obrigatória.")
        started_at = _required_text(started_at, "O início da captura é obrigatório.")
        cursor = self._conn.execute(
            "INSERT INTO captures (interface, started_at) VALUES (?, ?)",
            (interface, started_at),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def finish_capture(self, capture_id: int, ended_at: str) -> None:
        """Grava o fim da sessão. Não apaga os pacotes já inseridos."""
        ended_at = _required_text(ended_at, "O fim da captura é obrigatório.")
        cursor = self._conn.execute(
            "UPDATE captures SET ended_at = ? WHERE id = ?",
            (ended_at, capture_id),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            raise CaptureNotFoundError(f"Captura {capture_id} não encontrada.")

    def insert_packet(
        self,
        capture_id: int,
        captured_at: str,
        src_ip: str,
        dst_ip: str,
        protocol: str,
        size_bytes: int,
    ) -> int:
        """Insere um IPv4 já extraído. Devolve o id da linha."""
        captured_at = _required_text(captured_at, "O horário do pacote é obrigatório.")
        src_ip = _required_text(src_ip, "O IP de origem é obrigatório.")
        dst_ip = _required_text(dst_ip, "O IP de destino é obrigatório.")
        protocol = _required_text(protocol, "O protocolo é obrigatório.")
        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
            raise PacketRejectedError("size_bytes precisa ser um inteiro maior ou igual a zero.")

        try:
            cursor = self._conn.execute(
                """
                INSERT INTO packets (
                    capture_id, captured_at, src_ip, dst_ip, protocol, size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (capture_id, captured_at, src_ip, dst_ip, protocol, size_bytes),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            self._conn.rollback()
            message = str(exc).lower()
            if "foreign key" in message:
                raise CaptureNotFoundError(f"Captura {capture_id} não encontrada.") from exc
            raise PacketRejectedError("O pacote viola o schema de packets.") from exc
        return int(cursor.lastrowid)

    def increment_ignored_non_ip(self, capture_id: int) -> None:
        """Soma um quadro sem IPv4 na sessão. Não cria linha em `packets`."""
        cursor = self._conn.execute(
            "UPDATE captures SET ignored_non_ip = ignored_non_ip + 1 WHERE id = ?",
            (capture_id,),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            raise CaptureNotFoundError(f"Captura {capture_id} não encontrada.")

    def list_packets(self, capture_id: int) -> list[StoredPacket]:
        """Pacotes da sessão, na ordem de inserção."""
        rows = self._conn.execute(
            """
            SELECT id, capture_id, captured_at, src_ip, dst_ip, protocol, size_bytes
            FROM packets
            WHERE capture_id = ?
            ORDER BY id ASC
            """,
            (capture_id,),
        ).fetchall()
        return [_packet_from_row(row) for row in rows]

    def get_last_capture(self) -> Capture | None:
        """Sessão de maior id, ou `None` se o banco ainda não tem captura."""
        row = self._conn.execute(
            """
            SELECT id, interface, started_at, ended_at, ignored_non_ip
            FROM captures
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return _capture_from_row(row)

    def get_capture(self, capture_id: int) -> Capture | None:
        """Uma sessão pelo id, ou `None` se ela não existe."""
        row = self._conn.execute(
            """
            SELECT id, interface, started_at, ended_at, ignored_non_ip
            FROM captures
            WHERE id = ?
            """,
            (capture_id,),
        ).fetchone()
        if row is None:
            return None
        return _capture_from_row(row)

    def _connect(self) -> sqlite3.Connection:
        parent = self._path.parent
        if str(parent) not in ("", ".") and not parent.exists():
            raise DatabaseError(f"Diretório do banco inexistente: {parent}")
        try:
            connection = sqlite3.connect(self._path)
        except sqlite3.Error as exc:
            raise DatabaseError("Não foi possível abrir o banco.") from exc
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        try:
            self._conn.executescript(_SCHEMA)
        except sqlite3.Error as exc:
            raise DatabaseError("Não foi possível criar as tabelas.") from exc
        self._conn.execute("PRAGMA foreign_keys = ON")


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidArgumentError(message)
    return value.strip()


def _capture_from_row(row: sqlite3.Row) -> Capture:
    return Capture(
        id=int(row["id"]),
        interface=str(row["interface"]),
        started_at=str(row["started_at"]),
        ended_at=None if row["ended_at"] is None else str(row["ended_at"]),
        ignored_non_ip=int(row["ignored_non_ip"]),
    )


def _packet_from_row(row: sqlite3.Row) -> StoredPacket:
    return StoredPacket(
        id=int(row["id"]),
        capture_id=int(row["capture_id"]),
        captured_at=str(row["captured_at"]),
        src_ip=str(row["src_ip"]),
        dst_ip=str(row["dst_ip"]),
        protocol=str(row["protocol"]),
        size_bytes=int(row["size_bytes"]),
    )
