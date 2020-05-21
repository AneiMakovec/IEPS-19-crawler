import sqlite3
import re
from selectolax.parser import HTMLParser
from preproc import preprocess, tokenize_text, index_words  # importing custom package

print("Connecting to database...")

conn = sqlite3.connect('inverted-index.db')

cur = conn.cursor()

cur.execute('''
    CREATE TABLE IndexWord (
        word TEXT PRIMARY KEY
    );
''')

cur.execute('''
    CREATE TABLE Posting (
        word TEXT NOT NULL,
        documentName TEXT NOT NULL,
        frequency INTEGER NOT NULL,
        indexes TEXT NOT NULL,
        PRIMARY KEY(word, documentName),
        FOREIGN KEY (word) REFERENCES IndexWord(word)
    );
''')

cur.execute('''
    CREATE TABLE Snippets (
        documentName TEXT NOT NULL,
        sindex INTEGER NOT NULL,
        snippet TEXT NOT NULL,
        PRIMARY KEY(documentName, sindex)
    );
''')

conn.commit()

dir_names = ["e-prostor.gov.si", "e-uprava.gov.si", "evem.gov.si", "podatki.gov.si"]
dir_nums = [218, 60, 662, 564]

print("Started processing and indexing...")

for dir in range(4):
    for num in range(1, dir_nums[dir] + 1):
        file_name = dir_names[dir] + "/" + dir_names[dir] + "." + str(num) + ".html"

        try:
            f = open("../input-indexing/" + file_name, 'r')
        except IOError:
            continue

        print(f"Processing file {file_name}...")

        content = f.read()

        html = HTMLParser(content)
        if html.body is None:
            continue

        for tag in html.css('script'):
            tag.decompose()
        for tag in html.css('style'):
            tag.decompose()

        content = html.body.text(separator='\n')

        text = tokenize_text(content)
        content = preprocess(content)

        content, snippets = index_words(content, text)
        for word in content:
            num, i = content[word]

            cur.execute('INSERT OR IGNORE INTO IndexWord (word) VALUES (?);', (word,))

            post = (word, file_name, num, i)
            cur.execute('INSERT INTO Posting VALUES (?,?,?,?);', post)

        conn.commit()

        for index in snippets:
            snippet = snippets[index]

            s = (file_name, index, snippet)
            cur.execute('INSERT INTO Snippets VALUES (?,?,?);', s)

        conn.commit()

conn.close()

print("Finished processing.")
