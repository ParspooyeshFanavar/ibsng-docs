package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/tidwall/pretty"

	openrpc_document "github.com/ParspooyeshFanavar/meta-schema"
)

func main() {
	dirPath, err := filepath.Abs("../..")
	if err != nil {
		panic(err)
	}
	branches := []string{"E", "D", "C"}
	for _, branch := range branches {
		branchDir := filepath.Join(dirPath, branch)
		entries, err := os.ReadDir(branchDir)
		if err != nil {
			panic(err)
		}
		for _, entry := range entries {
			fpath := filepath.Join(branchDir, entry.Name())
			ext := filepath.Ext(fpath)
			if ext != ".json" {
				continue
			}
			fmt.Println(fpath)
			fpath_nox := fpath[:len(fpath)-5]
			jsonB, err := os.ReadFile(fpath)
			if err != nil {
				panic(err)
			}
			doc := &openrpc_document.OpenrpcDocument{}
			err = json.Unmarshal(jsonB, doc)
			if err != nil {
				panic(err)
			}
			jsonB_2, err := json.Marshal(doc)
			if err != nil {
				panic(err)
			}
			jsonB_3 := pretty.PrettyOptions(jsonB_2, &pretty.Options{
				Width:    80,
				Prefix:   "",
				Indent:   "  ",
				SortKeys: false,
			})
			err = os.WriteFile(fpath_nox+".std.json", jsonB_3, 0o644)
			if err != nil {
				panic(err)
			}
		}
	}
}
