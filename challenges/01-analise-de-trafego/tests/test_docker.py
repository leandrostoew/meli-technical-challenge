"""Contrato do Docker, sem daemon e sem interface de rede."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_dockerfile_usa_a_cli_existente() -> None:
    text = _text("Dockerfile")

    assert "python:3.12" in text
    assert "scapy==2.7.0" in text
    assert 'ENTRYPOINT ["python", "-m", "traffic_analyzer"]' in text
    assert "sudo" not in text.lower()
    assert "wlp3s0" not in text
    assert "--interface" not in text
    assert "privileged" not in text.lower()


def test_compose_publica_rede_do_host_capabilities_e_volume() -> None:
    text = _text("docker-compose.yml")

    assert "network_mode: host" in text
    assert "- NET_RAW" in text
    assert "- NET_ADMIN" in text
    assert "privileged: false" in text
    assert "privileged: true" not in text
    assert "./data:/app/data" in text
    assert "sudo" not in text.lower()
    assert "wlp3s0" not in text
    assert "--interface" not in text


def test_sniffer_nao_e_alterado_pelo_docker() -> None:
    sniffer = (ROOT / "src" / "traffic_analyzer" / "capture" / "sniffer.py").read_text(encoding="utf-8")

    assert "promisc=False" in sniffer
