# Import all models so Alembic can discover them
from app.modules.assets.models import Plant, Area, Asset  # noqa: F401
from app.modules.signals.models import Signal  # noqa: F401
from app.modules.edge_nodes.models import EdgeNode  # noqa: F401
from app.modules.events.models import StateEvent, DowntimeEvent, ProductionEvent  # noqa: F401
