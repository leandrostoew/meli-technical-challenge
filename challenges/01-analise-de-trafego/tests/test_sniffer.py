"""Sniffer com Scapy simulado. Nenhuma interface física e nenhum privilégio."""

import logging
from pathlib import Path

import pytest
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.l2 import ARP

from traffic_analyzer.capture import sniffer
from traffic_analyzer.capture.ingest import ingest
from traffic_analyzer.errors import (
    CaptureFailedError,
    CapturePermissionError,
    InterfaceNotFoundError,
    InvalidArgumentError,
)
from traffic_analyzer.persistence.repository import PacketRepository

_WHEN = "2026-09-29T18:00:00.000Z"


@pytest.fixture
def interfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sniffer, "get_if_list", lambda: ["eth0", "lo"])


def _install_sniff(monkeypatch: pytest.MonkeyPatch, fake) -> None:
    monkeypatch.setattr(sniffer, "sniff", fake)


def test_chama_sniff_com_a_interface_informada(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_sniff(**kwargs):
        seen.update(kwargs)

    _install_sniff(monkeypatch, fake_sniff)

    result = sniffer.capture_packets("eth0", lambda _packet: True)

    assert seen["iface"] == "eth0"
    assert seen["store"] is False
    assert seen["promisc"] is False
    assert seen["timeout"] is None
    assert result.interface == "eth0"
    assert result.interrupted is False


def test_callback_recebe_cada_pacote(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[object] = []

    def on_packet(packet: object) -> bool:
        received.append(packet)
        return True

    def fake_sniff(**kwargs):
        kwargs["prn"]("quadro-1")
        kwargs["stop_filter"]("quadro-1")

    _install_sniff(monkeypatch, fake_sniff)

    result = sniffer.capture_packets("eth0", on_packet, packet_limit=1)

    assert received == ["quadro-1"]
    assert result.packets_seen == 1
    assert result.packets_stored == 1


def test_limite_conta_somente_pacotes_aceitos(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[str] = []

    def on_packet(packet: str) -> bool:
        received.append(packet)
        return packet == "ipv4"

    def fake_sniff(**kwargs):
        for packet in ("arp", "arp", "ipv4", "ipv4", "ipv4"):
            kwargs["prn"](packet)
            if kwargs["stop_filter"](packet):
                break

    _install_sniff(monkeypatch, fake_sniff)

    result = sniffer.capture_packets("eth0", on_packet, packet_limit=2)

    assert received == ["arp", "arp", "ipv4", "ipv4"]
    assert result.packets_stored == 2
    assert result.packets_ignored == 2
    assert result.packets_seen == 4


def test_duracao_vai_para_o_timeout_do_sniff(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_sniff(**kwargs):
        seen.update(kwargs)

    _install_sniff(monkeypatch, fake_sniff)

    sniffer.capture_packets("lo", lambda _packet: True, duration_seconds=2.5)

    assert seen["timeout"] == 2.5
    assert seen["iface"] == "lo"


def test_ctrl_c_encerra_sem_propagar(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sniff(**_kwargs):
        raise KeyboardInterrupt

    _install_sniff(monkeypatch, fake_sniff)

    result = sniffer.capture_packets("eth0", lambda _packet: True)

    assert result.interrupted is True
    assert result.packets_seen == 0


def test_erro_de_captura_nao_e_mascarado(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sniff(**_kwargs):
        raise OSError("socket encerrado")

    _install_sniff(monkeypatch, fake_sniff)

    with pytest.raises(CaptureFailedError) as caught:
        sniffer.capture_packets("eth0", lambda _packet: True)

    assert isinstance(caught.value.__cause__, OSError)


def test_erro_de_permissao(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sniff(**_kwargs):
        raise PermissionError("raw socket")

    _install_sniff(monkeypatch, fake_sniff)

    with pytest.raises(CapturePermissionError):
        sniffer.capture_packets("eth0", lambda _packet: True)


def test_interface_inexistente_nao_chama_sniff(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sniff(**_kwargs):
        raise AssertionError("sniff não deveria ser chamado")

    _install_sniff(monkeypatch, fake_sniff)

    with pytest.raises(InterfaceNotFoundError):
        sniffer.capture_packets("eth9", lambda _packet: True)


def test_erro_do_callback_volta_a_subir(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def on_packet(_packet: object) -> bool:
        raise RuntimeError("falha no banco")

    def fake_sniff(**kwargs):
        kwargs["prn"](object())
        kwargs["stop_filter"](object())

    _install_sniff(monkeypatch, fake_sniff)

    with pytest.raises(RuntimeError, match="falha no banco"):
        sniffer.capture_packets("eth0", on_packet)


def test_quantidade_e_duracao_juntas_sao_recusadas(interfaces: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sniff(**_kwargs):
        raise AssertionError("sniff não deveria ser chamado")

    _install_sniff(monkeypatch, fake_sniff)

    with pytest.raises(InvalidArgumentError):
        sniffer.capture_packets("eth0", lambda _packet: True, packet_limit=1, duration_seconds=1)


def test_interface_vazia_e_recusada(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sniff(**_kwargs):
        raise AssertionError("sniff não deveria ser chamado")

    _install_sniff(monkeypatch, fake_sniff)

    with pytest.raises(InvalidArgumentError):
        sniffer.capture_packets("  ", lambda _packet: True)


def test_log_registra_a_interface_e_omite_o_quadro(
    interfaces: None,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fake_sniff(**kwargs):
        kwargs["prn"]("PAYLOAD-SECRETO")
        kwargs["stop_filter"]("PAYLOAD-SECRETO")

    _install_sniff(monkeypatch, fake_sniff)

    with caplog.at_level(logging.INFO):
        sniffer.capture_packets("eth0", lambda _packet: False, packet_limit=1)

    text = caplog.text
    assert "Início da captura na interface eth0." in text
    assert "Encerramento da captura na interface eth0." in text
    assert "processados=1" in text
    assert "ignorados=1" in text
    assert "PAYLOAD-SECRETO" not in text


def test_fluxo_simulado_grava_no_sqlite(interfaces: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = PacketRepository(tmp_path / "traffic.db")
    capture_id = repository.create_capture("eth0", _WHEN)
    frames = [IP(src="192.0.2.10", dst="198.51.100.20") / TCP(), ARP(), IP(src="192.0.2.11", dst="198.51.100.21") / UDP()]

    def on_packet(packet: object) -> bool:
        return ingest(packet, repository, capture_id)

    def fake_sniff(**kwargs):
        for frame in frames:
            kwargs["prn"](frame)
            if kwargs["stop_filter"](frame):
                break

    _install_sniff(monkeypatch, fake_sniff)

    try:
        result = sniffer.capture_packets("eth0", on_packet)
    finally:
        repository.finish_capture(capture_id, "2026-09-29T18:00:05.000Z")
        repository.close()

    assert result.packets_seen == 3
    assert result.packets_stored == 2
    assert result.packets_ignored == 1
    assert result.interrupted is False

    reopened = PacketRepository(tmp_path / "traffic.db")
    try:
        stored = reopened.list_packets(capture_id)
        capture = reopened.get_last_capture()
    finally:
        reopened.close()

    assert [packet.protocol for packet in stored] == ["TCP", "UDP"]
    assert capture is not None
    assert capture.ended_at == "2026-09-29T18:00:05.000Z"
    assert capture.ignored_non_ip == 1
