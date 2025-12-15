from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from src.models.enums import ViewType
from uuid import uuid4
from src.models.page_model import Component





class View(BaseModel):
    side: ViewType
    image: str  # SVG content as string
    wall_image: str  # SVG content as string
    pano: str  # Path to panorama image
    wall_data: Optional[Dict[str, Any]] = None  # Wall data as dictionary

    def __eq__(self, other):
        if not isinstance(other, View):
            return False
        return (
            self.side == other.side and
            self.image == other.image and
            self.wall_image == other.wall_image and
            self.pano == other.pano and
            self.wall_data == other.wall_data
        )

    def __ne__(self, other):
        return not self.__eq__(other)



class TableData(BaseModel):
    headers: List[str]
    data: List[Dict[str, Any]]  # List of dictionaries representing rows

    def __eq__(self, other):
        if not isinstance(other, TableData):
            return False
        return (
            self.headers == other.headers and
            self.data == other.data
        )

    def __ne__(self, other):
        return not self.__eq__(other)


class PageContext(BaseModel):
    """
    Model for page context data that contains information specific to a page.
    """
    page_title: str
    generation_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    page_number: int = 1

    # Page-specific data
    views: List[View] = Field(default_factory=list)
    table_data: Optional[TableData] = None

    # PDF and preview URLs
    pdf_url: Optional[str] = None
    preview_url: Optional[str] = None

    # Additional context fields that might be needed
    extra_context: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        # Allow extra fields in case additional context data is added
        extra = "allow"
        # Enable arbitrary types for complex objects if needed
        arbitrary_types_allowed = True


class SharedContext(BaseModel):
    """
    Model for shared context data that's consistent across all pages in a document.
    """
    embedded_css: Optional[str] = None
    total_pages: int = 1
    document_name: str
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    address_line: str
    powered_by_logo_url: str
    header_logo_url: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        arbitrary_types_allowed = True


class Document(BaseModel):
    """
    Model for a document that contains multiple pages and shared context.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    shared_context: SharedContext
    pages: List[PageContext] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def add_page(self, page_context: PageContext):
        """Add a page to the document and update page numbers."""
        page_context.page_number = len(self.pages) + 1
        self.pages.append(page_context)
        self.shared_context.total_pages = len(self.pages)
        self.updated_at = datetime.now().isoformat()
        return self

    def delete_page(self, page_index: int):
        """Delete a page from the document by index and update page numbers."""
        if 0 <= page_index <= len(self.pages):
            new_pages = self.pages.copy()
            del new_pages[page_index]
            # Update page numbers for remaining pages
            for i in range(len(new_pages)):
                new_pages[i].page_number = i + 1

            self.shared_context.total_pages = len(self.pages)
            self.updated_at = datetime.now().isoformat()
            self.pages = new_pages
        else:
            raise IndexError(f"Page index {page_index} is out of range. Document has {len(self.pages)} pages.")
        return self

    def update_shared_context(self, **kwargs):
        """Update shared context values."""
        for key, value in kwargs.items():
            if hasattr(self.shared_context, key):
                setattr(self.shared_context, key, value)
        self.updated_at = datetime.now().isoformat()
        return self

    def to_dict(self):
        """
        Convert the Document instance to a dictionary representation.
        
        Returns:
            dict: Dictionary representation of the Document
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data):
        """
        Create a Document instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing document data
            
        Returns:
            Document: A new Document instance
        """
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str):
        """Create a Document instance from a JSON string."""
        import json
        data = json.loads(json_str)
        return cls(**data)