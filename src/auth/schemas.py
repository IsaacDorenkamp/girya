from pydantic import BaseModel, Field


class UserInput(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str


class User(BaseModel):
    email: str
    first_name: str
    last_name: str
    id: int
    auth_group: str


class UserRecord(User):
    password: str


class Credentials(BaseModel):
    email: str
    password: str


class Tokens(BaseModel):
    access: str
    refresh: str


class RefreshToken(BaseModel):
    refresh: str

