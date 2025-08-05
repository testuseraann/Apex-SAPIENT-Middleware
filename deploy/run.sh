#!/bin/bash

# Install required libraries
pip install -r requirements.txt

# Run apex.dist/apex.bin in the background
# ./bin/apex.bin &
# Start Python backend
PYTHONPATH=../ python3 ../sapient_apex_server/apex.py &
PYTHON_PID=$!

# Wait 4 seconds
sleep 4

# Start GUI
./bin/apex_gui.bin &
GUI_PID=$!

# Wait for GUI to exit
wait $GUI_PID

# Kill Python backend when GUI exits
kill $PYTHON_PID
