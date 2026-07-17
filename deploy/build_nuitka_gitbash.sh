#!/bin/bash

# Set script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Build apex_gui
echo "Building apex_gui"
python -m nuitka --standalone \
    --plugin-enable=pyside6 --include-qt-plugins=sensible \
    --include-data-file=apex-logo.ico=apex-logo.ico \
    --include-package=sqlalchemy \
    --include-package=google.protobuf \
    --output-dir=deploy/build sapient_apex_gui/apex_gui.py

# Build apex_replay_gui
echo "Building apex_replay_gui"
python -m nuitka --standalone \
    --plugin-enable=pyside6 --include-qt-plugins=sensible \
    --include-data-file=apex-logo.ico=apex-logo.ico \
    --include-package=sqlalchemy \
    --include-package=google.protobuf \
    --output-dir=deploy/build sapient_apex_replay_gui/replay_gui.py

# Build apex
echo "Building apex"
python -m nuitka \
  --standalone \
  --enable-plugin=pkg-resources \
  --enable-plugin=pylint-warnings \
  --include-package=apex \
  --include-package=google \
  --include-package=urllib3 \
  --include-package-data=urllib3 \
  --enable-plugin=pkg-resources \
  --include-package=fastapi \
  --include-package=uvicorn \
  --include-package=elasticsearch \
  --enable-plugin=data-files \
  --output-dir=deploy/build \
  --follow-imports \
  sapient_apex_server/apex.py


# Build replay

echo "Building replay"
python -m nuitka --standalone \
    --include-package=google.protobuf \
    --output-dir=deploy/build sapient_apex_replay/replay.py

# Clean up old 'bin' directory if it exists
if [ -d "deploy/bin" ]; then
    rm -rf deploy/bin
fi
mkdir -p deploy/bin

# Copy build outputs to 'deploy/bin'
cp -r deploy/build/apex_gui.dist/* deploy/bin
cp -r deploy/build/replay_gui.dist/* deploy/bin
cp -r deploy/build/apex.dist/* deploy/bin
cp -r deploy/build/replay.dist/* deploy/bin

# Return to the script's root folder
cd "$SCRIPT_DIR"

# Copy configuration and batch files
cp ../apex_config.json .
cp ../replay_config.json .
cp ../install_elastic.sh .
cp ../start_elastic.sh .

# Zip the build folder into a .zip file
echo "Zipping binaries"
python -c "
import zipfile, os, sys
items = sys.argv[1:]
with zipfile.ZipFile('apex.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for path in items:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    zf.write(fp)
        elif os.path.exists(path):
            zf.write(path)
" deploy/bin apex_config.json replay_config.json \
    elasticsearch-8.11.1 acknowledgements.txt install_elastic.sh start_elastic.sh run_all.sh

echo "Done"
