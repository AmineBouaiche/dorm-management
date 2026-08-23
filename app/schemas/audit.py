from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int
    action: str
    resource_type: str
    resource_id: int
    request_id: str
    details: dict[str, Any] | None
    created_at: datetime
