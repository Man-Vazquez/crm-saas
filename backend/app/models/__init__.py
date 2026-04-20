# Importar aquí todos los modelos garantiza que SQLAlchemy los registre
# en la metadata de Base antes de que Alembic genere las migraciones.
# Si no importas un modelo aquí, Alembic no sabrá que existe.

from app.models.tenant import Tenant
from app.models.user import User
from app.models.customer import Customer
from app.models.ticket_config import TicketType, TicketSubtype, TicketStatus
from app.models.ticket import Ticket
from app.models.message import Message
from app.models.channel import Channel
from app.models.agent_channel import AgentChannel
from app.models.ticket_counter import TicketCounter

# En fases futuras iremos agregando:
# from app.models.ticket import Ticket              # noqa: F401
# from app.models.customer import Customer          # noqa: F401
# from app.models.message import Message            # noqa: F401