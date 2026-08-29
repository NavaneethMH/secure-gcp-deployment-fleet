from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubPushEvent:
    event_id: str
    repository: str
    repository_owner: str
    ref: str
    branch: str
    commit_sha: str
    installation_id: int | None = None
