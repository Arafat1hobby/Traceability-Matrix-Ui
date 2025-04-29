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

# Set page config
st.set_page_config(
    page_title="MXA Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
if "jdce_file" not in st.session_state:
    st.session_state.jdce_file = None
    st.session_state.jdce_data = None

if "csv_file" not in st.session_state:
    st.session_state.csv_file = None
    st.session_state.csv_data = None

if "tiff_file" not in st.session_state:
    st.session_state.tiff_file = None
    st.session_state.tiff_metadata = None
    st.session_state.tiff_image = None

if "protocol_file" not in st.session_state:
    st.session_state.protocol_file = None
    st.session_state.protocol_data = None


# --- TIFF VIEWER PAGE ---
def tiff_viewer_page():
    st.title("🖼️ TIFF Image Viewer (Web-Based)")

    uploaded = st.file_uploader("Upload a 16-bit TIFF image", type=["tif", "tiff"])

    if uploaded:
        st.session_state.tiff_file = uploaded

    if st.session_state.tiff_file:
        try:
            tiff_bytes = st.session_state.tiff_file.read()
            with tifffile.TiffFile(io.BytesIO(tiff_bytes)) as tif:
                image = tif.pages[0].asarray()
                metadata_raw = tif.pages[0].tags.get("ImageDescription")
                description = metadata_raw.value if metadata_raw else None

            image_8bit = (image / 256).astype('uint8')
            pil_img = Image.fromarray(image_8bit)

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


# --- MXA ANALYZER PAGE ---
def main_analyzer_page():
    st.title("🔬 MXA Data Analyzer")

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📁 Upload JDCE File", expanded=True):
            jdce_file = st.file_uploader("Select .jdce file", type=["jdce"], label_visibility="collapsed")
            if jdce_file:
                st.session_state.jdce_file = jdce_file
                reader = JdceDataReader(jdce_file)
                st.session_state.jdce_data = reader.extract_data()

    with col2:
        with st.expander("📊 Upload CSV File", expanded=True):
            csv_file = st.file_uploader("Select .csv file", type=["csv"], label_visibility="collapsed")
            if csv_file:
                st.session_state.csv_file = csv_file
                reader = CsvDataReader(csv_file)
                st.session_state.csv_data = reader.extract_data()

    if st.session_state.jdce_data or st.session_state.csv_data:
        st.markdown("---")
        col1, col2 = st.columns(2)

        if st.session_state.jdce_data:
            with col1:
                st.markdown("### 📄 JDCE Data Analysis")
                for category, data in st.session_state.jdce_data.items():
                    with st.expander(f"📂 {category}"):
                        if isinstance(data, (dict, list)):
                            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
                            st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
                        else:
                            st.write(data)

        if st.session_state.csv_data is not None:
            with col2:
                st.markdown("### 📈 CSV Data Analysis")
                df = st.session_state.csv_data

                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_pagination()
                gb.configure_side_bar()
                gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
                gridOptions = gb.build()

                AgGrid(
                    df,
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
                    selected_column = st.selectbox("Select Column to Filter:", options=df.columns, index=0)
                with filter_col2:
                    selected_value = st.selectbox(
                        f"Select {selected_column} Value:", options=df[selected_column].unique(), index=0
                    )

                filtered_df = df[df[selected_column] == selected_value]
                with st.expander(f"📋 Filtered Results for {selected_column} = {selected_value}", expanded=True):
                    st.dataframe(filtered_df, use_container_width=True)
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Filtered Data",
                        data=csv,
                        file_name=f"filtered_{selected_column}_{selected_value}.csv",
                        mime="text/csv"
                    )


# --- PROTOCOL VIEWER PAGE ---
def protocol_data_page():
    st.title("⚙️ Protocol Data Explorer")

    with st.expander("📂 Upload Protocol File", expanded=True):
        mxprotocol_file = st.file_uploader("Select .mxprotocol file", type=["mxprotocol"], label_visibility="collapsed")
        if mxprotocol_file:
            st.session_state.protocol_file = mxprotocol_file
            content = mxprotocol_file.read().decode("utf-8")
            extractor = ProtocolDataExtractor()
            st.session_state.protocol_data = extractor.extract_data(content)

    if st.session_state.protocol_data:
        st.success("✅ Data extracted successfully!")
        for category, data in st.session_state.protocol_data.items():
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
    selected_page = st.radio("Choose a module:", list(page_names_to_funcs.keys()), index=0)

# Render selected page
page_names_to_funcs[selected_page]()
