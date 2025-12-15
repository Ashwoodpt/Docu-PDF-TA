import streamlit as st

from src.streamlit.dialogs import upload_files_dialog, new_page_dialog
from src.streamlit.sidebar import sidebar
from src.streamlit.edit_page import edit_page
from src.streamlit.dynamic.home_component import render_home_component
from src.streamlit.state_manager import state_manager
from src.render.template_engine import engine


st.set_page_config(page_title = "PDF RENDER",layout = "wide")

# Global state manager instance
state_manager.__init__()

sidebar()
# Handle wizard steps using the new state management
current_wizard_step = state_manager.app_state.wizard_step

if state_manager.app_state.show_confirm_success:
    st.toast(state_manager.app_state.success_message, duration=3, icon="✅")
    state_manager.update_app_state(show_confirm_success=False, success_message="")

match current_wizard_step:
    case 0:
        pass
    case 1:
        new_page_dialog()
    case 2:
        upload_files_dialog(state_manager.document_state.new_page.template)

css = state_manager.app_state.embedded_css

def render_current_page():
    """Render the current page from the document."""
    doc = state_manager.get_current_document()

    if doc is None:
        # Render home page if no page is selected
        try:
            context = {
                "embedded_css": css,
                "documents": state_manager.update_document_list()
            }
            home_event = render_home_component(
                engine=engine,
                context=context,
                key=f"home_component{hash(str(context['documents'])) if context['documents'] else 'no_docs'}",
                events=True
            )
            if home_event:
                action = home_event.get("action",'')

                match action:
                    case "add_new_document":
                        state_manager.set_wizard_step(1)
                        st.rerun()
                    case "delete_document":
                        success = state_manager.delete_document(home_event.get("name"))
                        if success:
                            list = state_manager.update_document_list()
                            state_manager.app_state.document_list = list
                        st.rerun()
                    case "open_document":
                        state_manager.open_document(home_event.get("name"))
                        st.rerun()
                    case _:
                        return
        except Exception as e:
            st.error(f"Error rendering template: {e}")
            st.warning("Displaying fallback content...")
            st.title("PDF RENDER")
            st.subheader("Document Processing")
        return

    # If we have a document and a current page, render it
    page_idx = state_manager.get_current_page_index()
    if doc is not None and page_idx is not None:
        try:
            # Get current page context from document
            current_page_ctx = doc.pages[page_idx]

            # Get shared context
            shared_ctx = doc.shared_context

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
                "embedded_css": css,  # Now using CSS from shared context
                "generation_date": current_page_ctx.generation_date,
                "page_number": current_page_ctx.page_number,  # Use the page's own page_number field
                "total_pages": len(doc.pages),
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
                "embedded_css": css,
            }
            rendered_html = engine.render("home.html", context)
            st.markdown(rendered_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error rendering template: {e}")
            st.warning("Displaying fallback content...")
            st.title("PDF RENDER")
            st.subheader("Document Processing")

if state_manager.app_state.is_editing:
    col1,col2 = st.columns(2)
    with col1:
        render_current_page()
    with col2:
        edit_page()
else:
    render_current_page()