"""Repositório SQLite em arquivo temporário. Nenhuma interface é aberta."""

from pathlib import Path

import pytest

from traffic_analyzer.errors import (
    CaptureNotFoundError,
    DatabaseError,
    InvalidArgumentError,
    PacketRejectedError,
)
from traffic_analyzer.persistence.repository import PacketRepository


@pytest.fixture
def repository(tmp_path: Path):
    repo = PacketRepository(tmp_path / "traffic.db")
    yield repo
    repo.close()


def test_schema_tem_tabelas_chave_estrangeira_e_indices(repository: PacketRepository) -> None:
    foreign_keys = repository._conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert foreign_keys == 1

    names = {
        row[0]
        for row in repository._conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
        ).fetchall()
    }
    assert "captures" in names
    assert "packets" in names
    assert "idx_packets_capture_protocol" in names
    assert "idx_packets_capture_src" in names
    assert "idx_packets_capture_dst" in names

    packets_sql = repository._conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'packets'"
    ).fetchone()[0]
    assert "REFERENCES captures" in packets_sql
    assert "size_bytes >= 0" in packets_sql


def test_banco_vazio_nao_tem_ultima_captura(repository: PacketRepository) -> None:
    assert repository.get_last_capture() is None


def test_cria_finaliza_e_recupera_a_ultima_captura(repository: PacketRepository) -> None:
    first_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")
    second_id = repository.create_capture("eth1", "2026-09-29T18:05:00.000Z")

    repository.finish_capture(first_id, "2026-09-29T18:01:00.000Z")

    last = repository.get_last_capture()
    assert last is not None
    assert last.id == second_id
    assert last.interface == "eth1"
    assert last.started_at == "2026-09-29T18:05:00.000Z"
    assert last.ended_at is None
    assert last.ignored_non_ip == 0

    repository.finish_capture(second_id, "2026-09-29T18:06:00.000Z")
    finished = repository.get_last_capture()
    assert finished is not None
    assert finished.ended_at == "2026-09-29T18:06:00.000Z"


def test_insere_e_lista_pacotes_da_sessao(repository: PacketRepository) -> None:
    capture_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")
    other_id = repository.create_capture("eth1", "2026-09-29T18:05:00.000Z")

    repository.insert_packet(
        capture_id=capture_id,
        captured_at="2026-09-29T18:00:01.000Z",
        src_ip="192.0.2.10",
        dst_ip="198.51.100.20",
        protocol="TCP",
        size_bytes=60,
    )
    repository.insert_packet(
        capture_id=other_id,
        captured_at="2026-09-29T18:05:01.000Z",
        src_ip="192.0.2.11",
        dst_ip="198.51.100.21",
        protocol="UDP",
        size_bytes=40,
    )

    packets = repository.list_packets(capture_id)
    assert len(packets) == 1
    assert packets[0].src_ip == "192.0.2.10"
    assert packets[0].dst_ip == "198.51.100.20"
    assert packets[0].protocol == "TCP"
    assert packets[0].size_bytes == 60
    assert packets[0].capture_id == capture_id


def test_incrementa_ignorados_sem_gravar_pacote(repository: PacketRepository) -> None:
    capture_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")

    repository.increment_ignored_non_ip(capture_id)
    repository.increment_ignored_non_ip(capture_id)

    capture = repository.get_last_capture()
    assert capture is not None
    assert capture.ignored_non_ip == 2
    assert repository.list_packets(capture_id) == []


def test_pacote_sem_sessao_e_recusado(repository: PacketRepository) -> None:
    with pytest.raises(CaptureNotFoundError):
        repository.insert_packet(
            capture_id=999,
            captured_at="2026-09-29T18:00:01.000Z",
            src_ip="192.0.2.10",
            dst_ip="198.51.100.20",
            protocol="TCP",
            size_bytes=40,
        )


def test_tamanho_negativo_e_recusado(repository: PacketRepository) -> None:
    capture_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")
    with pytest.raises(PacketRejectedError):
        repository.insert_packet(
            capture_id=capture_id,
            captured_at="2026-09-29T18:00:01.000Z",
            src_ip="192.0.2.10",
            dst_ip="198.51.100.20",
            protocol="TCP",
            size_bytes=-1,
        )


def test_ip_vazio_e_recusado(repository: PacketRepository) -> None:
    capture_id = repository.create_capture("eth0", "2026-09-29T18:00:00.000Z")
    with pytest.raises(InvalidArgumentError):
        repository.insert_packet(
            capture_id=capture_id,
            captured_at="2026-09-29T18:00:01.000Z",
            src_ip="  ",
            dst_ip="198.51.100.20",
            protocol="TCP",
            size_bytes=40,
        )


def test_interface_vazia_e_recusada(repository: PacketRepository) -> None:
    with pytest.raises(InvalidArgumentError):
        repository.create_capture("  ", "2026-09-29T18:00:00.000Z")


def test_operacao_em_captura_inexistente_falha(repository: PacketRepository) -> None:
    with pytest.raises(CaptureNotFoundError):
        repository.finish_capture(404, "2026-09-29T18:01:00.000Z")
    with pytest.raises(CaptureNotFoundError):
        repository.increment_ignored_non_ip(404)


def test_diretorio_do_banco_inexistente_falha(tmp_path: Path) -> None:
    missing = tmp_path / "ainda-nao-existe" / "traffic.db"
    with pytest.raises(DatabaseError):
        PacketRepository(missing)
