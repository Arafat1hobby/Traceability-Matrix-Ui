import json

class ProtocolDataExtractor:
    """
    Extracts and organizes data from a .mxprotocol file
    in a human-readable format.
    """

    def extract_data(self, json_data):
        """
        Extracts data from the JSON content.
        """
        try:
            data = json.loads(json_data)
            extracted_data = {}

            # Function to extract nested data
            def extract_nested_data(source, keys):
                result = {}
                for key, label in keys.items():
                    value = source
                    for part in key.split('.'):
                        value = value.get(part, {})
                    result[label] = value if value else ""
                return result

            # Define the keys to extract for the acquisition engine protocol with proper labels
            acquisition_keys = {
                'commandId': 'Command ID',
                'commandName': 'Command Name',
                'protocolDefinition.protocolName': 'Protocol Name',
                'protocolDefinition.acquisitionName': 'Acquisition Name',
                'commandData.acquisitionEngineProtocol.commandDefinitions': 'Command Definitions',
                'commandData.acquisitionEngineProtocol.data.devicePositions': 'Device Positions',
                'commandData.acquisitionEngineProtocol.data.labwareDefinition': 'Labware Definition',
                'commandData.acquisitionEngineProtocol.data.siteList': 'Site List',
                'commandData.acquisitionEngineProtocol.data.wellList': 'Well List',
                'protocolDefinition.commandSequence.commands': 'Command Sequence',
                'protocolDefinition.fileSaveLocation': 'File Save Location',
                'protocolDefinition.isInteractiveProtocol': 'Is Interactive Protocol',
                'protocolDefinition.mxProtocolFilePath': 'MX Protocol File Path',
                'protocolDefinition.postProcessingOptions': 'Post Processing Options',
                'protocolDefinition.sendShadingCorrectedImagesToUi': 'Send Shading Corrected Images to UI',
                'protocolName': 'Protocol Name',
                'protocolVersion': 'Protocol Version'
            }

            # Extract data using the defined keys
            extracted_data['Acquisition Engine Protocol'] = extract_nested_data(data.get('acquisitionEngineProtocol', {}), acquisition_keys)

            # Extract UI Model data (unchanged)
            ui_keys = [
                'acquisitionName', 'objective.name', 'objective.magnification',
                'cameraName', 'autofocus.channel.channelName', 'autofocus.autofocusSettingsPerObjectiveList',
                'targetedAcquisition.enabled', 'targetedAcquisition.parameters',
                'timeSeries.enabled', 'timeSeries', 'zSeries.enabled', 'zSeries',
                'wellsSitesData'
                # Add other relevant fields you want to extract from ui
            ]
            extracted_data['UI Model'] = extract_nested_data(data.get('uiModel', {}), {key: key for key in ui_keys})

            return extracted_data

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")  # Print the error
            return None
        except Exception as e:
            print(f"An error occurred while processing JSON data: {e}")  # Print the error
            return None