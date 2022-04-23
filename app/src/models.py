from pydantic import BaseModel


class PingBody(BaseModel):
    url: str


class PingError(BaseModel):
    reason: str


class PingResponse(BaseModel):
    status: str
    payload: str | None
    status_details: PingError | None
