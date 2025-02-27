from dataclasses import dataclass


@dataclass
class JobPostingCvrve:
    company_name: str
    title: str
    locations: list[str]
    date_posted: int
    terms: list[str]
    active: bool
    url: str
    is_visible: bool
    source: str | None
    company_url: str | None
    date_updated: int
    id: str
    sponsorship: str


@dataclass
class JobPostingSimplify:
    source: str | None
    company_name: str
    id: str
    title: str
    active: bool
    terms: list[str]
    date_updated: int
    url: str
    locations: list[str]
    company_url: str | None
    is_visible: bool
    date_posted: int
    sponsorship: str
