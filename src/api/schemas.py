from pydantic import BaseModel


class PartialLift(BaseModel):
    name: str
    slug: str


class Lift(PartialLift):
    id: int


class BaseSplit(BaseModel):
    name: str
    slug: str


class SplitInput(BaseSplit):
    lifts: list[str]  # identified by slugs


class PartialSplit(BaseSplit):
    lifts: list[Lift]


class Split(PartialSplit):
    id: int

