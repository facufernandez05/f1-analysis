# Schemas Pydantic para pilotos.

from pydantic import BaseModel


class DriverBase(BaseModel):
    code: str
    full_name: str
    team: str | None = None


class DriverCreate(DriverBase):
    pass


class DriverResponse(DriverBase):
    id: int

    model_config = {"from_attributes": True}
