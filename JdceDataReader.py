import json
import streamlit as st
import pandas as pd

class JdceDataReader:
    """
    Reads and processes data from a .jdce file.
    """

    def __init__(self, jdce_file):
        """
        Initializes JdceDataReader with a .jdce file.
        """
        self.jdce_file = jdce_file

    def clean_data(self, jdce_string):
        """
        Placeholder for cleaning the .jdce data.
        """
        # Add your data cleaning logic here if necessary.
        return jdce_string

    def extract_data(self):
        """
        Extracts and categorizes data from the .jdce file content.
        """
        try:
            jdce_content = self.jdce_file.read().decode("utf-8")
            cleaned_data = self.clean_data(jdce_content)
            data = json.loads(cleaned_data)

            extracted_data = {}

            # --- General Information ---
            image_stack = data.get('ImageStack', {})
            extracted_data['General Information'] = {
                'Version': data.get('Version'),
                'PlateId': image_stack.get('PlateId'),
                'Uuid': image_stack.get('Uuid'),
                'ImageFormat': image_stack.get('ImageFormat'),
                'LargeImage': image_stack.get('LargeImage'),
                'CollectionComplete': image_stack.get('CollectionComplete')
            }

            # --- Application Details ---
            application = image_stack.get('Application', {})
            extracted_data['Application Details'] = {
                'Name': application.get('Name'),
                'SoftwareLabel': application.get('SoftwareLabel')
            }

            # --- Creation Timestamp ---
            creation = image_stack.get('Creation', {})
            extracted_data['Creation Timestamp'] = {
                'Date': creation.get('Date'),
                'Time': creation.get('Time'),
                'TimeZoneOffset': creation.get('TimeZoneOffset')
            }

            # --- AutoLead Acquisition Protocol ---
            auto_lead_protocol = image_stack.get('AutoLeadAcquisitionProtocol', {})

            # --- Camera Settings ---
            camera = auto_lead_protocol.get('Camera', {})
            extracted_data['Camera Settings'] = {
                'Width': camera.get('Size', {}).get('Width'),
                'Height': camera.get('Size', {}).get('Height'),
                'Binning': camera.get('Binning')
            }

            # --- Objective Calibration ---
            objective_calibration = auto_lead_protocol.get('ObjectiveCalibration', {})
            extracted_data['Objective Calibration'] = {
                'Unit': objective_calibration.get('Unit'),
                'ObjectiveName': objective_calibration.get('ObjectiveName'),
                'PixelWidth': objective_calibration.get('PixelWidth'),
                'PixelHeight': objective_calibration.get('PixelHeight')
            }

            # --- Plate Information ---
            plate = auto_lead_protocol.get('Plate', {})
            extracted_data['Plate Information'] = {
                'Name': plate.get('Name'),
                'Rows': plate.get('Rows'),
                'Columns': plate.get('Columns'),
                'TopLeftWellCenterOffset': plate.get('TopLeftWellCenterOffset'),
                'WellParameters': plate.get('WellParameters'),
                'WellSpacing': plate.get('WellSpacing')
            }

            # --- Wavelength Settings ---
            wavelengths = []
            wavelength_data = auto_lead_protocol.get('Wavelengths', [])
            for wl in wavelength_data:
                wavelengths.append({
                    'Index': wl.get('Index'),
                    'ImagingMode': wl.get('ImagingMode'),
                    'ZSlice': wl.get('ZSlice'),
                    'ZStep': wl.get('ZStep'),
                    'EmissionFilter': wl.get('EmissionFilter'),
                    'ExcitationFilter': wl.get('ExcitationFilter')
                })
            extracted_data['Wavelength Settings'] = wavelengths

            # --- Plate Map Parameters ---
            plate_map = auto_lead_protocol.get('PlateMap', {})
            extracted_data['Plate Map Parameters'] = {
                'ZDimensionParameters': plate_map.get('ZDimensionParameters'),
                'TimeSchedule': plate_map.get('TimeSchedule')
            }

            # --- Project Information ---
            project_info = auto_lead_protocol.get('ProjectInformation', {})
            extracted_data['Project Information'] = {
                'ProjectName': project_info.get('Project', {}).get('Name'),
                'UserName': project_info.get('User', {}).get('Name')
            }

            # --- Operator Information ---
            operator = image_stack.get('Operator', {})  # Access Operator within ImageStack
            extracted_data['Operator Information'] = {
                'Login': operator.get('Login')
            }

            # --- Specimen Holder ---
            specimen_holder = image_stack.get('SpecimenHolder', {})  # Access SpecimenHolder within ImageStack
            extracted_data['Specimen Holder'] = {
                'Type': specimen_holder.get('Type'),
                'Label': specimen_holder.get('Label'),
                'Barcode': specimen_holder.get('Barcode'),
                'Description': specimen_holder.get('Description')
            }

            # --- Image Metadata Files ---
            image_metadata_files = image_stack.get('ImageMetadataFiles', [])
            extracted_data['Image Metadata Files'] = {
                'Filename': image_metadata_files[0] if image_metadata_files else None
            }

            return extracted_data

        except json.JSONDecodeError as e:
            st.error(f"Error decoding JDCE JSON: {e}")
            return None
        except Exception as e:
            st.error(f"An error occurred while processing JDCE data: {e}")
            return None