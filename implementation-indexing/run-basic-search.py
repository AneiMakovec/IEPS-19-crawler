import sys
import time
import re
from selectolax.parser import HTMLParser
from preproc import preprocess, tokenize_text, index_words  # importing custom package

def sort_by_freq(e):
    doc, freq, snippet = e
    return freq

if len(sys.argv) == 1:
    print("ERROR: no arguments.")
    exit(0)
elif len(sys.argv) > 2:
    print("ERROR: too much arguments.")
    exit(0)

q = sys.argv[1]

query = preprocess(q)
query = [word for i, word in query]

dir_names = ["e-prostor.gov.si", "e-uprava.gov.si", "evem.gov.si", "podatki.gov.si"]
dir_nums = [218, 60, 662, 564]

num_files = sum(dir_nums)
files_checked = 0

print("Executing query...")

start = time.time()

results = dict()
for dir in range(4):
    for num in range(1, dir_nums[dir] + 1):
        print("\rProgress: {:.2f}%".format(files_checked / num_files * 100), end='')

        file_name = dir_names[dir] + "/" + dir_names[dir] + "." + str(num) + ".html"

        try:
            f = open("../input-indexing/" + file_name, 'r')
        except IOError:
            continue

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
            if word in query:
                num, i = content[word]

                indices = [int(i) for i in i.split(',')]

                snippet = ""
                for i in indices:
                    if len(snippet) >= 250:
                        break

                    snippet += snippets[i]

                if file_name not in results:
                    results[file_name] = (num, "..." + snippet)
                else:
                    n, s = results[file_name]
                    n += num
                    if len(s) + len(snippet) <= 250:
                        s += snippet

                    results[file_name] = (n, s)

        files_checked += 1

merged_results = list()
for doc in results:
    freq, snippet = results[doc]
    merged_results.append((doc, freq, snippet))

merged_results.sort(reverse=True, key=sort_by_freq)

duration = time.time() - start

print("\rProgress: 100.00%")

print(f"Results for a query: \"{q}\"\n\n")
print("  Results found in {:.4f}s.\n\n".format(duration))
print("  Frequencies Document                                           Snippet")
print("  ----------- -------------------------------------------------- ----------------------------------------------------------------------------------------------------")

for doc, freq, snippet in merged_results:
    print("  {:<11d} {:<50s} {}".format(freq, doc, snippet))
