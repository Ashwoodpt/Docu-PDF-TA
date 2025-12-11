import streamlit as st
import pandas as pd
import numpy as np
from src.pdf.pdf_service import PDFService
from uuid import uuid4
from src.models.context_model import Document, PageContext, SharedContext, View, ViewType, TableData
from src.core.asset_manager import AssetManager, AssetType
from src.streamlit.state_manager import update_document_list
import json
from src.svg.wall_processor import generate_wall_projection_svg

from src.render.template_engine import TemplateEngine
from pathlib import Path

# Constants
TEMPLATES_PATH = Path(__file__).parent.parent / "templates"
STATIC_PATH = Path(__file__).parent / "static"
CSS_PATH = STATIC_PATH / "css" / "main.css"
DEFAULT_ADDRESS = "127 Example Street, Example City, CA 12345"
DOCUMENT_PREFIX = "documents:"

# Initialize template engine
template_engine = TemplateEngine(TEMPLATES_PATH)

# Load embedded CSS
if CSS_PATH.exists():
    css_content = CSS_PATH.read_text(encoding='utf-8')
    embedded_css = f'<style>{css_content}</style>'
else:
    embedded_css = '<style>/* CSS file not found */</style>'

def _save_file_to_asset_manager(file_obj, asset_prefix: str, asset_type: AssetType = None):
    """
    Helper function to save a file to the asset manager and return the URL.
    
    Args:
        file_obj: File object to save
        asset_prefix: Prefix for the asset name
        asset_type: Asset type, will be inferred if not provided
    
    Returns:
        URL of the saved asset
    """
    if not file_obj:
        return ""
    
    asset_manager = st.session_state.asset_manager
    
    if asset_type is None:
        file_extension = file_obj.name.split('.')[-1].lower() if hasattr(file_obj, 'name') else 'svg'
        asset_type = AssetType.SVG if file_extension == 'svg' else AssetType.IMG
    else:
        file_extension = 'svg' if asset_type == AssetType.SVG else 'img'
    
    asset_name = f"{asset_prefix}_{str(uuid4())}.{file_extension}"
    asset_content = file_obj.read()
    
    # Reset file pointer after reading
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
    
    asset_manager.save(asset_name, asset_content, asset_type)
    asset_url = asset_manager.get_public_url(asset_name, asset_type)
    
    return asset_url

