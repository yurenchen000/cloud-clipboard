package main

/**
*** FILE: config.go
***   handle config.json <===> Config
**/

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	// "github.com/sanity-io/litter"
)

type Config struct {
	Server struct {
		Host    string `json:"host"`    //done
		Port    int    `json:"port"`    //done
		Prefix  string `json:"prefix"`  //done
		History int    `json:"history"` //done
		// Auth    string `json:"auth"`
		Auth interface{} `json:"auth"` //done
	} `json:"server"`
	Text struct {
		Limit int `json:"limit"` //done
	} `json:"text"`
	File struct {
		Expire int `json:"expire"` //done
		Chunk  int `json:"chunk"`  //done, but no limit
		Limit  int `json:"limit"`  //done
	} `json:"file"`
}

var config_path = "config.json"

func load_config(config_path string) *Config {

	// Read the config.json file_content
	// file_content, err := ioutil.ReadFile("config.json")
	file_content, err := os.ReadFile(config_path)
	if err != nil {
		fmt.Printf("Error reading config file: %v\n", err)
		// os.Exit(1)
		file_content = []byte("{}")
	}

	// Parse the JSON data into the Config struct
	var config Config
	err = json.Unmarshal(file_content, &config)
	if err != nil {
		fmt.Printf("Error parsing config file: %v\n", err)
		os.Exit(1)
	}

	// Set default values
	if config.Server.Port == 0 {
		config.Server.Port = 9501
	}

	config.Server.Prefix = strings.TrimRight(config.Server.Prefix, "/")

	if config.Server.History == 0 {
		config.Server.History = 100
	}
	if config.Server.Auth != nil {
		switch auth := config.Server.Auth.(type) {
		case bool:
			fmt.Printf("Auth is a boolean: %v\n", auth)
		case string:
			fmt.Printf("Auth is a string: %s\n", auth)
		default:
			fmt.Printf("Auth is of an unexpected type: %T\n", auth)
		}
	} else {
		fmt.Println("Auth field is not provided in the config file")
		config.Server.Auth = false
	}

	if config.Server.Auth == false { // convert to ""
		config.Server.Auth = ""
	}

	if config.Text.Limit == 0 {
		config.Text.Limit = 4096
	}
	if config.File.Expire == 0 {
		config.File.Expire = 3600
	}
	if config.File.Chunk == 0 {
		config.File.Chunk = 2 * _MB
	}
	if config.File.Limit == 0 {
		config.File.Limit = 256 * _MB
	}

	// Print the parsed configuration
	fmt.Printf("\n---Parsed Config: %+v\n", config)
	// fmt.Println("\n---litter.dump:")
	// litter.Dump(config)

	return &config
}

func typeof(v interface{}) string {
	return fmt.Sprintf("%T", v)
}

/*

func typeof2(v interface{}) string {
	return reflect.TypeOf(v).String()
}

func main() {
	conf := load_config(config_path)

	fmt.Println("auth:", conf.Server.Auth, conf.Server.Auth == false)
	// fmt.Println("auth:", fmt.Sprintf("%T", conf.Server.Auth))
	fmt.Println("auth:", typeof(conf.Server.Auth))

}

//*/
