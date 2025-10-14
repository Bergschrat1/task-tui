from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict

IsoDateTime = Annotated[datetime, BeforeValidator(datetime.fromisoformat)]


class Status(StrEnum):
    PENDING = auto()
    DELETED = auto()
    COMPLETED = auto()
    WAITING = auto()
    RECURRING = auto()


class Annotation(BaseModel):
    entry: IsoDateTime | None = None
    description: str


class Task(BaseModel):
    id: int
    description: str
    entry: IsoDateTime
    modified: IsoDateTime
    due: IsoDateTime | None = None
    start: IsoDateTime | None = None
    scheduled: IsoDateTime | None = None
    wait: IsoDateTime | None = None
    end: IsoDateTime | None = None
    until: IsoDateTime | None = None
    recur: str | None = None
    project: str | None = None
    status: Status
    uuid: UUID
    urgency: float
    annotations: list[Annotation] | None = None
    priority: str | None = None
    tags: list[str] | None = None
    depends: list[UUID] = list()

    model_config = ConfigDict(extra="allow")
