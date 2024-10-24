#!/bin/bash

# Make sure script is executed from the parent directory
if [ ! $(basename "$(pwd)") = "akai_mpk_mini_flasher" ]; then
    echo "ERROR: Must be run from the 'akai_mpk_mini_flasher' directory."
    exit 1
fi

# Install or just activate virtual environment
if [ ! -f "venv/bin/activate" ]; then
    python3 -m venv venv || python -m venv venv
    source venv/bin/activate
else
    source venv/bin/activate
fi

pip install -r requirements.txt

echo 'Virtual environment installed in ./venv/'
