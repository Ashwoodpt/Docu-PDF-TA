from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from src.models.context_model import Document, SharedContext, View, TableData
from pathlib import Path
from src.render.template_engine import TemplateEngine


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class AppState(BaseModel):
    """Global application state"""
    is_save_on_exit: bool = True
    wizard_step: int = 0
    is_editing: bool = False
    logo_urls: Dict[str, str] = Field(default_factory=dict)
    document_list: List[Dict[str, Any]] = Field(default_factory=list)
    show_confirm_success: bool = False
    success_message: str = ""
    embedded_css: str = ""
    templates_dir: Path = TEMPLATES_DIR

    def get_template_engine(self) -> TemplateEngine:
        """Create and return a TemplateEngine instance."""
        return TemplateEngine(self.templates_dir)


class NewPage(BaseModel):
    title: str = ""
    template: str = ""
    view: List[View] = Field(default_factory=list)
    table: List[TableData] = Field(default_factory=list)
    wall_data: List[Dict[str, Any]] = Field(default_factory=list)

class DocumentState(BaseModel):
    """Current document state"""
    document: Optional[Document] = None  # Using proper Document model
    current_page_index: Optional[int] = None
    new_page: NewPage = NewPage()
    new_document_name: str = ""
    shared_context: Optional[SharedContext] = None


class PendingChangesState(BaseModel):
    """Pending changes during editing"""
    page_title: Optional[str] = None
    view: Optional[View] = None  # Using proper View model
    table: Optional[TableData] = None  # Using proper TableData model


class WizardState(Enum):
    """Enum for wizard step states"""
    HOME = 0
    NEW_PAGE = 1
    UPLOAD_FILES = 2

class CurrentActionState(BaseModel):
    """Current action state"""
    action: Optional[str] = None
    name: Optional[str] = None
    index: Optional[int] = None


class AssetManagerState(BaseModel):
    """State for asset manager and its health status"""
    manager: Optional[Any] = None
    is_connected: bool = False
    last_checked: Optional[datetime] = None
    connection_error: Optional[str] = None

