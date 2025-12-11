import streamlit as st
from src.streamlit.dialogs import new_page_dialog,confirm_dialog
from src.streamlit.processing import save_document
from st_clickable_images import clickable_images
from src.streamlit.state_manager import update_document_list
def sidebar() -> None:
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
            if st.button("Edit page", key="edit page", use_container_width=True,shortcut="CTRL+E"):
                st.session_state.isEditing = not st.session_state.isEditing
            if st.button("Back", key="back", use_container_width=True,shortcut="Escape"):
                def save_and_back():
                    save_document()
                    st.session_state.isEditing = False
                    st.session_state.document = None
                    update_document_list()
                confirm_dialog("Save changes?", on_confirm=save_and_back, on_cancel=None)


        st.divider()
        if st.session_state.document is not None:
            st.subheader(st.session_state.document.name)
        if st.session_state.document is not None and st.session_state.document.pages:
            # Create a list of page titles for the radio button
            page_titles = [page.page_title for page in st.session_state.document.pages]
            page_previews = [page.preview_url for page in st.session_state.document.pages]
            # Get current page index based on current_page state
            preview_image_style = {
                "width": "100%",
                "height": "auto",
                "margin-bottom": "20px",
                "transition": "transform .2s ease-in-out",
                "border-radius": "15px",
                "cursor": "pointer",
            }
            selected_page = clickable_images(page_previews, titles=page_titles, key="page",img_style=preview_image_style)
            current_page_index = st.session_state.get("current_page_index", 0) if "current_page_index" in st.session_state else 0
            if selected_page != current_page_index:
                st.session_state.current_page_index = selected_page

        else:
            st.write("No pages yet")