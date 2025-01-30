from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CommitFile(BaseModel):
    filename: str
    additions: int
    deletions: int


class Commit(BaseModel):
    hash: str
    date: str
    author: str
    message: str
    files: List[CommitFile]
    time_prompting: Optional[str] = None


class ChartConfig(BaseModel):
    output_dir: str = Field(..., description="Directory where charts will be saved")
    format: str = Field(default="html", description="Output format (html, png, pdf)")


class ContributionStats(BaseModel):
    date: datetime
    ai_commits: int
    total_commits: int
    human_commits: int
    ai_lines_added: int
    ai_lines_deleted: int
    ai_total_changes: int
    human_lines_added: int
    human_lines_deleted: int
    human_total_changes: int
    percentage_total_changes_ai: float
    time_prompting_S: int
    time_prompting_M: int
    time_prompting_L: int
    time_prompting_XL: int
