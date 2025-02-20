from dataclasses import dataclass


@dataclass
class JobPosting:
    date_updated: int
    url: str
    locations: list[str]
    sponsorship: str
    active: bool
    company_name: str
    title: str
    season: str | None
    source: str | None
    id: str
    date_posted: int
    company_url: str | None
    is_visible: bool
