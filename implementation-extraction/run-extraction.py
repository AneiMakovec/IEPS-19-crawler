import sys
import re
import json
import pylcs
import math
from lxml import html


###########################################################
############ REGULAR EXPRESSION IMPLEMENTATION ############
###########################################################

def do_reg_ex():
    print("STARTING REGULAR EXPRESSION IMPLEMENTATION")

    print("Started extracting overstock.com...")

    # extract first page from overstock.com
    content = open('../input-extraction/overstock.com/jewelry01.html', encoding='utf8', errors='ignore').read()
    do_reg_ex_overstock(content, "jewelry01.html")

    # extract second page from overstock.com
    content = open('../input-extraction/overstock.com/jewelry02.html', encoding='utf8', errors='ignore').read()
    do_reg_ex_overstock(content, "jewelry02.html")

    print("Started extracting rtvslo.si...")

    # extract first page from rtvslo.si
    content = open('../input-extraction/rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html', encoding='utf8', errors='ignore').read()
    do_reg_ex_rtvslo(content, "Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html")

    # extract second page from rtvslo.si
    content = open('../input-extraction/rtvslo.si/Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html', encoding='utf8', errors='ignore').read()
    do_reg_ex_rtvslo(content, "Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html")

    print("Started extracting bookdepository.com...")

    # extract first page from bookdepository.com
    content = open('../input-extraction/bookdepository.com/Book_Depository_1.html', encoding='utf8', errors='ignore').read()
    do_reg_ex_books(content, "Book_Depository_1.html")

    # extract second page from bookdepository.com
    content = open('../input-extraction/bookdepository.com/Book_Depository_2.html', encoding='utf8', errors='ignore').read()
    do_reg_ex_books(content, "Book_Depository_2.html")

def do_reg_ex_overstock(content, page):
    # extract titles
    pattern = re.compile("<a\\s*href=\"\\S*\"><b>([^V][\\w\-\'.,\\s()]*)<\\Wb><\\Wa>")
    titles = pattern.findall(content)

    # extract list prices
    pattern = re.compile("List Price:<\\/b><\\/td><td align=\"\\D*\" nowrap=\"\\D*\"><s>(\\$\\d*,?\\d*.\\d*)")
    listPrices = pattern.findall(content)

    # extract prices
    pattern = re.compile("Price:<\\/b><\\/td><td align=\"\\D*\" nowrap=\"\\D*\"><span class=\"bigred\"><b>(\\$\\d*,?\\d*.?\\d*)")
    prices = pattern.findall(content)

    # extract savings and saving percentages
    pattern = re.compile("You Save:<\\/b><\\/td><td align=\"\\D*\" nowrap=\"\\D*\"><span class=\"littleorange\">(\\$\\d*,?\\d*.?\\d* \\(\\d*\\%\\))")
    savingsMatch = pattern.findall(content)
    savings = list()
    percentages = list()
    for match in savingsMatch:
        s = match.split(' ')

        savings.append(s[0])
        percentages.append(s[1].replace('(', '').replace(')', ''))

    # extract contents
    pattern = re.compile("<td valign=\"top\"><span class=\"normal\">([\\s\\S]*?)\\s*<br><a href=\"[\\S]*\"><span class=\"tiny\"><b>Click here to purchase[.]<\\/b><\\/span><\\/a><\\/span><br>")
    contents = pattern.findall(content)

    # print data records in JSON format
    print("PAGE {}:".format(page))

    for i in range(len(titles)):
        dataRecord = {
            "title": titles[i],
            "list_price": listPrices[i],
            "price": prices[i],
            "saving": savings[i],
            "saving_percent": percentages[i],
            "content": contents[i].replace('\n', " ")
        }
        print(json.dumps(dataRecord, indent = 4))

def do_reg_ex_rtvslo(content, page):
    # extract title
    pattern = re.compile("<h1>([\\s\\S]*)<\\/h1>")
    title = pattern.search(content).group(1)

    # extract subtitle
    pattern = re.compile("<div class=\"subtitle\">([\\s\\D]*)<\\/div>")
    subtitle = pattern.search(content).group(1)

    # extract author and published time
    pattern = re.compile("<div class=\"author-timestamp\">\\s*<strong>([\\s\\D]*)<\\/strong>\\|\\s*(\\d*\\.\\D*\\d*\\D*\\d*\\:\\d*)\\s*<\\/div>")
    match = pattern.search(content)
    author = match.group(1)
    publishedTime = match.group(2)

    # extract lead
    pattern = re.compile("<p class=\"lead\">([a-zA-Z0-9žščŽŠČ.,\\s]*)<\\/p>")
    lead = pattern.search(content).group(1)

    # extract content
    pattern = re.compile("<p(?: class=\"Body\")?>(?:<strong>)?((?!Test|Preizkus|Ogrožena|Obuditev|Ekipa|Razvoj)[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)(?:<br>)?(?:<\\/strong>)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*(?:<sub>)?\\d?(?:<\\/sub>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?((?:<br>)?[\\sa-zA-Z0-9žščŽŠČ\",.:–\\/=-]*)?")
    c = ""
    for match in pattern.finditer(content):
        for group in match.groups():
            if group != "":
                c += group.replace("<br>", "").replace("<sub>", "").replace("</sub>", "")
                c += " "

    # print data record in JSON format
    print("PAGE {}:".format(page))

    dataRecord = {
        "author": author,
        "published_time": publishedTime,
        "title": title,
        "subtitle": subtitle,
        "lead": lead,
        "content": c
    }
    print(json.dumps(dataRecord, ensure_ascii=False, indent = 4).encode('utf8').decode())