def create_page_from_uploaded_data() -> None:
    """
    Create a page from uploaded data when user completes the wizard.
    This function processes uploaded images, panorama, wall data, and table data
    to create a new page context and add it to the document.
    """
    # Get the uploaded data from new_page session state
    title = st.session_state.new_page.get("title", "New Page")
    view_data = st.session_state.new_page.get("view", {})
    table_data_file = st.session_state.new_page.get("table")

    # Process the view data
    side = view_data.get("side", "Back")
    image_file = view_data.get("image")
    panorama_file = view_data.get("panorama")
    wall_image_svg = view_data.get("wall_image_svg", "")
    wall_data_file = view_data.get("wall_data")

    # Process side projection image - save it to asset manager and get URL
    image_url = ""
    if image_file:
        image_url = _save_file_to_asset_manager(image_file, "side")

    # Process wall image SVG - save it to asset manager and get URL
    wall_image_url = ""
    if wall_image_svg:
        asset_manager = st.session_state.asset_manager
        wall_asset_name = f"wall_{str(uuid4())}.svg"
        asset_manager.save(wall_asset_name, wall_image_svg.encode('utf-8'), AssetType.SVG)
        wall_image_url = asset_manager.get_public_url(wall_asset_name, AssetType.SVG)

    pano_content = ""
    if panorama_file:
        pano_content = _save_file_to_asset_manager(panorama_file, "pano")

    # Process the table data
    table_data = None
    if table_data_file:
        # Read CSV content
        df = pd.read_csv(table_data_file)
        df = process_table(df)

        headers = list(df.columns)
        # Convert DataFrame to list of dictionaries
        data_records = df.to_dict('records')
        table_data = TableData(
            headers=headers,
            data=data_records
        )

    # Create the page context
    page_context = PageContext(
        page_title=title,
        views=[
            View(
                side=ViewType(side),
                image=image_url,
                wall_image=wall_image_url,
                pano=pano_content,
                wall_data=wall_data_file
            )
        ],
        table_data=table_data
    )

    # Add to document or create a new document if none exists
    if st.session_state.document is None:
        # Create a new document
        shared_context = SharedContext(
            document_name=st.session_state.get("new_document_name", "New Document"),
            document_id=hex(uuid4().int)[0:8],
            address_line=DEFAULT_ADDRESS,
            powered_by_logo_url=st.session_state.logo_urls['powered_by'],
            header_logo_url=st.session_state.logo_urls['header'],
            embedded_css=embedded_css
        )

        document = Document(
            name=st.session_state.new_document_name,
            shared_context=shared_context
        )
        document.add_page(page_context)
        st.session_state.document = document
        st.session_state.current_page_index = 0
    else:
        st.session_state.document.add_page(page_context)
        st.session_state.current_page_index = len(st.session_state.document.pages) - 1

    # Generate PDF for the page using the PDF service
    asset_manager = st.session_state.asset_manager
    pdf_service = PDFService(template_engine, asset_manager)

    # Add the page PDF to the page context
    page_pdf_url, preview_url = pdf_service.save_page_pdf(
        page_context,
        st.session_state.document.shared_context,
        st.session_state.current_page_index
    )
    
    # Update the page context with PDF URLs after page creation
    current_page_ctx = st.session_state.document.pages[st.session_state.current_page_index]
    current_page_ctx.pdf_url = page_pdf_url
    current_page_ctx.preview_url = preview_url

    # Set the current page index to the last page (newly added page)
    st.session_state.current_page_index = len(st.session_state.document.pages) - 1

    # Clear the new_page session state
    st.session_state.new_page = {}
    st.session_state.wizard_step = 0

def save_document() -> None:
    """
    Save the current document to the asset manager as a JSON file.
    This function serializes the document object and saves it to the configured storage backend.
    """
    if st.session_state.document is not None:
        document = st.session_state.get("document")
        asset_manager: AssetManager = st.session_state.get("asset_manager")

        try:
            # Use model_dump with serialization mode to properly handle enums
            document_dict = document.model_dump(mode='json')

            # Convert to JSON string and save
            document_json = json.dumps(document_dict)
            document_name = f"{DOCUMENT_PREFIX}{document.name}.json"  # Use document ID to ensure uniqueness
            asset_manager.save(document_name, document_json.encode('utf-8'), AssetType.JSON)

            st.session_state.show_confirm_success = True
            st.session_state.success_message = f"Document '{document.name}' saved successfully!"

        except Exception as e:
            st.error(f"Error saving document: {e}")

def load_document(document_name: str):
    asset_manager: AssetManager = st.session_state.get("asset_manager")
    
    try:
        # Get the document JSON from the asset manager
        document_bytes = asset_manager.get(document_name, AssetType.JSON)
        document_json = document_bytes.decode('utf-8')

        # Create the Document object from the JSON
        document = Document.from_json(document_json)

        # Update session state with the loaded document
        st.session_state.document = document
        st.session_state.current_page_index = 0  # Default to first page

        st.success(f"Document '{document.name}' loaded successfully!")
        st.rerun()
        return document
    except Exception as e:
        st.error(f"Error loading document: {e}")
        return None

def list_documents():
    """List all documents saved in the asset manager."""
    asset_manager: AssetManager = st.session_state.get("asset_manager")
    try:
        json_files = asset_manager.list(AssetType.JSON)
        document_files = [f for f in json_files if f.endswith('.json') and f.startswith(DOCUMENT_PREFIX)]
        return document_files
    except Exception as e:
        st.error(f"Error listing documents: {e}")
        return []

