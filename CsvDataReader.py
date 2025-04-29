import pandas as pd
import streamlit as st

class CsvDataReader:
    """
    Reads and processes data from a CSV file.
    """

    def __init__(self, csv_file):
        """
        Initializes CsvDataReader with a CSV file.
        """
        self.csv_file = csv_file

    def extract_data(self):
        """
        Extracts data from the CSV file and reorders columns.
        """
        try:
            df = pd.read_csv(self.csv_file)

            # Reorder columns with ImageFileName first
            cols = df.columns.tolist()
            cols.insert(0, cols.pop(cols.index('ImageFileName')))
            cols.insert(1, cols.pop(cols.index('Well')))
            cols.insert(2, cols.pop(cols.index('PositionXUm')))
            cols.insert(3, cols.pop(cols.index('PositionYUm')))
            cols.insert(4, cols.pop(cols.index('PositionZUm')))
            cols.insert(5, cols.pop(cols.index('ExcitationEmissionFilter')))
            df = df[cols]

            return df
        except Exception as e:
            st.error(f"An error occurred while processing CSV data: {e}")
            return None