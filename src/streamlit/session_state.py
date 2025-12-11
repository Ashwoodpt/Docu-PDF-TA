import streamlit as st
from src.core.asset_factory import create_asset_manager, BackendType
from src.core.asset_manager import AssetType
from src.streamlit.state_manager import format_datetime
from src.streamlit.state_manager import update_document_list
from pathlib import Path
import json

static_path = Path(__file__).parent / "static"



def initialize_logos() -> dict:
    """
    Initialize logo URLs by loading logos from static assets and storing them in the asset manager.
    
    Returns:
        A dictionary containing URLs for powered_by and header logos
    """
    try:
        asset_manager = st.session_state.asset_manager
        logo_urls = {}

        # Load powered by logo
        powered_by_logo_path = static_path / "images" / "new_logo_powered.png"
        if powered_by_logo_path.exists():
            powered_by_logo_content = powered_by_logo_path.read_bytes()
            powered_by_logo_name = f"logo_powered.png"
            asset_manager.save(powered_by_logo_name, powered_by_logo_content, AssetType.IMG)
            logo_urls['powered_by'] = asset_manager.get_public_url(powered_by_logo_name, AssetType.IMG)
        else:
            logo_urls['powered_by'] = ""  # Fallback if file doesn't exist

        # Load header logo
        header_logo_path = static_path / "images" / "new_logo.svg"
        if header_logo_path.exists():
            header_logo_content = header_logo_path.read_text(encoding='utf-8')
            header_logo_name = f"logo_header.svg"
            asset_manager.save(header_logo_name, header_logo_content.encode('utf-8'), AssetType.SVG)
            logo_urls['header'] = asset_manager.get_public_url(header_logo_name, AssetType.SVG)
        else:
            logo_urls['header'] = ""  # Fallback if file doesn't exist

        return logo_urls
    except Exception as e:
        st.error(f"Error initializing logos: {e}")
        return {'powered_by': "", 'header': ""}

def check_redis_connection() -> tuple[bool, object]:
    """
    Check if Redis connection is available and return the asset manager if successful.
    
    Returns:
        A tuple containing (connection_success: bool, asset_manager: object or None)
    """
    try:
        asset_manager = create_asset_manager(BackendType.REDIS)
        # Try to ping Redis to confirm connection
        if hasattr(asset_manager, 'client') and asset_manager.client:
            asset_manager.client.ping()
            return True, asset_manager
        return False, None
    except Exception as e:
        return False, None
def init_state() -> None:
    """
    Initialize the Streamlit session state with default values and asset managers.
    This function sets up Redis connection, asset managers, document lists, and other
    necessary session state variables.
    """
    if "asset_manager" not in st.session_state:
        success, manager = check_redis_connection()
        if success:
            st.session_state.asset_manager = manager
            st.session_state.redis_connected = True
        else:
            # Fallback to local storage if Redis connection fails
            st.session_state.asset_manager = create_asset_manager(BackendType.LOCAL)
            st.session_state.redis_connected = False
        # Initialize logos after setting up the asset manager
        st.session_state.logo_urls = initialize_logos()

    if "document_list" not in st.session_state:
        update_document_list()


    # Initialize logos and store in session state (only if not already done)
    if "logo_urls" not in st.session_state and "asset_manager" in st.session_state:
        st.session_state.logo_urls = initialize_logos()
    # Initialize document state - create document only when user adds first page
    if "document" not in st.session_state:
        st.session_state.document = None
    if "current_page_index" not in st.session_state:
        st.session_state.current_page_index = None
    if "new_page" not in st.session_state:
        st.session_state.new_page = {}
    if "new_document_name" not in st.session_state:
        st.session_state.new_document_name = ''
    if "show_confirm_success" not in st.session_state:
        st.session_state.show_confirm_success = False
    if "success_message" not in st.session_state:
        st.session_state.success_message = ''
    if "create_new_page" not in st.session_state:
        st.session_state.create_new_page = False
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 0
    if "isEditing" not in st.session_state:
        st.session_state.isEditing = False
    if "pending_view" not in st.session_state:
        st.session_state.pending_view = None
    if "pending_table" not in st.session_state:
        st.session_state.pending_table = None
    if "pending_changes" not in st.session_state:
        st.session_state.pending_changes = {}
    if "isSaveOnExit" not in st.session_state:
        st.session_state.isSaveOnExit = True



    if st.session_state.get("show_confirm_success", False):
        message = st.session_state.get("success_message", "Success")
        st.toast(message,duration=3, icon="✅")
        st.session_state.show_confirm_success = False
        st.session_state.success_message = ''

