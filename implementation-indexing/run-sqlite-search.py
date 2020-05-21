import sys
import time
import sqlite3
import re
from selectolax.parser import HTMLParser
from preproc import preprocess, tokenize_text  # importing custom package

if len(sys.argv) == 1:
    print("ERROR: no arguments.")
    exit(0)
elif len(sys.argv) > 2:
    print("ERROR: too much arguments.")
    exit(0)

q = sys.argv[1]

query = preprocess(q)
query = [word for i, word in query]

print("Connecting to database...")

conn = sqlite3.connect('inverted-index.db')

cur = conn.cursor()

s = '''
    SELECT p.documentName AS docName, SUM(frequency) AS freq, GROUP_CONCAT(indexes) AS idxs
    FROM Posting p
    WHERE
        p.word IN ({l})
    GROUP BY p.documentName
    ORDER BY freq DESC;
'''.format(l=','.join(['?'] * len(query)))

print("Executing query...")

start = time.time()
results = cur.execute(s, query).fetchall()

snippets = list()
for doc, freq, i in results:
    indices = [int(n) for n in i.split(",")]
    indices.sort()

    s = '''
        SELECT s.snippet
        FROM Snippets s
        WHERE
            s.documentName = (?) AND s.sindex IN ({l});
    '''.format(l=','.join(['?'] * len(indices)))

    indices = [doc] + indices

    snippet = "..."
    for snip in cur.execute(s, indices):
        if len(snippet) >= 250:
            break

        snippet += snip[0]

    snippets.append(snippet)

duration = time.time() - start;

print(f"Results for a query: \"{q}\"\n\n")
print("  Results found in {:.4f}s.\n\n".format(duration))
print("  Frequencies Document                                           Snippet")
print("  ----------- -------------------------------------------------- ----------------------------------------------------------------------------------------------------")

for i in range(len(results)):
    doc, freq, index = results[i]
    snippet = snippets[i]
    print("  {:<11d} {:<50s} {}".format(freq, doc, snippet))
