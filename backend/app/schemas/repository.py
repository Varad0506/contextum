from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RepositoryCreate(BaseModel):
    """
    Payload for registering + cloning a new repository.

    Note: we deliberately use a plain `str` (not Pydantic's HttpUrl) for
    `url`, because we run our own git-specific validation in the service
    layer (accepts https:// and git@ SSH-style URLs, which HttpUrl rejects).
    """

    url: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        examples=["https://github.com/octocat/Hello-World.git"],
    )
    branch: str | None = Field(
        default=None,
        max_length=255,
        description="Branch to clone. Defaults to the repository's default branch if omitted.",
    )


class RepositoryRead(BaseModel):
    """Response shape returned to clients when reading a Repository row."""

    model_config = ConfigDict(from_attributes=True)  # allows .model_validate(orm_obj)

    id: str
    name: str
    url: str
    local_path: str | None
    default_branch: str
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class RepositoryDeleteResponse(BaseModel):
    """Response returned after successfully deleting a repository."""

    id: str
    message: str
