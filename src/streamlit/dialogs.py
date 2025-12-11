
import streamlit as st
import json
from src.models.enums import AvailableTemplates
from streamlit_image_select import image_select
from src.streamlit.processing import create_page_from_uploaded_data,process_table,generate_svg_from_json
from lxml import etree
import pandas as pd
@st.dialog("New page",dismissible=False)
def new_page_dialog():
    st.session_state.wizard_step = 0

    if st.session_state.document is None:
        document_name = st.text_input("Document name")
    title = st.text_input("Title")
    template = image_select(
        label="Select a template",
        images = ["src/streamlit/static/images/base.png", "src/streamlit/static/images/template2.png"],
        captions=[template.value for template in AvailableTemplates],
        use_container_width=False,
    )
    template = template.split("/")[-1].split(".")[0]
    st.session_state.new_page["template"] = template
    st.session_state.new_page["title"] = title
    if st.session_state.document is None and document_name != '':
        st.session_state.new_document_name = document_name
    isValid = title != '' and template

    if st.button("Next", use_container_width=True, disabled=not isValid,shortcut="Enter"):
        st.session_state.wizard_step = 2
        st.rerun()
    if st.button("Cancel", use_container_width=True):
        st.session_state.wizard_step = 0
        st.rerun()

@st.dialog("Upload files",width="large",dismissible=False)
def upload_files_dialog(template: AvailableTemplates):
    match template:
        case AvailableTemplates.BASE.value:
            upload_views_tab, upload_table_tab = st.tabs(["Upload views", "Upload table"])

            with upload_views_tab:
                st.subheader("Upload view")
                view_options = ["Front", "Back", "Left", "Right"]
                side = st.selectbox("Select view", view_options, key="view")
                col1,col2,col3 = st.columns(3)

                with col1:
                    image = st.file_uploader(
                        "Upload side projection",
                        type=["svg"],
                        accept_multiple_files=False,
                        key="upload_side_projection"
                    )

                    if image:
                        svg_string = image.getvalue().decode("utf-8")
                        st.image(svg_string, "Preview", width=400)

                with col2:
                    panorama = st.file_uploader(
                        "Upload panorama",
                        type=["jpg", "jpeg", "png"],
                        accept_multiple_files=False,
                        key="upload_panorama"
                    )
                    if panorama:
                        st.image(panorama,"Preview",width=400)
                with col3:
                    wall_data = st.file_uploader(
                        "Upload wall data",
                        type=["json"],
                        accept_multiple_files=False,
                        key="upload_wall"
                    )
                    if wall_data is not None:
                        wall_json = json.loads(wall_data.getvalue())
                        st.session_state.new_page["wall_data"] = wall_data

                        svg_element = generate_svg_from_json(wall_json,side)

                        svg_string = etree.tostring(svg_element, encoding="unicode", method="xml").strip()
                        st.image(svg_string, "Preview", width=400)
                if side is not None and image is not None and panorama is not None and wall_data and svg_element is not None:
                    # Store the SVG string (not the element) for processing in create_page_from_uploaded_data
                    svg_string = etree.tostring(svg_element, encoding="unicode", method="xml").strip() if svg_string is not None else ""
                    st.session_state.new_page["view"] = {"side": side, "image": image, "panorama": panorama, "wall_data": wall_json, "wall_image_svg": svg_string}

            with upload_table_tab:
                table = st.file_uploader(
                    "Upload table",
                    type=["csv"],
                    accept_multiple_files=False,
                    key="upload_table"
                )
                if table:
                    csv = pd.read_csv(table)
                    csv = process_table(csv)
                    new_edited = st.data_editor(csv,num_rows="dynamic",key="uploaded_table_editor")
                    edited_df = pd.DataFrame(new_edited)
                    st.session_state.new_page["table"] = edited_df
            isValid = side and wall_data and image and panorama and table
            if st.button("Back", use_container_width=True):
                st.session_state.wizard_step = 1
                st.rerun()
            if st.button("Cancel", use_container_width=True):
                st.session_state.wizard_step = 0
                st.session_state.current_action = ""

                st.rerun()
            if st.button("Create", use_container_width=True, disabled=not isValid,type="primary",shortcut="Enter"):
                # Create the page with uploaded data and save to backend
                with st.spinner("Creating page..."):
                    create_page_from_uploaded_data()
                st.session_state.show_confirm_success = True
                st.session_state.success_message = "Page created successfully!"
                st.rerun()

@st.dialog("Confirm dialog",dismissible=False)
def confirm_dialog(message, on_confirm, on_cancel = lambda: st.rerun()):
    st.write(message)
    col1, col2,col3 = st.columns(3)
    with col1:
        if st.button("Confirm", key="confirm", on_click=on_confirm, shortcut="Enter"):
            st.rerun()
    with col3:
        if st.button("Cancel", key="cancel", on_click=on_cancel, shortcut="Escape"):
            st.rerun()
    return True

