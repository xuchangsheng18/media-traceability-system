from dataclasses import dataclass
from typing import TypeAlias, Union
from uuid import UUID

JsonValue: TypeAlias = Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]]


@dataclass(frozen=True)
class Actor:
    user_id: UUID
    org_id: UUID


@dataclass(frozen=True)
class Scope:
    actor: Actor
    case_id: UUID


@dataclass(frozen=True)
class ObjectRef:
    object_id: UUID
    version_id: str
    sha256: str


@dataclass(frozen=True)
class ResultKey:
    task_id: UUID
    run_version: int
    result_version: int
