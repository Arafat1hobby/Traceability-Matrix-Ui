import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
from CsvDataReader import CsvDataReader
from JdceDataReader import JdceDataReader
import pandas as pd
from protocol import ProtocolDataExtractor
import tifffile
import os
import subprocess
import sys

# Set page config with modern theme
st.set_page_config(
    page_title="MXA Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }

    .stButton>button {
        border-radius: 25px;
        padding: 12px 28px;
        background: linear-gradient(135deg, #6B8DD6 0%, #8E37D7 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #8E37D7 0%, #6B8DD6 100%);
    }

    .stFileUploader>section>div {
        border: 2px dashed #6B8DD6;
        border-radius: 15px;
        background-color: rgba(107, 141, 214, 0.05);
    }

    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #6B8DD6;
        padding-bottom: 10px;
        font-size: 2.5rem;
    }

    .data-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 1px solid #dee2e6;
    }

    .filter-section {
        background: #ffffff;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def open_tiff_viewer():
    try:
        # Get the path to the Python executable in the virtual environment
        python_path = os.path.join(os.path.dirname(sys.executable), 'python.exe')
        command = [python_path, "imageData.py"]
        subprocess.Popen(command)
        st.success("🎉 Image viewer launched successfully!")

    except Exception as e:
        st.error(f"❌ Failed to open TIFF viewer: {e}")

def main_page():
    st.title("🔬 MXA Data Analyzer")

    # Image Viewer button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("📷 Launch Image Viewer"):
            open_tiff_viewer()

    # File uploaders
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("📁 Upload JDCE File", expanded=True):
                jdce_file = st.file_uploader("Select .jdce file", type=["jdce"], label_visibility="collapsed")
        with col2:
            with st.expander("📊 Upload CSV File", expanded=True):
                csv_file = st.file_uploader("Select .csv file", type=["csv"], label_visibility="collapsed")

    # Data display
    if jdce_file or csv_file:
        st.markdown("---")

        # Create dynamic layout columns
        if jdce_file and csv_file:
            col1, col2 = st.columns(2)
        else:
            # If only one file is uploaded, use full width
            col2 = st.container()

        # JDCE Data (only show if file exists)
        if jdce_file:
            with col1:
                with st.container():
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

        # CSV Data (always show if file exists)
        if csv_file:
            with col2:
                with st.container():
                    st.markdown("### 📈 CSV Data Analysis")
                    csv_reader = CsvDataReader(csv_file)
                    extracted_csv_data = csv_reader.extract_data()

                    if extracted_csv_data is not None:
                        # AgGrid configuration
                        gb = GridOptionsBuilder.from_dataframe(extracted_csv_data)
                        gb.configure_pagination()
                        gb.configure_side_bar()
                        gb.configure_default_column(
                            groupable=True,
                            value=True,
                            enableRowGroup=True,
                            aggFunc="sum",
                            editable=True
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

                        # Filter section
                        st.markdown("---")
                        st.markdown("### 🔍 Column Filter")

                        filter_col1, filter_col2 = st.columns(2)
                        with filter_col1:
                            selected_column = st.selectbox(
                                "Select Column to Filter:",
                                options=extracted_csv_data.columns,
                                index=0
                            )

                        unique_values = extracted_csv_data[selected_column].unique()

                        with filter_col2:
                            selected_value = st.selectbox(
                                f"Select {selected_column} Value:",
                                options=unique_values,
                                index=0
                            )

                        filtered_df = extracted_csv_data[extracted_csv_data[selected_column] == selected_value]

                        with st.expander(f"📋 Filtered Results for {selected_column} = {selected_value}", expanded=True):
                            st.dataframe(
                                filtered_df.style
                                .set_properties(**{'background-color': '#f8f9fa', 'border': '1px solid #dee2e6'})
                                .set_table_styles([{
                                    'selector': 'th',
                                    'props': [('background-color', '#6B8DD6'), ('color', 'white')]
                                }]),
                                use_container_width=True
                            )

                            csv = filtered_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Filtered Data",
                                data=csv,
                                file_name=f"filtered_{selected_column}_{selected_value}.csv",
                                mime="text/csv"
                            )


def protocol_data_page():
    extractor = ProtocolDataExtractor()

    st.title("⚙️ Protocol Data Explorer")

    with st.container():
        with st.expander("📂 Upload Protocol File", expanded=True):
            mxprotocol_file = st.file_uploader("Select .mxprotocol file", type=["mxprotocol"],
                                               label_visibility="collapsed")

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


# Sidebar navigation
page_names_to_funcs = {
    "🔬 MXA Analyzer": main_page,
    "⚙️ Protocol Data": protocol_data_page,
}

with st.sidebar:
    st.title("🧭 Navigation")
    st.image("https://cdn-icons-png.flaticon.com/512/1534/1534959.png", width=80)
    selected_page = st.radio("Choose a module:", page_names_to_funcs.keys(), index=0)

page_names_to_funcs[selected_page]()