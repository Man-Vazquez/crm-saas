from app.channels.base import BaseChannel

# Mapa de channel_type → clase del adapter
# Se puebla en main.py al arrancar la app
_registry: dict[str, type[BaseChannel]] = {}


def register_channel(channel_type: str, cls: type[BaseChannel]) -> None:
    """Registra un adapter de canal."""
    _registry[channel_type] = cls


def get_channel_class(channel_type: str) -> type[BaseChannel] | None:
    """Devuelve la clase del adapter para un channel_type dado."""
    return _registry.get(channel_type)