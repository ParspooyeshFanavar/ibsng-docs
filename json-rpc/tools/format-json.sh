#!/bin/bash
set -e

DIR=$(dirname $0)

cd $DIR/format-json/
go build -o format-json.bin
cd -

$DIR/format-json/format-json.bin "$@"
