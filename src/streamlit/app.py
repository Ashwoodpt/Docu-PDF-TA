import streamlit as st
from pathlib import Path
from src.render.template_engine import TemplateEngine

from src.streamlit.dialogs import upload_files_dialog, new_page_dialog
from src.streamlit.processing import load_document,delete_document
from src.streamlit.session_state import init_state
from src.streamlit.sidebar import sidebar
from src.streamlit.edit_page import edit_page
from src.streamlit.dynamic.home_component import render_home_component

import pandas as pd

# Initialize global embedded CSS
static_path = Path(__file__).parent / "static"
css_path = static_path / "css" / "main.css"
if css_path.exists():
    css_content = css_path.read_text(encoding='utf-8')
    embedded_css = f'<style>{css_content}</style>'
else:
    embedded_css = '<style>/* CSS file not found */</style>'

st.set_page_config(page_title = "PDF RENDER",layout = "wide")

# Check Redis connection status
init_state()

sidebar(embedded_css=embedded_css)

match st.session_state.get("wizard_step", 0):
    case 0:
        pass
    case 1:
        new_page_dialog()
    case 2:
        upload_files_dialog(st.session_state.new_page["template"])


# Initialize the template engine
templates_path = Path(__file__).parent.parent / "templates"
engine = TemplateEngine(templates_path)
st.session_state.engine = engine

def render_current_page():
    """Render the current page from the document."""
    if st.session_state.document is None:
        # Render home page if no page is selected
        try:
            context = {
                "embedded_css": embedded_css,
                "documents": st.session_state.document_list
            }
            home_event = render_home_component(
                engine=engine,
                context=context,
                key=f"home_component{hash(str(context['documents']))}",
                events=True
            )
            if home_event:
                action = home_event.get("action",'')
            
                match action:
                    case "add_new_document":
                        st.session_state.wizard_step = 1
                    case "delete_document":
                        delete_document(home_event.get("name"))
                    case "open_document":
                        load_document(home_event.get("name"))
                    case _:
                        return
        except Exception as e:
            st.error(f"Error rendering template: {e}")
            st.warning("Displaying fallback content...")
            st.title("PDF RENDER")
            st.subheader("Document Processing")
        return

    # If we have a document and a current page, render it
    if st.session_state.document is not None and "current_page_index" in st.session_state:
        try:
            # Get current page context from document
            current_page_index = st.session_state.current_page_index
            current_page_ctx = st.session_state.document.pages[current_page_index]

            # Get shared context
            shared_ctx = st.session_state.document.shared_context

            # Convert page context to template context format
            # Convert View objects to dict format expected by template
            views_for_template = []
            for view in current_page_ctx.views:
                views_for_template.append({
                    "side": view.side.value if hasattr(view.side, 'value') else view.side,
                    "image": view.image,
                    "wall_image": view.wall_image,
                    "pano": view.pano,
                    "wall_data": view.wall_data
                })

            # Convert table data to template format
            table_data_for_template = None
            if current_page_ctx.table_data:
                table_data_for_template = {
                    "headers": current_page_ctx.table_data.headers,
                    "data": current_page_ctx.table_data.data
                }

            # Create context for template rendering
            context = {
                "page_title": current_page_ctx.page_title,
                "embedded_css": shared_ctx.embedded_css,  # Now using CSS from shared context
                "generation_date": current_page_ctx.generation_date,
                "page_number": current_page_ctx.page_number,
                "total_pages": len(st.session_state.document.pages),
                "document_name": shared_ctx.document_name,
                "document_id": shared_ctx.document_id,
                "address_line": shared_ctx.address_line,
                "powered_by_logo_url": shared_ctx.powered_by_logo_url,
                "header_logo_url": shared_ctx.header_logo_url,
                "views": views_for_template,
                "table_data": table_data_for_template,
            }

            rendered_html = engine.render("base.html", context)
            st.markdown(rendered_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error rendering template: {e}")
            st.warning("Displaying fallback content...")
            st.title("PDF RENDER")
            st.subheader("Document Processing")
    else:
        # Default home page rendering if no document exists
        try:
            # Use the global embedded CSS
            context = {
                "embedded_css": embedded_css,
            }
            rendered_html = engine.render("home.html", context)
            st.markdown(rendered_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error rendering template: {e}")
            st.warning("Displaying fallback content...")
            st.title("PDF RENDER")
            st.subheader("Document Processing")

if st.session_state.isEditing:
    col1,col2 = st.columns(2)
    with col1:
        render_current_page()
    with col2:
        edit_page()
else:
    render_current_page()