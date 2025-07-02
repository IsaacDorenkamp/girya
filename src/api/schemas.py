import datetime
from typing import Any

from pydantic import BaseModel, model_validator


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


class Workout(BaseModel):
    at: datetime.datetime
    slug: str
    split: Split
    user_id: int

    @model_validator(mode="before")
    @classmethod
    def generate_slug(cls, data: Any):
        if isinstance(data, dict):
            if (
                "slug" not in data and
                "at" in data and
                isinstance(data["at"], datetime.datetime)
            ):
                slug = data["at"].strftime("%Y%m%d-%H%M%S-%f") + f"-{data['user_id']}"
                data["slug"] = slug

        return data


class WorkoutInput(BaseModel):
    at: datetime.datetime
    split: str  # identified by slugs

