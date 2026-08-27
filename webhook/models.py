from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GitHubPushEvent:
    event_id: str
    repository: str
    repository_owner: str
    ref: str
    branch: str
    commit_sha: str
    installation_id: Optional[int] = None
