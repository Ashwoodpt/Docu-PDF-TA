import streamlit as st
from src.streamlit.dialogs import new_page_dialog
from src.streamlit.processing import save_document
from src.streamlit.dynamic.page_list_component import render_page_list_component
from src.streamlit.state_manager import state_manager
from src.render.template_engine import engine


def sidebar() -> None:
    """
    Render the sidebar UI component in the Streamlit application.
    The sidebar includes Redis connection status, document management buttons,
    and page navigation controls when a document is loaded.
    """
    document = state_manager.get_current_document()
    current_index = state_manager.get_current_page_index()

    with st.sidebar:
        # Display Redis connection status
        if state_manager.check_asset_manager_health():
            st.success("✅ Redis Connected")
        else:
            st.warning("⚠️ Redis Disconnected (Using Local Storage)")

        if document is not None:
            st.button("Add a new page", key="new page", on_click=new_page_dialog, use_container_width=True,shortcut="CTRL+Q")
            if st.button("Save document", key="save document", use_container_width=True,shortcut="CTRL+S"):
                save_document()
            with st.container(horizontal_alignment="distribute"):
                if st.button("Edit page", key="edit page", use_container_width=True,shortcut="CTRL+E"):
                    state_manager.app_state.is_editing = not state_manager.app_state.is_editing
                if st.button("Back", key="back", use_container_width=True,shortcut="Escape"):
                    if state_manager.app_state.is_save_on_exit:
                        save_document()
                    state_manager.app_state.is_editing = False
                    state_manager.reset_document_state()
                    list = state_manager.update_document_list()
                    state_manager.app_state.document_list = list
                    st.rerun()
        st.toggle("Save on exit?", key="save_on_exit", value=state_manager.app_state.is_save_on_exit,on_change=state_manager.toggle_save_on_exit)


        st.divider()
        if document is not None:
            st.header(document.name,text_alignment="center")
            
        if document is not None and document.pages:
            # Convert PageContext objects to JSON-serializable dictionaries
            pages_serializable = [page.model_dump() for page in document.pages]
            context = {
                "embedded_css": state_manager.get_embedded_css(),
                "pages": pages_serializable,
                "active_page": current_index + 1
            }
            page_list_event = render_page_list_component(
                engine=engine,
                context=context,
                key=f"page_list_component{hash(str(len(pages_serializable)))}",
                events=True
            )
            
            if page_list_event:
                selected_page = page_list_event.get("index", 0)

                match page_list_event.get("action", ""):
                    case "open_page":
                        if(selected_page != current_index):
                            state_manager.open_page(selected_page)
                    case "delete_page":
                        state_manager.delete_page(page_list_event.get("index"))
                    case _:
                        pass
                page_list_event = None                

        else:
            st.write("No pages yet")