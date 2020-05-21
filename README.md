# IEPS-19-crawler
A web crawler implemented at the IEPS class.

## 1. ASSIGNMENT - INSTRUCTIONS

Download the crawler.py file and run it. The program will prompt you to insert the number of threads (workers) that it should use. After entering the number the program will run and terminate on its own.

## 2. ASSIGNMENT - INSTRUCTIONS

The assignment requires Python libraries to run:
- sys
- re
- json
- pylcs
- math
- lxml

To run the assignment execute file run-extraction.py in the implementation-extraction folder with arguments:
- A -> regular expressions
- B -> XPath
- C -> wrapper generation

The output is printed to standard output.

## 3. ASSIGNMENT - INSTRUCTIONS

The assignment requires Python libraries to run:
- nltk
- re
- sys
- time
- selectolax.parser (pip install selectolax)
- sqlite3

To run the assignment execute one of given programs:
- run-sqlite-search.py -> search with inverted index
- run-basic-search.py -> basic search with sequential file reading

The query is passed to the program as an argument.

The outout is printed to standard output.

To construct database first delete the curent one and then run program run-indexing.py.
