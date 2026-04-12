from contextvars import ContextVar
from uuid import UUID

# ── ContextVar ────────────────────────────────────────────────────────
# Una variable que almacena un valor distinto por cada corrutina async.
# Si request A setea _current_tenant_id = "uuid-A"
# y request B setea _current_tenant_id = "uuid-B",
# cada uno lee su propio valor sin interferencia.
# Es el equivalente async de un thread-local.
_current_tenant_id: ContextVar[UUID | None] = ContextVar(
    "_current_tenant_id",
    default=None,      # None si no hay tenant (rutas públicas)
)


def set_tenant_id(tenant_id: UUID) -> None:
    """Llamado por el middleware al inicio de cada request autenticado."""
    _current_tenant_id.set(tenant_id)


def get_tenant_id() -> UUID:
    """
    Llamado por los repositories antes de cada query.
    Lanza excepción si no hay tenant — esto es intencional.
    Si un repository intenta hacer un query sin tenant_id,
    significa que hay un bug en el flujo de autenticación.
    """
    tenant_id = _current_tenant_id.get()
    if tenant_id is None:
        raise RuntimeError(
            "tenant_id no está disponible en el contexto actual. "
            "¿El endpoint tiene autenticación configurada?"
        )
    return tenant_id


def get_tenant_id_optional() -> UUID | None:
    """Para rutas que pueden o no tener tenant (ej: health checks)."""
    return _current_tenant_id.get()