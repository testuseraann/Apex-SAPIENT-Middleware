@echo off
REM Copyright (c) 2019-2024 Roke Manor Research Ltd
pushd "%~dp0\.."

echo Building apex_gui.exe
python -m nuitka --mingw64 --standalone ^
    --plugin-enable=pyside6 --include-qt-plugins=sensible,styles ^
    --windows-disable-console --windows-icon-from-ico=apex-logo.ico ^
    --include-data-file=apex-logo.ico=apex-logo.ico ^
    --include-package=google.protobuf ^
    --output-dir=deploy\build sapient_apex_gui\apex_gui.py

echo Building apex_replay_gui.exe
python -m nuitka --mingw64 --standalone ^
    --plugin-enable=pyside6 --include-qt-plugins=sensible,styles ^
    --windows-disable-console --windows-icon-from-ico=apex-logo.ico ^
    --include-data-file=apex-logo.ico=apex-logo.ico ^
    --include-package=google.protobuf ^
    --output-dir=deploy\build sapient_apex_replay_gui\replay_gui.py

echo Building apex.exe
python -m nuitka --mingw64 --standalone ^
    --enable-plugin=pkg-resources --enable-plugin=pylint-warnings --enable-plugin=data-files ^
    --include-package=sapient_apex_server --include-package=sapient_apex_api ^
    --include-package=sapient_msg --include-package=google.protobuf ^
    --include-package=fastapi --include-package=uvicorn --include-package=elasticsearch ^
    --follow-imports --windows-icon-from-ico=apex-logo.ico ^
    --output-dir=deploy\build sapient_apex_server\apex.py

echo Building replay.exe
python -m nuitka --mingw64 --standalone ^
    --include-package=google.protobuf ^
    --windows-icon-from-ico=apex-logo.ico ^
    --output-dir=deploy\build sapient_apex_replay\replay.py

if exist deploy\bin rd /s /q deploy\bin
mkdir deploy\bin

xcopy /y /q /s deploy\build\apex_gui.dist deploy\bin
xcopy /y /q /s deploy\build\replay_gui.dist deploy\bin
xcopy /y /q /s deploy\build\apex.dist deploy\bin
xcopy /y /q /s deploy\build\replay.dist deploy\bin
popd

pushd "%~dp0"
copy ..\apex_config.json .
copy ..\replay_config.json .
copy ..\install_elastic.bat .
copy ..\start_elastic.bat .

echo Zipping binaries
python -m zipfile -c apex.zip bin apex_config.json replay_config.json elasticsearch-8.11.1 acknowledgements.txt install_elastic.bat start_elastic.bat run_all.bat
popd

echo Done
