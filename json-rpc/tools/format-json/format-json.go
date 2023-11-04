package main

import (
	"os"

	"github.com/tidwall/pretty"
)

func main() {
	for _, fpath := range os.Args[1:] {
		jsonB, err := os.ReadFile(fpath)
		if err != nil {
			panic(err)
		}
		newJsonB := pretty.PrettyOptions(jsonB, &pretty.Options{
			Width:    80,
			Prefix:   "",
			Indent:   "  ",
			SortKeys: false,
		})
		err = os.WriteFile(fpath, newJsonB, 0o644)
		if err != nil {
			panic(err)
		}
	}
}
