import streamlit as st
from typing import Any, Optional, Dict, List
from datetime import datetime
from ..models.state_models import AppState, CurrentActionState, DocumentState, PendingChangesState, AssetManagerState, NewPage
from src.models.context_model import Document, SharedContext
from src.core.asset_factory import get_default_asset_manager
from src.core.asset_manager import AssetType
from pathlib import Path
import json

static_path = Path(__file__).parent / "static"

class StateManager:
    """Centralized state manager for the application"""

    # State key constants
    APP_STATE_KEY = "state_manager"
    DOCUMENT_STATE_KEY = "document_state"
    PENDING_CHANGES_KEY = "pending_changes_state"
    ASSET_MANAGER_STATE_KEY = "asset_manager_state"
    CURRENT_ACTION_STATE_KEY = "current_action_state"

    def __init__(self):
        self._initialize_state()

    def _initialize_state(self):
        """Initialize all state containers if they don't exist"""
        if self.ASSET_MANAGER_STATE_KEY not in st.session_state:
            # Initialize with a default asset manager and check its health
            try:
                manager = get_default_asset_manager()
                is_connected = manager.health_check() if hasattr(manager, 'health_check') else True
                st.session_state[self.ASSET_MANAGER_STATE_KEY] = AssetManagerState(
                    manager=manager,
                    is_connected=is_connected,
                    last_checked=datetime.now()
                )
            except Exception as e:
                st.session_state[self.ASSET_MANAGER_STATE_KEY] = AssetManagerState(
                    manager=None,
                    is_connected=False,
                    connection_error=str(e)
                )
                print(f"Error initializing asset manager: {e}")

        if self.APP_STATE_KEY not in st.session_state:
            logo_urls = self._init_logos()
            documentlist = self.update_document_list()
            embedded_css = self._init_embedded_css()
            st.session_state[self.APP_STATE_KEY] = AppState(
                logo_urls=logo_urls,
                document_list=documentlist,
                embedded_css=embedded_css)

        if self.DOCUMENT_STATE_KEY not in st.session_state:
            st.session_state[self.DOCUMENT_STATE_KEY] = DocumentState()

        if self.PENDING_CHANGES_KEY not in st.session_state:
            st.session_state[self.PENDING_CHANGES_KEY] = PendingChangesState()

        if self.CURRENT_ACTION_STATE_KEY not in st.session_state:
            st.session_state[self.CURRENT_ACTION_STATE_KEY] = CurrentActionState()


    # App State Accessors
    @property
    def app_state(self) -> AppState:
        return st.session_state[self.APP_STATE_KEY]

    @app_state.setter
    def app_state(self, value: AppState):
        st.session_state[self.APP_STATE_KEY] = value

    # Document State Accessors
    @property
    def document_state(self) -> DocumentState:
        return st.session_state[self.DOCUMENT_STATE_KEY]

    @document_state.setter
    def document_state(self, value: DocumentState):
        st.session_state[self.DOCUMENT_STATE_KEY] = value

    # Pending Changes Accessors
    @property
    def pending_changes(self) -> PendingChangesState:
        return st.session_state[self.PENDING_CHANGES_KEY]

    @pending_changes.setter
    def pending_changes(self, value: PendingChangesState):
        st.session_state[self.PENDING_CHANGES_KEY] = value

    # Asset Manager Accessor
    @property
    def asset_manager(self) -> Any:
        return st.session_state[self.ASSET_MANAGER_STATE_KEY].manager

    @asset_manager.setter
    def asset_manager(self, value: Any):
        state = st.session_state[self.ASSET_MANAGER_STATE_KEY]
        state.manager = value
        st.session_state[self.ASSET_MANAGER_STATE_KEY] = state

    # App State Methods
    def update_app_state(self, **kwargs):
        """Update app state with provided values"""
        current = self.app_state
        for key, value in kwargs.items():
            if hasattr(current, key):
                setattr(current, key, value)
        self.app_state = current

    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get document list from app state"""
        return self.app_state.document_list

    def set_document_list(self, docs: List[Dict[str, Any]]):
        """Set document list in app state"""
        self.update_app_state(document_list=docs)

    def open_document(self, document_name: str):
        asset_manager = self.asset_manager
        try:
            document_bytes = asset_manager.get(document_name, AssetType.JSON)
            document_json = document_bytes.decode('utf-8')

            document = Document.from_json(document_json)

            self.set_current_document(document)
            self.set_current_page_index(0)
            return document
        except Exception as e:
            st.error(f"Error opening document: {e}")
            return False

    def delete_document(self, document_name: str):
        asset_manager = self.asset_manager
        try:
            document_name = f"documents:{document_name}.json"
            document_files = asset_manager.list(AssetType.JSON)
            found = False
            for document_file in document_files:
                if document_name == f"documents:{document_file.split('documents:')[1]}":
                    found = True
                    break
            if not found:
                st.error(f"Document '{document_name.split('documents:')[1][:-5]}' not found")
                return False

            asset_manager.delete(document_name, AssetType.JSON)
            return True

        except Exception as e:
            st.error(f"Error deleting document: {e}")
            return False

    def toggle_save_on_exit(self):
        """Toggle the save on exit setting"""
        self.update_app_state(is_save_on_exit=not self.app_state.is_save_on_exit)

    def set_wizard_step(self, step: int):
        """Update the current wizard step"""
        self.update_app_state(wizard_step=step)

    def set_editing_mode(self, is_editing: bool):
        """Set the editing mode"""
        self.update_app_state(is_editing=is_editing)

    def show_success_message(self, message: str):
        """Show a success message"""
        self.update_app_state(show_confirm_success=True, success_message=message)

    # Document State Methods
    def update_document_state(self, **kwargs):
        """Update document state with provided values"""
        current = self.document_state
        for key, value in kwargs.items():
            if hasattr(current, key):
                setattr(current, key, value)
        self.document_state = current

    def get_current_document(self) -> Optional[Document]:
        """Get current document from document state"""
        doc_data = self.document_state.document
        if doc_data and isinstance(doc_data, dict):
            return Document(**doc_data)
        return doc_data

    def set_current_document(self, doc: Document):
        """Set current document in document state"""
        self.update_document_state(document=doc if doc else None)

    def get_current_page_index(self) -> Optional[int]:
        """Get current page index from document state"""
        return self.document_state.current_page_index

    def set_current_page_index(self, index: Optional[int]):
        """Set current page index in document state"""
        self.update_document_state(current_page_index=index)
    def reset_document_state(self):
        """
        Reset document state to initial values.
        This clears all document-related state including current document,
        page index, and new page data.
        """
        self.update_document_state(
            document=None,
            current_page_index=None,
            new_page=NewPage(),  # Use proper NewPage instance instead of empty dict
            new_document_name=""
        )

    def get_document_shared_context(self) -> Optional[SharedContext]:
        """
        Get shared context from document state.
        
        Returns:
            Optional[SharedContext]: The shared context if available, None otherwise
        """
        return self.document_state.shared_context
    # New Page Methods
    def set_new_page_data(self, new_page: NewPage):
        """Set new page data"""
        self.update_document_state(new_page=new_page)

    def update_new_page(self, **kwargs):
        """Update individual fields of new_page similar to update_document_state"""
        current_new_page = self.document_state.new_page
        for key, value in kwargs.items():
            if hasattr(current_new_page, key):
                setattr(current_new_page, key, value)
        # Update the document state with the modified new_page
        self.update_document_state(new_page=current_new_page)

    def get_new_page_data(self) -> NewPage:
        """Get new page data from document state"""
        return self.document_state.new_page

    def reset_new_page(self):
        """Reset new page data to initial values"""
        self.update_document_state(new_page=NewPage())

    def set_new_document_name(self, name: str):
        """Set new document name"""
        self.update_document_state(new_document_name=name)

    def update_page_urls(self, pdf_url: str, preview_url: str, index: int):
        """
        Update the PDF and preview URLs for a specific page.
        
        Args:
            pdf_url (str): URL of the PDF file
            preview_url (str): URL of the preview image
            index (int): Index of the page to update
        """
        page = self.get_current_document().pages[index]
        page.pdf_url = pdf_url
        page.preview_url = preview_url

    # Pending Changes Methods
    def get_pending_changes(self) -> List[PendingChangesState]:
        """Get pending changes from app state"""
        return self.pending_changes

    def update_pending_changes(self, **kwargs):
        """Update pending changes with provided values"""
        current = self.pending_changes
        for key, value in kwargs.items():
            if hasattr(current, key):
                setattr(current, key, value)
        self.pending_changes = current

    def clear_pending_changes(self):
        """Clear all pending changes"""
        self.pending_changes = PendingChangesState()

    def has_pending_changes(self) -> bool:
        """Check if there are any pending changes"""
        changes = self.pending_changes
        return any([
            changes.page_title is not None,
            changes.view is not None,
            changes.table is not None
        ])

    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get document list from app state"""
        return self.app_state.document_list

    def set_document_list(self, docs: List[Dict[str, Any]]):
        """Set document list in app state"""
        self.update_app_state(document_list=docs)

    def trigger_rerun_if_needed(self):
        """
        Trigger a Streamlit rerun if there's a success message to be shown.
        This displays the message as a toast and clears it from the state.
        """
        if self.app_state.show_confirm_success:
            message = self.app_state.success_message
            st.toast(message, duration=3, icon="✅")
            self.update_app_state(show_confirm_success=False, success_message="")

    def set_embedded_css(self, css: str):
        """Set embedded CSS in app state"""
        self.update_app_state(embedded_css=css)

    def get_embedded_css(self) -> str:
        """Get embedded CSS from app state"""
        return self.app_state.embedded_css

    def delete_page(self, page_index: int):
        """
        Delete a page from the current document by index.
        
        Args:
            page_index (int): Index of the page to delete
        """
        current_page = self.get_current_page_index()

        if page_index == 0 and len(self.get_current_document().pages) == 1:
            st.toast("Cannot delete last page, maybe you wanted to delete the document?", icon="⚠️")
            return

        if current_page >= page_index:
            self.set_current_page_index(current_page - 1)

        self.update_document_state(document=self.get_current_document().delete_page(page_index))
        self.show_success_message(f"Page deleted successfully!")
        st.rerun()

    def open_page(self, page_index: int):
        """
        Open a specific page by index.
        
        Args:
            page_index (int): Index of the page to open
        """
        self.set_current_page_index(page_index)
        st.rerun()

    def get_current_page(self):
        """
        Get the current page from the document.
        
        Returns:
            PageContext: The current page object
        """
        return self.get_current_document().pages[self.get_current_page_index()]


    # Asset Manager State Accessors
    @property
    def asset_manager_state(self) -> AssetManagerState:
        return st.session_state[self.ASSET_MANAGER_STATE_KEY]

    @asset_manager_state.setter
    def asset_manager_state(self, value: AssetManagerState):
        st.session_state[self.ASSET_MANAGER_STATE_KEY] = value

    # Asset Manager Accessor
    @property
    def asset_manager(self):
        """Convenience accessor to get the asset manager directly"""
        return self.asset_manager_state.manager

    def update_asset_manager_health(self, is_connected: bool, error_msg: Optional[str] = None):
        """Update the health status of the asset manager"""
        current_state = self.asset_manager_state
        current_state.is_connected = is_connected
        current_state.last_checked = datetime.now()
        current_state.connection_error = error_msg
        self.asset_manager_state = current_state

    def check_asset_manager_health(self) -> bool:
        """Check the health of the asset manager if it implements health_check method"""
        manager = self.asset_manager
        if hasattr(manager, 'health_check'):
            try:
                is_healthy = manager.health_check()
                self.update_asset_manager_health(is_healthy)
                return is_healthy
            except Exception as e:
                self.update_asset_manager_health(False, str(e))
                return False
        else:
            # Fallback behavior if health_check is not implemented
            self.update_asset_manager_health(True)  # Assume healthy if no health_check method
            return True

    # Current Action State Accessors
    @property
    def current_action_state(self) -> CurrentActionState:
        return st.session_state[self.CURRENT_ACTION_STATE_KEY]

    @current_action_state.setter
    def current_action_state(self, value: CurrentActionState):
        st.session_state[self.CURRENT_ACTION_STATE_KEY] = value

    # Private Methods
    def _init_logos(self) -> dict:
        logo_urls = {}

        powered_by_logo = static_path / "images" / "new_logo_powered.png"
        if powered_by_logo.exists():
            powered_by_logo_content = powered_by_logo.read_bytes()
            powered_by_logo_name = f"logo_powered.png"
            self.asset_manager.save(powered_by_logo_name, powered_by_logo_content, AssetType.IMG)
            logo_urls['powered_by'] = powered_by_logo_name
        else:
            logo_urls['powered_by'] = ""  # Fallback if file doesn't exist

        header_logo = static_path / "images" / "new_logo.svg"
        if header_logo.exists():
            header_logo_content = header_logo.read_text(encoding='utf-8')
            header_logo_name = f"logo_header.svg"
            self.asset_manager.save(header_logo_name, header_logo_content.encode('utf-8'), AssetType.SVG)
            logo_urls['header'] = header_logo_name
        else:
            logo_urls['header'] = ""  # Fallback if file doesn't exist

        return logo_urls

    def update_document_list(self):
        document_list = []
        files = self.asset_manager.list(AssetType.JSON)
        documents = [f for f in files if f.endswith('.json') and f.startswith('json:documents:')]
        for document in documents:
            try:
                doc_bytes = self.asset_manager.get(document.split("json:")[1], AssetType.JSON)
                doc_data = doc_bytes.decode('utf-8')
                doc_json = json.loads(doc_data)
                date = doc_json.get("updated_at", "")
                date = datetime.fromisoformat(date).strftime("%Y-%m-%d %H:%M")
                doc_info = {
                    "name": doc_json.get("name", ""),
                    "updated_at": date,
                    "preview": doc_json.get("pages")[0].get("preview_url", ""),
                    "page_count": len(doc_json.get("pages", [1]))
                }
                document_list.append(doc_info)
            except Exception as e:
                print(e)
        return document_list

    def _init_embedded_css(self):
        embedded_css = ""
        css_file = static_path / "css" / "main.css"
        if css_file.exists():
            embedded_css = f"<style>{css_file.read_text(encoding='utf-8')}</style>"
        return embedded_css

state_manager = StateManager()
