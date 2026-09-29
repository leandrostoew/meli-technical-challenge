"""CLI com sniff simulado. Nenhuma interface física é aberta."""

from pathlib import Path

import pytest
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.l2 import ARP

from traffic_analyzer.capture import sniffer
from traffic_analyzer.cli import main
from traffic_analyzer.errors import DatabaseError
from traffic_analyzer.persistence.repository import PacketRepository


@pytest.fixture
def interfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sniffer, "get_if_list", lambda: ["wlp3s0", "lo"])


def _db(tmp_path: Path) -> str:
    return str(tmp_path / "traffic.db")


def test_argumentos_recusam_quantidade_e_duracao_juntas(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "capture",
            "--interface",
            "wlp3s0",
            "--count",
            "10",
            "--duration",
            "5",
            "--db",
            _db(tmp_path),
        ]
    )

    assert code == 2
    assert "não as duas" in capsys.readouterr().err


def test_argumentos_exigem_a_interface(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["capture", "--count", "1"])

    assert code == 2
    assert "interface" in capsys.readouterr().err.lower()


def test_quantidade_invalida(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["capture", "--interface", "wlp3s0", "--count", "0", "--db", _db(tmp_path)])

    assert code == 2
    assert "quantidade" in capsys.readouterr().err


def test_execucao_normal_com_sniff_simulado(
    interfaces: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    frames = [
        IP(src="192.0.2.10", dst="198.51.100.20") / UDP(),
        ARP(),
        IP(src="192.0.2.11", dst="198.51.100.21") / TCP(),
    ]

    def fake_sniff(**kwargs):
        for frame in frames:
            kwargs["prn"](frame)
            if kwargs["stop_filter"](frame):
                break

    monkeypatch.setattr(sniffer, "sniff", fake_sniff)
    db_path = _db(tmp_path)

    code = main(["capture", "--interface", "wlp3s0", "--count", "2", "--db", db_path])
    captured = capsys.readouterr()

    assert code == 0
    assert "Status: concluída" in captured.out
    assert "Total de pacotes: 2" in captured.out
    assert "UDP  1" in captured.out
    assert "TCP  1" in captured.out
    assert "Ignorados: 1" in captured.out
    assert "IPv4 armazenados" in captured.out

    repository = PacketRepository(db_path)
    try:
        session = repository.get_last_capture()
        packets = repository.list_packets(session.id) if session else []
    finally:
        repository.close()

    assert session is not None
    assert session.interface == "wlp3s0"
    assert session.ended_at is not None
    assert session.ignored_non_ip == 1
    assert len(packets) == 2


def test_interrupcao_preserva_pacotes_e_mostra_relatorio(
    interfaces: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_sniff(**kwargs):
        kwargs["prn"](IP(src="192.0.2.10", dst="8.8.8.8") / TCP())
        raise KeyboardInterrupt

    monkeypatch.setattr(sniffer, "sniff", fake_sniff)
    db_path = _db(tmp_path)

    code = main(["capture", "--interface", "wlp3s0", "--db", db_path])
    captured = capsys.readouterr()

    assert code == 0
    assert "Status: interrompida" in captured.out
    assert "Total de pacotes: 1" in captured.out

    repository = PacketRepository(db_path)
    try:
        session = repository.get_last_capture()
        packets = repository.list_packets(session.id) if session else []
    finally:
        repository.close()

    assert session is not None
    assert session.ended_at is not None
    assert len(packets) == 1


def test_erro_de_permissao_finaliza_a_sessao(
    interfaces: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_sniff(**_kwargs):
        raise PermissionError("raw socket")

    monkeypatch.setattr(sniffer, "sniff", fake_sniff)
    db_path = _db(tmp_path)

    code = main(["capture", "--interface", "wlp3s0", "--count", "10", "--db", db_path])
    captured = capsys.readouterr()

    assert code == 3
    assert "permissão adequada" in captured.err
    assert "sudo" not in captured.err.lower()

    repository = PacketRepository(db_path)
    try:
        session = repository.get_last_capture()
    finally:
        repository.close()

    assert session is not None
    assert session.ended_at is not None
    assert session.ignored_non_ip == 0


def test_interface_inexistente_finaliza_a_sessao(
    interfaces: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_sniff(**_kwargs):
        raise AssertionError("sniff não deveria ser chamado")

    monkeypatch.setattr(sniffer, "sniff", fake_sniff)
    db_path = _db(tmp_path)

    code = main(["capture", "--interface", "eth9", "--count", "1", "--db", db_path])

    assert code == 2
    assert "não encontrada" in capsys.readouterr().err

    repository = PacketRepository(db_path)
    try:
        session = repository.get_last_capture()
    finally:
        repository.close()

    assert session is not None
    assert session.ended_at is not None


def test_erro_de_persistencia_durante_a_captura_finaliza_a_sessao(
    interfaces: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_insert = PacketRepository.insert_packet
    calls = {"n": 0}

    def failing_insert(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise DatabaseError("falha ao gravar o pacote")
        return real_insert(self, *args, **kwargs)

    def fake_sniff(**kwargs):
        kwargs["prn"](IP(src="192.0.2.10", dst="198.51.100.20") / UDP())
        kwargs["prn"](IP(src="192.0.2.11", dst="198.51.100.21") / TCP())

    monkeypatch.setattr(PacketRepository, "insert_packet", failing_insert)
    monkeypatch.setattr(sniffer, "sniff", fake_sniff)
    db_path = _db(tmp_path)

    code = main(["capture", "--interface", "wlp3s0", "--count", "5", "--db", db_path])

    assert code == 4
    assert "falha ao gravar o pacote" in capsys.readouterr().err

    repository = PacketRepository(db_path)
    try:
        session = repository.get_last_capture()
        packets = repository.list_packets(session.id) if session else []
    finally:
        repository.close()

    assert session is not None
    assert session.ended_at is not None
    assert len(packets) == 1


def test_banco_em_diretorio_inexistente(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "ausente" / "traffic.db"

    code = main(["capture", "--interface", "wlp3s0", "--count", "1", "--db", str(missing)])

    assert code == 4
    assert "Diretório do banco inexistente" in capsys.readouterr().err


def test_reexibe_relatorio_gravado(
    interfaces: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_sniff(**kwargs):
        kwargs["prn"](IP(src="192.0.2.10", dst="198.51.100.20") / UDP())
        kwargs["stop_filter"](object())

    monkeypatch.setattr(sniffer, "sniff", fake_sniff)
    db_path = _db(tmp_path)
    assert main(["capture", "--interface", "wlp3s0", "--count", "1", "--db", db_path]) == 0
    capsys.readouterr()

    code = main(["report", "--db", db_path])
    captured = capsys.readouterr()

    assert code == 0
    assert "Total de pacotes: 1" in captured.out
    assert "UDP  1" in captured.out
    assert "Interface: wlp3s0" in captured.out
