package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
)

func main() {

	// Open file or create if non-existent for logging.
	file, err := os.OpenFile("tester.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal(err)
	}
	logger := log.New(file, "", log.LstdFlags)

	// Test characters from first list for first URL.
	url := "https://ionaapp.com/assignment-magic/dk/short/"
	logger.Println("First URL is: " + url)

	firstFile := "first.txt"
	firstList, err := ioutil.ReadFile(firstFile)

	if err != nil {
		logger.Printf("There is a problem opening the file.")
		fmt.Printf("There is a problem opening the file.")
	}
	lines := strings.Split(string(firstList), "\n")

	for index, element := range lines {
		resp, err := http.Get(url + lines[index])
		if err != nil {
			log.Fatalln(err)
			logger.Printf("There is a problem http get.", err)
		}
		// Read the response body on the line below.
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Fatalln(err)
			logger.Printf("There is a problem read response body.", err)
		}
		// Convert the body to type string
		sb := string(body)
		logger.Println("Index:", strconv.Itoa(index), "with data from list:", element, "gave the response:", sb)
	}

	// Test characters from second list for second URL
	url2 := "https://ionaapp.com/assignment-magic/dk/long/"
	logger.Println("First URL is: " + url2)

	secondFile := "second.txt"
	secondList, err := ioutil.ReadFile(secondFile)

	if err != nil {
		logger.Printf("There is a problem opening the file.")
		fmt.Printf("There is a problem opening the file.")
	}
	lines2 := strings.Split(string(secondList), "\n")

	for index, element := range lines2 {
		resp, err := http.Get(url2 + lines2[index])
		if err != nil {
			log.Fatalln(err)
			logger.Printf("There is a problem http get.", err)
		}
		// We Read the response body on the line below.
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Fatalln(err)
		}
		// Convert the body to type string
		sb := string(body)
		logger.Println("Index:", strconv.Itoa(index), "with data from list:", element, "gave the response:", sb)
	}

	defer file.Close()
}
