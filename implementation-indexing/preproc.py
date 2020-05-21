import nltk
import stopwords
import re

def preprocess(text):
    tokens = nltk.word_tokenize(text)

    indexed_tokens = list()
    for i in range(len(tokens)):
        word = tokens[i].lower()
        if word not in stopwords.stop_words_slovene:
            indexed_tokens.append((i, word))

    return indexed_tokens

def tokenize_text(text):
    return nltk.word_tokenize(text)

def index_words(words, text):
    data = dict()
    snippets = dict()
    for index, word in words:
        if re.fullmatch(r"[^\wčšž]+", word) == None:
            if word not in data:
                data[word] = (1, str(index))

                snippets[index] = get_snippet(text, index)
            else:
                num, i = data[word]
                num += 1
                i = i + "," + str(index)
                data[word] = (num, i)

                snippets[index] = get_snippet(text, index)

    return (data, snippets)

def get_snippet(text, index):
    snippet = ""

    count = 3
    i = 1
    left = " "
    while count > 0:
        if index >= i:
            if text[index - i] == '(' or text[index - i] == '[' or text[index - i] == '{' or text[index - i] == '/' or text[index - i] == '-' or text[index - i] == '_':
                if left.startswith(' '):
                    if (len(left) > 1):
                        left = text[index - i] + left[1:len(left)]
                    else:
                        left = text[index - i]
                else:
                    left = text[index - i] + left

                i += 1
                continue
            elif re.fullmatch(r"[^\wčšžČŽŠ]+", text[index - i]) != None:
                left = text[index - i] + left
                i += 1
                continue

            left = " " + text[index - i] + left
            i += 1
            count -= 1
        else:
            break

    snippet += left + text[index]

    count = 3
    i = 1
    right = ""
    while count > 0:
        if index + i < len(text):
            if text[index + i] == '(':
                right += " " + text[index + i]
                i += 1
                continue
            elif re.fullmatch(r"[^\wčšžČŽŠ]+", text[index + i]) != None:
                right += text[index + i]
                i += 1
                continue

            if right.endswith('(') or right.endswith('[') or right.endswith('{') or right.endswith('/') or right.endswith('-') or right.endswith('_'):
                right += text[index + i]
            else:
                right += " " + text[index + i]

            i += 1
            count -= 1
        else:
            break

    snippet += right + " ..."

    return snippet
