#!/bin/bash

# Set script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# # Build apex_gui
# echo "Building apex_gui"
# python3 -m nuitka --standalone \
#     --plugin-enable=pyside6 --include-qt-plugins=sensible \
#     --include-data-file=apex-logo.ico=apex-logo.ico \
#     --include-package=sqlalchemy \
#     --include-package=google.protobuf \
#     --output-dir=deploy/build sapient_apex_gui/apex_gui.py

# # Build apex_replay_gui
# echo "Building apex_replay_gui"
# python3 -m nuitka --standalone \
#     --plugin-enable=pyside6 --include-qt-plugins=sensible \
#     --include-data-file=apex-logo.ico=apex-logo.ico \
#     --include-package=sqlalchemy \
#     --include-package=google.protobuf \
#     --output-dir=deploy/build sapient_apex_replay_gui/replay_gui.py

# Build apex
echo "Building apex"
python3 -m nuitka \
  --standalone \
  --enable-plugin=pkg-resources \
  --enable-plugin=pylint-warnings \
  --enable-plugin=data-files \
  --include-package=sapient_apex_server \
  --include-package=sapient_apex_api \
  --include-package=sapient_msg \
  --include-package=google.protobuf \
  --include-package=fastapi \
  --include-package=uvicorn \
  --include-package=elasticsearch \
  --include-package=urllib3 \
  --include-package-data=urllib3 \
  --include-distribution-metadata=urllib3 \
  --output-dir=deploy/build \
  --follow-imports \
  sapient_apex_server/apex.py


# # Build replay

# echo "Building replay"
# python3 -m nuitka --standalone \
#     --include-package=google.protobuf \
#     --output-dir=deploy/build sapient_apex_replay/replay.py

# # Clean up old 'bin' directory if it exists
# if [ -d "deploy/bin" ]; then
#     rm -rf deploy/bin
# fi
# mkdir -p deploy/bin

# # Copy build outputs to 'deploy/bin'
# cp -r deploy/build/apex_gui.dist/* deploy/bin
# cp -r deploy/build/replay_gui.dist/* deploy/bin
# cp -r deploy/build/apex.dist/* deploy/bin
# cp -r deploy/build/replay.dist/* deploy/bin

# # Return to the script's root folder
# cd "$SCRIPT_DIR"

# # Copy configuration and batch files
# cp ../apex_config.json .
# cp ../replay_config.json .
# cp ../install_elastic.sh .
# cp ../start_elastic.sh .

# # Zip the build folder into a .zip file
# echo "Zipping binaries"
# zip -r apex.zip deploy/bin apex_config.json replay_config.json \
#     elasticsearch-8.11.1 acknowledgements.txt install_elastic.sh start_elastic.sh run_all.sh

echo "Done"
