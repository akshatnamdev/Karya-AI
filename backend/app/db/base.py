"""
Karya AI - Base module for Alembic
Imports all models so Alembic can detect them
"""
from app.db.database import Base

# Import all models here (we'll add them as we create)
from app.models.user import User
from app.models.business import Business
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory, StockMovement
from app.models.order import Order, OrderItem
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.conversation import Conversation
from app.models.ai_action import AIAction
from app.models.embedding import Embedding
from app.models.audit_log import AuditLog
from app.models.support import SupportTicket, SupportMessage  # noqa