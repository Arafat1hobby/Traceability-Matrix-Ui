#!/bin/bash

# Define the path to the virtual environment
VENV_PATH="D:/MXA Analyzer/.venv"

# Check if the virtual environment directory exists
if [[ ! -d "$VENV_PATH" ]]; then
    echo "Virtual environment directory does not exist: $VENV_PATH"
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/Scripts/activate"

# Check if the virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment is activated."
else
    echo "Failed to activate the virtual environment."
    exit 1
fi

# Define the path to main1.py
MAIN_FILE="D:/MXA Analyzer/main1.py"

# Check if main1.py exists
if [[ ! -f "$MAIN_FILE" ]]; then
    echo "main1.py not found at $MAIN_FILE"
    exit 1
else
    echo "Found main1.py at $MAIN_FILE"
fi

# Run main1.py using streamlit
echo "Running main1.py using streamlit..."
streamlit run "$MAIN_FILE"

# Check the exit status of the streamlit command
if [[ $? -ne 0 ]]; then
    echo "Failed to run main1.py using streamlit."
    exit 1
else
    echo "main1.py is running successfully."
fi