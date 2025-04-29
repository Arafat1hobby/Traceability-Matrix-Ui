import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
from CsvDataReader import CsvDataReader
from JdceDataReader import JdceDataReader
from protocol import ProtocolDataExtractor
import pandas as pd
from PIL import Image, ImageEnhance
import tifffile
import io
import xml.etree.ElementTree as ET

# Set page config with modern theme
st.set_page_config(
    page_title="MXA Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- TIFF VIEWER (WEB VERSION) ---
def tiff_viewer_page():
    st.title("🖼️ TIFF Image Viewer (Web-Based)")

    uploaded_file = st.file_uploader("Upload a 16-bit TIFF image", type=["tif", "tiff"])

    if uploaded_file:
        try:
            tiff_bytes = uploaded_file.read()
            with tifffile.TiffFile(io.BytesIO(tiff_bytes)) as tif:
                image = tif.pages[0].asarray()
                metadata_raw = tif.pages[0].tags.get("ImageDescription")
                description = metadata_raw.value if metadata_raw else None

            # Convert to 8-bit for display
            image_8bit = (image / 256).astype('uint8')
            pil_img = Image.fromarray(image_8bit)

            # Adjustments
            st.sidebar.markdown("### 🔧 Adjustments")
            brightness = st.sidebar.slider("Brightness", 0.1, 2.0, 1.0)
            contrast = st.sidebar.slider("Contrast", 0.1, 2.0, 1.0)

            pil_img = ImageEnhance.Brightness(pil_img).enhance(brightness)
            pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)

            st.image(pil_img, use_column_width=True, caption="TIFF Preview")

            if description:
                try:
                    root = ET.fromstring(description)
                    st.markdown("### 🧬 Metadata")
                    for prop in root.findall(".//prop"):
                        st.text(f"{prop.get('id')}: {prop.get('value')}")
                except ET.ParseError:
                    st.warning("⚠️ Metadata could not be parsed.")
        except Exception as e:
            st.error(f"Failed to process TIFF: {e}")


# --- CSV + JDCE ANALYZER ---
def main_analyzer_page():
    st.title("🔬 MXA Data Analyzer")

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📁 Upload JDCE File", expanded=True):
            jdce_file = st.file_uploader("Select .jdce file", type=["jdce"], label_visibility="collapsed")
    with col2:
        with st.expander("📊 Upload CSV File", expanded=True):
            csv_file = st.file_uploader("Select .csv file", type=["csv"], label_visibility="collapsed")

    if jdce_file or csv_file:
        st.markdown("---")

        if jdce_file and csv_file:
            col1, col2 = st.columns(2)
        else:
            col2 = st.container()

        if jdce_file:
            with col1:
                st.markdown("### 📄 JDCE Data Analysis")
                jdce_reader = JdceDataReader(jdce_file)
                extracted_jdce_data = jdce_reader.extract_data()
                if extracted_jdce_data:
                    for category, data in extracted_jdce_data.items():
                        with st.expander(f"📂 {category}"):
                            if isinstance(data, (dict, list)):
                                df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
                                st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
                            else:
                                st.write(data)

        if csv_file:
            with col2:
                st.markdown("### 📈 CSV Data Analysis")
                csv_reader = CsvDataReader(csv_file)
                extracted_csv_data = csv_reader.extract_data()
                if extracted_csv_data is not None:
                    gb = GridOptionsBuilder.from_dataframe(extracted_csv_data)
                    gb.configure_pagination()
                    gb.configure_side_bar()
                    gb.configure_default_column(
                        groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True
                    )
                    gridOptions = gb.build()

                    AgGrid(
                        extracted_csv_data,
                        gridOptions=gridOptions,
                        update_mode=GridUpdateMode.MODEL_CHANGED,
                        allow_unsafe_jscode=True,
                        height=500,
                        width='100%',
                        theme='material'
                    )

                    st.markdown("---")
                    st.markdown("### 🔍 Column Filter")
                    filter_col1, filter_col2 = st.columns(2)
                    with filter_col1:
                        selected_column = st.selectbox("Select Column to Filter:", options=extracted_csv_data.columns, index=0)
                    with filter_col2:
                        selected_value = st.selectbox(
                            f"Select {selected_column} Value:", options=extracted_csv_data[selected_column].unique(), index=0
                        )

                    filtered_df = extracted_csv_data[extracted_csv_data[selected_column] == selected_value]
                    with st.expander(f"📋 Filtered Results for {selected_column} = {selected_value}", expanded=True):
                        st.dataframe(filtered_df, use_container_width=True)
                        csv = filtered_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Filtered Data",
                            data=csv,
                            file_name=f"filtered_{selected_column}_{selected_value}.csv",
                            mime="text/csv"
                        )


# --- PROTOCOL PARSER PAGE ---
def protocol_data_page():
    extractor = ProtocolDataExtractor()
    st.title("⚙️ Protocol Data Explorer")

    with st.expander("📂 Upload Protocol File", expanded=True):
        mxprotocol_file = st.file_uploader("Select .mxprotocol file", type=["mxprotocol"], label_visibility="collapsed")

    if mxprotocol_file:
        with st.spinner("🔍 Analyzing protocol data..."):
            json_content = mxprotocol_file.read().decode("utf-8")
            extracted_data = extractor.extract_data(json_content)
            if extracted_data:
                st.success("✅ Data extracted successfully!")
                for category, data in extracted_data.items():
                    with st.expander(f"📁 {category}"):
                        if isinstance(data, dict):
                            st.json(data)
                        else:
                            st.write(data)


# --- SIDEBAR NAVIGATION ---
page_names_to_funcs = {
    "🔬 MXA Analyzer": main_analyzer_page,
    "🖼️ TIFF Viewer": tiff_viewer_page,
    "⚙️ Protocol Data": protocol_data_page,
}

with st.sidebar:
    st.title("🧭 Navigation")
    st.image("https://cdn-icons-png.flaticon.com/512/1534/1534959.png", width=80)
    selected_page = st.radio("Choose a module:", page_names_to_funcs.keys(), index=0)

page_names_to_funcs[selected_page]()
