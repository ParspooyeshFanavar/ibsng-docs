package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Document struct {
	OpenRPC string   `json:"openrpc"`
	Info    Info     `json:"info"`
	Methods []Method `json:"methods"`
}

type Info struct {
	Version string `json:"version"`
	Title   string `json:"title"`
}

type Method struct {
	Name        string  `json:"name"`
	Description string  `json:"description"`
	Params      []Param `json:"params"`
}

type Param struct {
	Name        string       `json:"name"`
	Description string       `json:"description"`
	Value       *ParamValue  `json:"value,omitempty"`
	Schema      *ParamSchema `json:"schema,omitempty"`
}

type ParamSchema struct {
	Type string `json:"type"`
}

type ParamValue []string

func main() {
	fpath := os.Args[1]
	jsonB, err := os.ReadFile(fpath)
	if err != nil {
		panic(err)
	}
	doc := &Document{}
	err = json.Unmarshal(jsonB, doc)
	if err != nil {
		panic(err)
	}
	newJsonB, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		panic(err)
	}
	fmt.Println(string(newJsonB))
}
