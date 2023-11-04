#!/bin/bash
set -e

if [ -z "$GOPATH" ] ; then
	echo '$GOPATH is not set'
	exit 1
fi

myPath=$(realpath "$0")
myDir=$(dirname "$myPath")
parentDir=$(dirname "$myDir")

toolsRepoDir=$GOPATH/src/github.com/ParspooyeshFanavar/ibsng-go-tools/

if [ ! -d "$toolsRepoDir" ] ; then
	mkdir -p "$GOPATH/src/github.com/ParspooyeshFanavar"
	cd "$GOPATH/src/github.com/ParspooyeshFanavar"
	git clone https://github.com/ParspooyeshFanavar/ibsng-go-tools/
fi

cd "$toolsRepoDir/json-rpc/check-json/"
go build
./check-json "$parentDir"




