from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict

IsoDateTime = Annotated[datetime, BeforeValidator(datetime.fromisoformat)]


class VirtualTag(StrEnum):
    """Virtual tags.

    Value is the color configuration name.
    """

    ACTIVE = "active"
    BLOCKED = "blocked"
    BLOCKING = "blocking"
    COMPLETED = "completed"
    DELETED = "deleted"
    DUE = "due"
    DUETODAY = "due.today"
    NO_PROJECT = "project.none"
    NO_TAG = "tag.none"
    OVERDUE = "overdue"
    PRIORITY = "priority"
    PROJECT = "project"
    RECURRING = "recurring"
    SCHEDULED = "scheduled"
    TAGGED = "tagged"
    UNTIL = "until"
    WAITING = "waiting"


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
    tags: set[str] = set()
    depends: set[UUID] = set()
    virtual_tags: set[VirtualTag] = set()

    model_config = ConfigDict(extra="allow")

    def __str__(self) -> str:
        return f'Task(id={self.id}, description="{self.description}, virtual_tags=[{",".join(self.virtual_tags)}]")'


@dataclass(frozen=True)
class ContextInfo:
    name: str
    read_filter: str
    is_active: bool = False
