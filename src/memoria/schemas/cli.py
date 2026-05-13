from pydantic import BaseModel


class CommandResult(BaseModel):
    ok: bool
    data: object
