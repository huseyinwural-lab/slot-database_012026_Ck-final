from app.core.database import SQLModel
from app.models import vip_models
print("VIP Tables:", [t for t in SQLModel.metadata.tables.keys() if "vip" in t or "loyalty" in t])
