import streamlit as st
import pandas as pd
import json
from src.streamlit.processing import generate_svg_from_json,process_table,save_uploaded_file_to_asset_manager,update_page_from_edits,save_wall_projection_to_asset_manager,save_document
from src.models.context_model import TableData
from src.models.enums import ViewType
from lxml import etree

def edit_page() -> None:
    """
    Render the page editing UI component in the Streamlit application.
    This function provides controls to edit page content including side views,
    panorama images, wall projections, and table data, with changes tracked
    in pending changes until the user saves them.
    """
    page = st.session_state.document.pages[st.session_state.current_page_index]
    pending_view = page.views[0].copy()
    st.space(12)
    if pending_view is not None:
        with st.container(horizontal=True,vertical_alignment="center"):
            side_image = st.session_state.document.pages[st.session_state.current_page_index].views[0].image
            with st.container(width='content'):
                st.image(side_image,width=400,caption="Side View")

            new_side_image = st.file_uploader("Replace", type=["svg"], key="replace_side_image",accept_multiple_files=False)
            if new_side_image is not None:
                svg_image = new_side_image.getvalue()
                
                new_image_url = save_uploaded_file_to_asset_manager(new_side_image, asset_prefix="side", is_svg=True)
                pending_view.image = new_image_url

                svg_string = svg_image.decode("utf-8")
                if new_side_image:
                    st.image(svg_string,width=400,caption="New side view")

        with st.container(horizontal=True,vertical_alignment="center"):
            pano_image = st.session_state.document.pages[st.session_state.current_page_index].views[0].pano
            st.image(pano_image,width=400,caption="Pano View")
            new_pano_image = st.file_uploader("Replace", type=["png", "jpg", "jpeg"], key="replace_pano_image",accept_multiple_files=False)
            if new_pano_image:
                new_pano_image_url = save_uploaded_file_to_asset_manager(new_pano_image, asset_prefix="pano", is_svg=False)
                pending_view.pano = new_pano_image_url
                st.image(new_pano_image.getvalue(),width=400,caption="New pano view")

        with st.container(horizontal=True,vertical_alignment="top"):
            side = st.session_state.document.pages[st.session_state.current_page_index].views[0].side
            with st.container():
                available_sides=["Front", "Back", "Left", "Right"]
                side = st.session_state.document.pages[st.session_state.current_page_index].views[0].side
                side_index = available_sides.index(side.value)
                new_side = st.selectbox("Replace highlight direction", available_sides, index=side_index, key="replace_side")

                wall_data = st.session_state.document.pages[st.session_state.current_page_index].views[0].wall_data
                new_json = st.file_uploader("Replace", type=["json"], key="replace_json",accept_multiple_files=False)

            if new_json:
                new_data = json.loads(new_json.getvalue())
                svg_element = generate_svg_from_json(new_data,new_side)
                svg_string = etree.tostring(svg_element, encoding="unicode", method="xml").strip()
                st.image(svg_string,width=400,caption="New wall view")
                svg_url = save_wall_projection_to_asset_manager(svg_string)
                pending_view.wall_data = new_data
                pending_view.wall_image = svg_url
            elif new_side:
                svg_element = generate_svg_from_json(wall_data, new_side)
                svg_string = etree.tostring(svg_element, encoding="unicode", method="xml").strip()
                st.image(svg_string,width=400,caption="New wall view")
                svg_url = save_wall_projection_to_asset_manager(svg_string)

                new_side = ViewType(new_side)
                if new_side != side:
                    pending_view.wall_image = svg_url
                    pending_view.side = new_side
                    
    if pending_view != page.views[0]:
        st.session_state.pending_changes["view"] = pending_view
    else:
        if "view" in st.session_state.pending_changes:
            del st.session_state.pending_changes["view"]
        
    pending_table = st.session_state.document.pages[st.session_state.current_page_index].table_data.copy()
    new_table_data = st.file_uploader("Replace", type=["csv"], key="replace_table_data",accept_multiple_files=False)
    if new_table_data is None:
        table_data = pending_table
        df = pd.DataFrame(table_data.data, columns=table_data.headers)
        edited = st.data_editor(df,num_rows='dynamic',key="table_data")
        pending_table = pd.DataFrame(edited)
        headers = pending_table.columns.tolist()
        data = pending_table.to_dict('records')
        pending_table = TableData(headers=headers, data=data)
    else:
        new_csv = pd.read_csv(new_table_data)
        new_csv = process_table(new_csv)
        new_edited = st.data_editor(new_csv,num_rows='dynamic',key="replaced_table_data")
        edited_df = pd.DataFrame(new_edited)
        headers = edited_df.columns.tolist()
        data = edited_df.to_dict('records')
        pending_table = TableData(headers=headers, data=data)

    if pd.DataFrame(page.table_data.data, columns=page.table_data.headers).equals(pd.DataFrame(pending_table.data, columns=pending_table.headers)) == False:
        st.session_state.pending_changes["table"] = pending_table
    else:
        if "table" in st.session_state.pending_changes:
            del st.session_state.pending_changes["table"]

    with st.container(horizontal_alignment="right"):
        if st.button("Save", key="save_edit",shortcut="ALT+s"):
            update_page_from_edits()
            save_document()
            st.rerun()
