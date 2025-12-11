import streamlit as st
from src.streamlit.dialogs import new_page_dialog,confirm_dialog
from src.streamlit.processing import save_document, delete_page
from src.streamlit.state_manager import update_document_list,toggle_save_on_exit
from src.streamlit.dynamic.page_list_component import render_page_list_component
from pathlib import Path
import json

def sidebar(embedded_css: str) -> None:
    """
    Render the sidebar UI component in the Streamlit application.
    The sidebar includes Redis connection status, document management buttons,
    and page navigation controls when a document is loaded.
    """
    with st.sidebar:
        # Display Redis connection status
        if st.session_state.get("redis_connected", False):
            st.success("✅ Redis Connected")
        else:
            st.warning("⚠️ Redis Disconnected (Using Local Storage)")

        if st.session_state.document is not None:
            st.button("Add a new page", key="new page", on_click=new_page_dialog, use_container_width=True,shortcut="CTRL+Q")
            if st.button("Save document", key="save document", use_container_width=True,shortcut="CTRL+S"):
                save_document()
                st.rerun()
            with st.container(horizontal_alignment="distribute"):
                if st.button("Edit page", key="edit page", use_container_width=True,shortcut="CTRL+E"):
                    st.session_state.isEditing = not st.session_state.isEditing
                if st.button("Back", key="back", use_container_width=True,shortcut="Escape"):
                    if st.session_state.isSaveOnExit:
                        save_document()
                    st.session_state.isEditing = False
                    st.session_state.document = None
                    update_document_list()
        st.toggle("Save on exit?", key="save_on_exit", value=st.session_state.isSaveOnExit,on_change=toggle_save_on_exit)


        st.divider()
        if st.session_state.document is not None:
            st.header(st.session_state.document.name,text_alignment="center")
        if st.session_state.document is not None and st.session_state.document.pages:
            # Convert PageContext objects to JSON-serializable dictionaries
            pages_serializable = [page.model_dump() for page in st.session_state.document.pages]
            context = {
                "embedded_css": embedded_css,
                "pages": pages_serializable,
                "active_page": st.session_state.current_page_index + 1
            }
            page_list_event = render_page_list_component(
                engine=st.session_state.engine,
                context=context,
                key=f"page_list_component{hash(str(len(pages_serializable)))}",
                events=True
            )
            
            if page_list_event:
                selected_page = page_list_event.get("index", 0)

                match page_list_event.get("action", ""):
                    case "open_page":
                        if(selected_page != st.session_state.current_page_index):
                            st.session_state.current_page_index = selected_page
                            st.rerun()
                    case "delete_page":
                        delete_page(page_list_event.get("index"))
                    case _:
                        pass
                page_list_event = None                

        else:
            st.write("No pages yet")