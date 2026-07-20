#!/bin/bash
export PYDANTIC_DISABLE_PLUGINS=1
exec "$(dirname "$0")/deploy/build/apex.dist/apex.bin" "$@"
