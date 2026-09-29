"""Erros da aplicação, em especial captura, interface e permissão."""


class TrafficAnalyzerError(Exception):
    """Base dos erros previstos da aplicação."""


class InvalidArgumentError(TrafficAnalyzerError):
    """Argumento obrigatório ausente, vazio ou de tipo inválido."""


class CaptureNotFoundError(TrafficAnalyzerError):
    """A sessão de captura informada não existe."""


class PacketRejectedError(TrafficAnalyzerError):
    """O pacote não satisfaz o modelo gravado em `packets`."""


class DatabaseError(TrafficAnalyzerError):
    """O arquivo SQLite não pôde ser aberto ou preparado."""


class InterfaceNotFoundError(TrafficAnalyzerError):
    """A interface informada não existe na lista vista pelo Scapy."""


class CapturePermissionError(TrafficAnalyzerError):
    """O processo não tem permissão para abrir o socket de captura."""


class CaptureFailedError(TrafficAnalyzerError):
    """A captura falhou por um erro que não é de permissão nem de interface."""