def do_reg_ex_books(content, page):
    # extract titles
    pattern = re.compile("<h3 class=\"title\">\\s*<a href=\"[\\S]*\">\\s*([\\sa-zA-Z0-9,.&\\/;:()+*#?!'-]*)<br>\\s*<\\/a>\\s*<\\/h3>")
    titles = pattern.findall(content)

    # extract authors
    pattern = re.compile("<p class=\"author\">\\s*<a href=\"[\\S]*\" itemprop=\"author\">([\\sa-zA-Z'.,-]*)<\\/a>\\s*<\\/p>")
    authors = pattern.findall(content)

    # extract published dates
    pattern = re.compile("<p class=\"published\" itemprop=\"datePublished\">([ \\da-zA-Z]*)<\\/p>")
    publishedDates = pattern.findall(content)

    # extract formats
    pattern = re.compile("<p class=\"format\">([a-zA-Z]*)<\\/p>")
    formats = pattern.findall(content)

    # extract original prices
    pattern = re.compile("<span class=\"rrp\">([ \\d,€]*)<\\/span>")
    originalPrices = pattern.findall(content)

    # extract prices
    pattern = re.compile("<p class=\"price\">\\s*([ \\d,€]*)\\s*.*\\s*<\\/p>")
    prices = pattern.findall(content)

    # extract savings
    pattern = re.compile("<p class=\"price-save\">\\s*Save ([ \\d,€]*)<\\/p>")
    savings = pattern.findall(content)

    # print data records in JSON format
    print("PAGE {}:".format(page))

    for i in range(len(titles)):
        dataRecord = {
            "title": titles[i],
            "author": authors[i],
            "published_date": publishedDates[i],
            "format": formats[i],
            "original_price": originalPrices[i],
            "price": prices[i],
            "saving": savings[i]
        }
        print(json.dumps(dataRecord, ensure_ascii=False, indent = 4).encode('utf8').decode())







###########################################################
################## XPATH IMPLEMENTATION ###################
###########################################################

def do_xpath():
    print("STARTING XPATH IMPLEMENTATION")

    print("Started extracting overstock.com...")

    # extract first page from overstock.com
    content = open('../input-extraction/overstock.com/jewelry01.html', encoding='utf8', errors='ignore').read()
    do_xpath_overstock(content, "jewelry01.html")

    # extract second page from overstock.com
    content = open('../input-extraction/overstock.com/jewelry02.html', encoding='utf8', errors='ignore').read()
    do_xpath_overstock(content, "jewelry02.html")

    print("Started extracting rtvslo.si...")

    # extract first page from rtvslo.si
    content = open('../input-extraction/rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html', encoding='utf8', errors='ignore').read()
    do_xpath_rtvslo(content, "Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html")

    # extract second page from rtvslo.si
    content = open('../input-extraction/rtvslo.si/Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html', encoding='utf8', errors='ignore').read()
    do_xpath_rtvslo(content, "Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html")

    print("Started extracting bookdepository.com...")

    # extract first page from bookdepository.com
    content = open('../input-extraction/bookdepository.com/Book_Depository_1.html', encoding='utf8', errors='ignore').read()
    do_xpath_books(content, "Book_Depository_1.html")

    # extract second page from bookdepository.com
    content = open('../input-extraction/bookdepository.com/Book_Depository_2.html', encoding='utf8', errors='ignore').read()
    do_xpath_books(content, "Book_Depository_2.html")