def delete_document(document_name: str) -> bool:
    """Delete a document from the asset manager."""
    asset_manager: AssetManager = st.session_state.get("asset_manager")
    try:
        # Check if document exists before attempting deletion
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

        # If the deleted document is the currently loaded one, clear the session state
        if (st.session_state.get("document") and
            f"documents:{st.session_state.document.name}.json" == document_name):
            st.session_state.document = None
            st.session_state.current_page_index = 0
        
        st.success(f"Document '{document_name.split('documents:')[1][:-5]}' deleted successfully!")
        update_document_list()
        return True

    except Exception as e:
        st.error(f"Error deleting document: {e}")
        return False

def generate_svg_from_json(json_data: dict, side: str):
    """
    Generate an SVG from JSON wall data for a specific side.
    
    Args:
        json_data: Dictionary containing wall data
        side: The side to generate the projection for (e.g., "North", "South")
        
    Returns:
        SVG element or None if an error occurs
    """
    # Generate SVG preview using the wall processor
    try:
        walls = json_data["walls"]
        svg_element = generate_wall_projection_svg(walls, [side])
        return svg_element
    except Exception as e:
        st.error(f"Error generating preview: {e}")
        return None

def process_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame by removing unnamed columns and replacing NaN values.
    
    Args:
        df: Input DataFrame to process
        
    Returns:
        Processed DataFrame with unnamed columns removed and NaN values replaced
    """
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.replace({np.nan: ''})
    return df

def save_uploaded_file_to_asset_manager(uploaded_file, asset_prefix="asset", is_svg=False):
    """
    Save an uploaded file to the asset manager and return the URL.

    Args:
        uploaded_file: The uploaded file object from Streamlit
        asset_prefix: Prefix for the asset name (e.g., "side", "pano", "wall")
        is_svg: Whether this is specifically an SVG file (overrides file extension detection)

    Returns:
        URL of the saved asset
    """
    if not uploaded_file:
        return ""

    asset_manager = st.session_state.asset_manager

    if is_svg:
        file_extension = "svg"
        asset_type = AssetType.SVG
    else:
        file_extension = uploaded_file.name.split('.')[-1].lower() if hasattr(uploaded_file, 'name') else 'svg'
        asset_type = AssetType.SVG if file_extension == 'svg' else AssetType.IMG

    asset_name = f"{asset_prefix}_{str(uuid4())}.{file_extension}"
    asset_content = uploaded_file.read()

    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)  # Reset file pointer after reading

    asset_manager.save(asset_name, asset_content, asset_type)
    asset_url = asset_manager.get_public_url(asset_name, asset_type)

    return asset_url

def save_wall_projection_to_asset_manager(svg_string: str) -> str:
    """
    Save a wall projection SVG string to the asset manager and return the URL.
    
    Args:
        svg_string: SVG content as a string
        
    Returns:
        URL of the saved SVG asset
    """
    asset_manager = st.session_state.asset_manager
    asset_name = f"wall_projection_{str(uuid4())}.svg"
    asset_content = svg_string.encode('utf-8')
    asset_manager.save(asset_name, asset_content, AssetType.SVG)
    asset_url = asset_manager.get_public_url(asset_name, AssetType.SVG)
    return asset_url

def update_page_from_edits() -> None:
    """
    Update the current page from pending edits in the session state.
    This function processes pending changes and saves an updated PDF for the page.
    """
    asset_manager = st.session_state.asset_manager
    pdf_service = PDFService(template_engine, asset_manager)

    if not st.session_state.pending_changes:
        return

    page = st.session_state.document.pages[st.session_state.current_page_index]
    for key, value in st.session_state.pending_changes.items():
        match key:
            case "table":
                page.table_data = value
            case "view":
                page.views[0] = value
            case _:
                pass

    pdf_url, preview_url = pdf_service.save_page_pdf(
        page,
        st.session_state.document.shared_context,
        st.session_state.current_page_index
    )
    page.pdf_url = pdf_url
    page.preview_url = preview_url

    if st.session_state.current_page_index == 0 and st.session_state.document is not None:
        doc_name = st.session_state.document.name
        for doc_info in st.session_state.document_list:
            if doc_info["name"] == doc_name:
                doc_info["preview"] = preview_url
                break
    st.session_state.pending_changes = {}
    st.session_state.show_confirm_success = True
    st.session_state.success_message = f"Page updated successfully!"
    st.session_state.isEditing = False
