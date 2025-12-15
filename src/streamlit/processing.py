import streamlit as st
import pandas as pd
import numpy as np
from src.pdf.pdf_service import PDFService
from uuid import uuid4
from src.models.context_model import Document, PageContext, SharedContext, View, ViewType, TableData
from src.core.asset_manager import AssetManager, AssetType
import json
from src.svg.wall_processor import generate_wall_projection_svg
from src.streamlit.state_manager import state_manager
from src.render.template_engine import engine
from pathlib import Path

# Constants
TEMPLATES_PATH = Path(__file__).parent.parent / "templates"
STATIC_PATH = Path(__file__).parent / "static"
CSS_PATH = STATIC_PATH / "css" / "main.css"
DEFAULT_ADDRESS = "127 Example Street, Example City, CA 12345"
DOCUMENT_PREFIX = "documents:"

css = state_manager.get_embedded_css()


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

    asset_manager = state_manager.asset_manager

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
    new_page_state = state_manager.get_new_page_data()
    asset_manager = state_manager.asset_manager
    document_state = state_manager.document_state
    # Get the uploaded data from new_page session state
    title = new_page_state.title
    view_data = new_page_state.view[0]
    table_data_file = new_page_state.table
    logos = state_manager.app_state.logo_urls

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
        asset_manager = asset_manager
        wall_asset_name = f"wall_{str(uuid4())}.svg"
        asset_manager.save(wall_asset_name, wall_image_svg.encode('utf-8'), AssetType.SVG)
        wall_image_url = asset_manager.get_public_url(wall_asset_name, AssetType.SVG)

    pano_content = ""
    if panorama_file:
        pano_content = _save_file_to_asset_manager(panorama_file, "pano")

    # Process the table data
    table_data = None
    data_records = table_data_file.to_dict('records')
    headers = list(table_data_file.columns)
    # Convert DataFrame to list of dictionaries
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
    if document_state.document is None:
        # Create a new document
        shared_context = SharedContext(
            document_name=document_state.new_document_name,
            document_id=hex(uuid4().int)[0:8],
            address_line=DEFAULT_ADDRESS,
            powered_by_logo_url=logos['powered_by'],
            header_logo_url=logos['header'],
            embedded_css=css
        )

        document = Document(
            name=document_state.new_document_name,
            shared_context=shared_context
        )
        document.add_page(page_context)
        state_manager.set_current_document(document)
        state_manager.set_current_page_index(0)
    else:
        document = state_manager.get_current_document()
        document = document.add_page(page_context)
        shared_context = document.shared_context  # Get the shared context from existing document
        state_manager.set_current_document(document)
        state_manager.set_current_page_index(len(document.pages) - 1)

    # Generate PDF for the page using the PDF service
    asset_manager = state_manager.asset_manager
    pdf_service = PDFService(engine, asset_manager)
    # Add the page PDF to the page context
    page_index = state_manager.get_current_page_index()
    page_pdf_url, preview_url = pdf_service.save_page_pdf(
        page_context,
        shared_context,
        page_index
    )

    # Update the page context with PDF URLs after page creation
    # current_page_ctx = state_manager.get_current_document().pages[page_index]
    state_manager.update_page_urls(page_pdf_url, preview_url, page_index)

    # Set the current page index to the last page (newly added page)
    state_manager.set_current_page_index(page_index)

    # Clear the new_page session state
    state_manager.reset_new_page()
    state_manager.set_wizard_step(0)

def save_document() -> None:
    """
    Save the current document to the asset manager as a JSON file.
    This function serializes the document object and saves it to the configured storage backend.
    """
    document = state_manager.get_current_document()
    if document is not None:
        asset_manager: AssetManager = state_manager.asset_manager
        try:
            # Use model_dump with serialization mode to properly handle enums
            document_dict = document.model_dump(mode='json')
            # Convert to JSON string and save
            document_json = json.dumps(document_dict)
            document_name = f"{DOCUMENT_PREFIX}{document.name}.json"  # Use document ID to ensure uniqueness
            asset_manager.save(document_name, document_json.encode('utf-8'), AssetType.JSON)

            state_manager.show_success_message(f"Document {document.name} saved successfully!")

        except Exception as e:
            st.error(f"Error saving document: {e}")

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

    asset_manager = state_manager.asset_manager

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
    asset_manager = state_manager.asset_manager
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
    asset_manager = state_manager.asset_manager
    pdf_service = PDFService(engine, asset_manager)
    document = state_manager.get_current_document()
    document_list = state_manager.get_document_list()

    if not state_manager.has_pending_changes():
        return

    current_index = state_manager.get_current_page_index()
    page = state_manager.get_current_document().pages[current_index]
    pending_changes = state_manager.get_pending_changes()
    for key, value in pending_changes:
        match key:
            case "table":
                if value is not None:
                    page.table_data = value
            case "view":
                if value is not None:
                    page.views[0] = value
            case "page_title":
                if value is not None:
                    page.page_title = value
            case _:
                pass

    pdf_url, preview_url = pdf_service.save_page_pdf(
        page,
        document.shared_context,
        current_index
    )
    page.pdf_url = pdf_url
    page.preview_url = preview_url

    if current_index == 0 and document is not None:
        doc_name = document.name
        for doc_info in document_list:
            if doc_info["name"] == doc_name:
                doc_info["preview"] = preview_url
                break
    state_manager.clear_pending_changes()
    state_manager.show_success_message("Page updated successfully!")
    state_manager.set_editing_mode(False)