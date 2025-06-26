from pydantic import BaseModel, Field


class UserInput(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str


class UserRecord(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str | None = Field(None)
    id: int


class Credentials(BaseModel):
    email: str
    password: str


class Tokens(BaseModel):
    access: str
    refresh: str


class RefreshToken(BaseModel):
    refresh: str

