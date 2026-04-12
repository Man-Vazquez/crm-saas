# Importar aquí todos los modelos garantiza que SQLAlchemy los registre
# en la metadata de Base antes de que Alembic genere las migraciones.
# Si no importas un modelo aquí, Alembic no sabrá que existe.

from app.models.tenant import Tenant, PlanType      # noqa: F401
from app.models.user import User, UserRole          # noqa: F401

# En fases futuras iremos agregando:
# from app.models.ticket import Ticket              # noqa: F401
# from app.models.customer import Customer          # noqa: F401
# from app.models.message import Message            # noqa: F401