import streamlit as st
import json
from src.models.asset_model import AssetType
import datetime

def format_datetime(value: str, format_string: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format a datetime string to a specified format.
    
    Args:
        value: ISO format datetime string
        format_string: Format string for output (default: "%Y-%m-%d %H:%M")
        
    Returns:
        Formatted datetime string
    """
    dt_object = datetime.datetime.fromisoformat(value)
    return dt_object.strftime(format_string)

def get_document_list() -> list:
    """
    Initialize the document list by fetching JSON documents from the asset manager.
    
    Returns:
        A list of document information dictionaries
    """
    document_list = []
    files = st.session_state.asset_manager.list(AssetType.JSON)
    documents = [f for f in files if f.endswith('.json') and f.startswith('json:documents:')]
    for document in documents:
        try:
            doc_bytes = st.session_state.asset_manager.get(document.split("json:")[1], AssetType.JSON)
            doc_data = doc_bytes.decode('utf-8')
            doc_json = json.loads(doc_data)

            doc_info = {
                "name": doc_json.get("name", ""),
                "updated_at": format_datetime(doc_json.get("updated_at", "")),
                "preview": doc_json.get("pages")[0].get("preview_url", ""),
                "page_count": len(doc_json.get("pages", [1]))
            }
            document_list.append(doc_info)
        except Exception as e:
            print(e)
    return document_list

def update_document_list():
    st.session_state.document_list = get_document_list()
    st.rerun()