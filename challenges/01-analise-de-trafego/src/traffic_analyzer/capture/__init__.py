"""Entrada dos pacotes: leitura na interface e ingestão."""

from traffic_analyzer.capture.sniffer import CaptureRun, capture_packets

__all__ = ["CaptureRun", "capture_packets"]
