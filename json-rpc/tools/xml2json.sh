#!/usr/bin/env bash
myPath=$(realpath "$0")
myDir=$(dirname "$myPath")

cd "$myDir"

python xml2json.py ../handlers_E.xml E ..
python xml2json.py ../handlers_D.xml D ..
python xml2json.py ../handlers_C.xml C ..

cd format-json
go build
./format-json ../../*/*.json
