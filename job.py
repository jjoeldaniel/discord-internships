from dataclasses import dataclass


@dataclass
class JobPosting:
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