def do_xpath_overstock(content, page):
    # form an XML tree from HTML content
    tree = html.fromstring(content)

    # extract titles
    titles = tree.xpath('//td[@valign="top"]/a/b/text()')

    # extract list prices
    listPrices = tree.xpath('//tr[td[1]/b[text()="List Price:"]]/td[2]/s/text()')

    # extract prices
    prices = tree.xpath('//tr[td[1]/b[text()="Price:"]]/td[2]/span/b/text()')

    # extract savings and saving percentages
    savings = tree.xpath('//tr[td[1]/b[text()="You Save:"]]/td[2]/span/text()')

    # extract contents
    contents = tree.xpath('//td[@valign="top"]/span[@class="normal"]/text()')

    # print data records in JSON format
    print("PAGE {}:".format(page))

    for i in range(len(titles)):
        saving, percentage = savings[i].split(" ")
        dataRecord = {
            "title": titles[i],
            "list_price": listPrices[i],
            "price": prices[i],
            "saving": saving,
            "saving_percent": percentage.replace("(", "").replace(")", ""),
            "content": contents[i].replace('\n', " ")
        }
        print(json.dumps(dataRecord, indent = 4))

def do_xpath_rtvslo(content, page):
    # form an XML tree from HTML content
    tree = html.fromstring(content)

    # extract title
    title = str(tree.xpath('//h1/text()')[0])

    # extract subtitle
    subtitle = str(tree.xpath('//div[@class="subtitle"]/text()')[0])

    # extract author
    author = str(tree.xpath('//div[@class="author-timestamp"]/strong/text()')[0])

    # extract published time
    publishedTime = str(tree.xpath('//div[@class="author-timestamp"]/text()')[1]).replace("|", "").replace("\n", "").strip()

    # extract lead
    lead = str(tree.xpath('//p[@class="lead"]/text()')[0])

    # extract content
    contents = tree.xpath('//p[@class="Body"]/text() | //p/strong/text() | //p[contains(text(), "-") or contains(text(), ":") or contains(text(), ",") and not(@class)]/text() | //p/sub/text()')
    content = ""
    for c in contents:
        content += c
        content += " "

    # print data record in JSON format
    print("PAGE {}:".format(page))

    dataRecord = {
        "author": author,
        "published_time": publishedTime,
        "title": title,
        "subtitle": subtitle,
        "lead": lead,
        "content": content
    }
    print(json.dumps(dataRecord, ensure_ascii=False, indent = 4).encode('utf8').decode())

def do_xpath_books(content, page):
    # form an XML tree from HTML content
    tree = html.fromstring(content)

    # extract titles
    titles = tree.xpath('//h3[@class="title"]/a/text()')
    newTitles = list()
    for title in titles:
        title = title.strip("\n ")
        if (title != ""):
            newTitles.append(title)
    titles = newTitles

    # extract authors
    authors = tree.xpath('//p[@class="author"]/a/text()')

    # extract published dates
    publishedDates = tree.xpath('//p[@class="published"]/text()')

    # extract formats
    formats = tree.xpath('//p[@class="format"]/text()')

    # extract original prices
    originalPrices = tree.xpath('//span[@class="rrp"]/text()')

    # extract prices
    prices = tree.xpath('//p[@class="price"]/text()')
    newPrices = list()
    for price in prices:
        price = price.strip("\n ")
        if (price != ""):
            price = price.split("\n")[0]
            newPrices.append(price)
    prices = newPrices

    # extract savings
    savings = tree.xpath('//p[@class="price-save"]/text()')
    newSavings = list()
    for saving in savings:
        saving = saving.strip("\n ")
        saving = saving.split("e ")[1]
        newSavings.append(saving)
    savings = newSavings

    # print data records in JSON format
    print("PAGE {}:".format(page))

    for i in range(len(titles)):
        dataRecord = {
            "title": titles[i],
            "author": authors[i],
            "published_date": publishedDates[i],
            "format": formats[i],
            "original_price": originalPrices[i],
            "price": prices[i],
            "saving": savings[i]
        }
        print(json.dumps(dataRecord, ensure_ascii=False, indent = 4).encode('utf8').decode())







###########################################################
######## AUTOMATIC WEB EXTRACTION IMPLEMENTATION ##########
###########################################################

def do_auto_web():
    print("STARTING AUTOMATIC WEB EXTRACTION ALGORITHM IMPLEMENTATION")

    print("Started wrapping overstock.com...")
    content1 = open('../input-extraction/overstock.com/jewelry01.html', encoding='utf8', errors='ignore').read()
    content2 = open('../input-extraction/overstock.com/jewelry02.html', encoding='utf8', errors='ignore').read()
    do_webstemmer(content1, content2, "overstock.com/jewelry01.html", "overstock.com/jewelry02.html")

    print("Started wrapping rtvslo.si...")
    content1 = open('../input-extraction/rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html', encoding='utf8', errors='ignore').read()
    content2 = open('../input-extraction/rtvslo.si/Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html', encoding='utf8', errors='ignore').read()
    do_webstemmer(content1, content2, "rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html", "rtvslo.si/Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html")

    print("Started wrapping bookdepository.com...")
    content1 = open('../input-extraction/bookdepository.com/Book_Depository_1.html', encoding='utf8', errors='ignore').read()
    content2 = open('../input-extraction/bookdepository.com/Book_Depository_2.html', encoding='utf8', errors='ignore').read()
    do_webstemmer(content1, content2, "bookdepository.com/Book_Depository_1.html", "bookdepository.com/Book_Depository_2.html")

