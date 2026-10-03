from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class Page[T](BaseModel):
    """Offset pagination. `total` is the count after public filtering."""

    model_config = ConfigDict(extra="forbid")

    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=MAX_PAGE_SIZE)
    offset: int = Field(ge=0)


class FacetCount(BaseModel):
    """How many records carry one facet value: a count, never a ranking."""

    model_config = ConfigDict(extra="forbid")

    value: str
    count: int = Field(ge=0)


class DirectoryPage[T](Page[T]):
    """A server-filtered directory page. `total` counts the rows matching every
    filter; `unfiltered_total` the public directory; `facets` count each value
    over the rows matching the search text."""

    unfiltered_total: int = Field(ge=0)
    facets: dict[str, list[FacetCount]] = Field(default_factory=dict)
