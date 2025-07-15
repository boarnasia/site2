"""
Domain models for HTML parsing and analysis.
"""

from typing import Dict, Optional

from pydantic import BaseModel


class HTMLStructureAnalysis(BaseModel):
    """Represents the structural analysis of an HTML document."""

    has_main: bool
    has_article: bool
    has_nav: bool
    has_header: bool
    has_footer: bool
    heading_count: Dict[str, int]
    paragraph_count: int
    link_count: int
    image_count: int
    table_count: int
    list_count: int


class HTMLMetadata(BaseModel):
    """Represents the metadata extracted from an HTML document."""

    title: Optional[str]
    description: Optional[str]
    keywords: Optional[str]
    author: Optional[str]
    language: Optional[str]
    meta_tags: Dict[str, str]
    og_tags: Dict[str, str]