def do_webstemmer(content1, content2, page1, page2):
    # form an XML tree from HTML content
    tree1 = html.fromstring(content1)
    tree2 = html.fromstring(content2)

    # define HTML tags to parse
    tags = ("title", "h1", "h2", "h3", "h4", "h5", "h6", "div", "td", "tr", "table", "tbody", "b", "a", "p", "strong", "i", "em", "small", "u", "strike", "li", "marquee", "center", "th")

    # parse the pages
    layoutBlocks1 = list()
    parse_page(tree1, layoutBlocks1, tags)

    layoutBlocks2 = list()
    parse_page(tree2, layoutBlocks2, tags)

    # generate layout pattern
    layoutBlocks1, layoutBlocks2 = generate_layout_pattern(layoutBlocks1, layoutBlocks2)

    # calculate diffscore
    diffScores = calc_diffscore(layoutBlocks1, layoutBlocks2)

    # calculate mainscore
    mainScores = calc_mainscore(layoutBlocks1, layoutBlocks2, diffScores)

    # calculate layout pattern score
    layoutPatternScore = math.log(len(mainScores)) * sum(mainScores)

    # print wrapper
    print("# {} {} (pattern 1)".format(layoutPatternScore, page1))
    print("#       (Pages which belong to this cluster)")
    print("#       {}".format(page1))
    print("#       {}".format(page2))
    print("({},                             (Overall score of the cluster)".format(layoutPatternScore))
    print(" {}, (Cluster ID)".format(repr(page1)))
    print(" [                                                       (List of layout blocks)")
    print("  # (diffscore, mainscore, block feature)")

    for i in range(len(layoutBlocks1)):
        line = "  ({}, {}, {})".format(diffScores[i], mainScores[i], get_path(layoutBlocks1[i], ""))
        if i < len(layoutBlocks1) - 1:
            line += ","

        print(line)

    print(" ]")
    print(")")

def parse_page(page, list, tags):
    for e in page:
        if str(e.tag) in tags:
            list.append(e)

        parse_page(e, list, tags)

        if (len(e) > 0) and str(e.tag) in tags:
            list.append(e)

def generate_layout_pattern(blocks1, blocks2):
    if len(blocks1) < len(blocks2):
        size = len(blocks1)
    else:
        size = len(blocks2)

    pattern1 = list()
    pattern2 = list()
    for i in range(size):
        if blocks1[i].tag == blocks2[i].tag:
            pattern1.append(blocks1[i])
            pattern2.append(blocks2[i])

    return (pattern1, pattern2)

def calc_diffscore(blocks1, blocks2):
    scores = list()
    for i in range(len(blocks1)):
        s1 = blocks1[i].text
        s2 = blocks2[i].text

        if not s1:
            s1 = ""
            w1 = 0
        else:
            s1 = str(s1).strip("\t\n ")
            w1 = len(s1)

        if not s2:
            s2 = ""
            w2 = 0
        else:
            s2 = str(s2).strip("\t\n ")
            w2 = len(s2)

        if w1 == 0 and w2 == 0:
            scores.append(0.0)
        else:
            score = (w1 + w2 - 2 * pylcs.lcs(s1, s2)) / (w1 + w2)
            scores.append(score)

    return scores

def calc_mainscore(blocks1, blocks2, diffscore):
    scores = list()
    for i in range(len(blocks1)):
        s1 = blocks1[i].text
        s2 = blocks2[i].text

        if not s1:
            s1 = ""
            w1 = 0
        else:
            s1 = str(s1).strip("\t\n ")
            w1 = len(s1)

        if not s2:
            s2 = ""
            w2 = 0
        else:
            s2 = str(s2).strip("\t\n ")
            w2 = len(s2)

        score = diffscore[i] * (w1 + w2) / len(str(blocks1[i].tag))
        scores.append(score)

    return scores

def get_path(element, path):
    if element != None and str(element.tag) != "html" and str(element.tag) != "body" and str(element.tag) != "head":
        new_path = str(element.tag)

        for attrib in element.attrib:
            new_path += ":{}={}".format(attrib, element.attrib[attrib])

        if path != "":
            new_path += "/"

        new_path += path
        return get_path(element.getparent(), new_path)
    else:
        if path == "":
            path += str(element.tag)

        return path






if len(sys.argv) != 2:
    print("ERROR: invalid argument.")
    exit(0)

if sys.argv[1] == 'A':
    do_reg_ex()
elif sys.argv[1] == 'B':
    do_xpath()
elif sys.argv[1] == 'C':
    do_auto_web()
else:
    print("ERROR: invalid argument.")
    exit(0)
