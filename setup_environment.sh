#!/bin/bash

# Determine the target directory for the virtual environment
if [ -n "$1" ]; then
    TARGET_DIR="$(realpath "$1")"
else
    TARGET_DIR="$(pwd)"
fi

# Define the virtual environment folder within the target directory
VENV_FOLDER="$TARGET_DIR/.venv"

# Function to create virtual environment and install dependencies
setup_environment() {
    if [ ! -d "$VENV_FOLDER" ]; then
        echo "Virtual environment not found at '$VENV_FOLDER'. Creating virtual environment..."
        python3 -m venv "$VENV_FOLDER"

        if [ $? -ne 0 ]; then
            echo "Error creating virtual environment. Ensure Python 3 is installed."
            exit 1
        fi
    else
        echo "Virtual environment already exists at '$VENV_FOLDER'."
    fi

    echo "Activating virtual environment..."
    # Check for OS and activate virtual environment accordingly
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        # For macOS/Linux
        source "$VENV_FOLDER/bin/activate"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # For Windows (Powershell/cmd)
        source "$VENV_FOLDER/Scripts/activate"
    else
        echo "Unsupported OS: $OSTYPE"
        exit 1
    fi

    if [ -f "$TARGET_DIR/requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install -r "$TARGET_DIR/requirements.txt"

        if [ $? -ne 0 ]; then
            echo "Error installing dependencies. Check your requirements.txt file."
            deactivate
            exit 1
        fi
    else
        echo "No requirements.txt found in $TARGET_DIR. Skipping dependency installation."
    fi
}

setup_environment
