import os
import re
import time
import threading
import queue
import socket
import urlcanon
import concurrent.futures
import psycopg2
import tldextract
import requests
import requests.exceptions
import robotexclusionrulesparser
from datetime import datetime
from urllib.parse import urlsplit
from urllib.parse import urlparse
from urllib import parse
from urllib import robotparser
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

WEB_DRIVER_LOCATION = os.path.abspath("selenium_drivers" + os.path.sep + "chromedriver")
EXTRA_TIMEOUT = 10
TIMEOUT = 5
MINOR_TIMEOUT = 3
USER_AGENT = "fri-ieps-19"

# PAGE TYPE CODES
HTML = 'HTML'
BINARY = 'BINARY'
DUPLICATE = 'DUPLICATE'
FRONTIER = 'FRONTIER'
UNDEFINED = 'UNDEFINED'
PAGE_TIMEOUT = 'TIMEOUT'
NO_RESPONSE = 'NO_RESPONSE'
FRONTIER_HTML = 'FRONTIER_HTML'

# DATA TYPE CODES
PDF = 'PDF'
DOC = 'DOC'
DOCX = 'DOCX'
PPT = 'PPT'
PPTX = 'PPTX'
TXT = 'TXT'
UNKNOWN = 'UNKNOWN'
CSS = 'CSS'
CSV = 'CSV'
ZIP = 'ZIP'

# load selenium browser options
options = Options()
options.add_argument("--headless")

# set User-agent parameter
options.add_argument("user-agent=fri-ieps-19")

print("WebCrawler initialization complete.")

# let user input nuber of workers
workers_num = int(input("Please insert number of workers: "))

# initialize frontier
frontier = queue.Queue(0)
frontier.put("http://www.gov.si/")
frontier.put("http://evem.gov.si/")
frontier.put("http://e-uprava.gov.si/")
frontier.put("http://www.e-prostor.gov.si/")

conn = psycopg2.connect(host="localhost", user="postgres", password="postgres", database="crawler")
conn.autocommit = True

cursor = conn.cursor()
cursor.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s);", (None, FRONTIER, "http://www.gov.si/", None, None, None))
cursor.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s);", (None, FRONTIER, "http://evem.gov.si/", None, None, None))
cursor.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s);", (None, FRONTIER, "http://e-uprava.gov.si/", None, None, None))
cursor.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s);", (None, FRONTIER, "http://www.e-prostor.gov.si/", None, None, None))

# initialize duplicate lock
duplicatesLock = threading.Lock()

# initialize IP dictionary for each domain
domainIPDict = {}

# initialize dictionary to check when was the last request sent to an IP address
accessIPDict = {}
accessIPLock = threading.Lock()

# initialize robots.txt lock
robotLock = threading.Lock()

# initialize database lock
dataLock = threading.Lock()

# define worker class
class Worker(threading.Thread):
    def __init__(self, threadID, webDriver):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.webDriver = webDriver
        self.delay = TIMEOUT
        self.urlValidator = re.compile(r'^(?:http|ftp)s?://'
                                       r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                                       r'localhost|'
                                       r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                                       r'(?::\d+)?'
                                       r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        self.conn = self.connectDB()

    def run(self):
        while not frontier.empty():
            # get next url from frontier
            url = frontier.get()

            # parse url to get base url and domain name
            split_url = urlsplit(url)
            base = "{0.netloc}".format(split_url)

            domain = base.replace("www.", "") if "www." in base else base
            base_url = "{0.scheme}://{0.netloc}/".format(split_url)

            # first check if can access page
            canAccess = self.checkIPAccessTime(domain)
            if canAccess != None:
                if not canAccess:
                    # return url to frontier and move on to the next url
                    frontier.put(url)
                    continue
            else:
                continue

            # check if site already saved
            robotLock.acquire()
            site = self.findSiteByDomain(domain)
            if site:
                robotLock.release()
                siteID = site[0]
                robot_content = site[2]
            else:
                # retrieve robots.txt content
                try:
                    r = requests.get(parse.urljoin(base_url, 'robots.txt'))
                    robot_content = None

                    # if it exists, save it
                    if r.status_code == requests.codes.ok:
                        robot_content = r.text
                except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
                    robot_content = None

                # wait some time
                time.sleep(MINOR_TIMEOUT)

                # get sitemap.xml
                try:
                    s = requests.get(parse.urljoin(base_url, 'sitemap.xml'))
                    sitemap_content = None

                    # if it exists save it
                    if s.status_code == requests.codes.ok:
                        sitemap_content = s.text
                except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
                    sitemap_content = None

                # wait some time
                time.sleep(MINOR_TIMEOUT)

                # save site
                siteID = self.insertSite(domain, robot_content, sitemap_content)
                robotLock.release()

            # create robot file parser object
            robot = robotexclusionrulesparser.RobotExclusionRulesParser()
            if robot_content:
                robot.parse(robot_content)

            # check if current url is allowed by robots.txt
            duplicatesLock.acquire()
            if not robot.is_allowed(USER_AGENT, url):
                pageID = self.findPageByUrl(url)
                self.deleteLinkByID(pageID)
                self.deletePageByUrl(url)
                duplicatesLock.release()
                continue

            duplicatesLock.release()

            # download content from url
            try:
                self.webDriver.get(url)
                time.sleep(TIMEOUT)
            except TimeoutException:
                # save timeout
                if pageID:
                    # page already saved
                    self.updatePage(pageID, siteID, PAGE_TIMEOUT, None, req.response.status_code, datetime.now())
                else:
                    # save new page
                    pageID = self.insertPage(siteID, PAGE_TIMEOUT, url, None, req.response.status_code, datetime.now())

                # continue to next url in frontier
                del self.webDriver.requests
                print(f"Worker {self.threadID}: {url} done...")
                continue

            # retrieve request that loaded page
            req = None
            for request in self.webDriver.requests:
                if request.response and request.response.status_code >= 300 and request.response.status_code <= 399:
                    continue

                if request.response and request.path == url:
                    req = request
                    break

                if request.response and request.response.status_code == requests.codes.ok:
                    req = request
                    break

            if req == None:
                for request in self.webDriver.requests:
                    if request.response:
                        if request.response.status_code == 403 or request.response.status_code == 503:
                            req = request
                            break

                if not req:
                    req = self.webDriver.last_request

            # check page type and save page info
            pageID = self.findPageByUrl(url)
            if req and req.response:
                content_type = req.response.headers.get('Content-Type')
                if content_type:
                    if "text/html" in content_type:
                        # HTML page

                        # check for canonical link
                        try:
                            canonicalLink = self.webDriver.find_element_by_xpath("//link[@rel='canonical']")
                            if canonicalLink:
                                link = canonicalLink.get_attribute('href')

                                if link != url:
                                    # is duplicate
                                    duplicatesLock.acquire()

                                    # check if original page already saved
                                    originalPageID = self.findPageByUrl(link)
                                    if originalPageID:
                                        duplicatesLock.release()

                                        if pageID:
                                            # page already saved
                                            self.updatePage(pageID, None, DUPLICATE, None, None, datetime.now())
                                        else:
                                            # save new page and remember id
                                            pageID = self.insertPage(None, DUPLICATE, None, None, None, datetime.now())

                                        # add link to original page
                                        self.insertLink(pageID, originalPageID)

                                        # continue to next url in frontier
                                        del self.webDriver.requests
                                        print(f"Worker {self.threadID}: {url} done...")
                                        continue
                                    else:
                                        # create blank page
                                        originalPageID = self.insertPage(None, FRONTIER, link, None, None, None)
                                        duplicatesLock.release()

                                        if pageID:
                                            # page already saved
                                            self.updatePage(pageID, None, DUPLICATE, None, None, datetime.now())
                                        else:
                                            # save new page and remember id
                                            pageID = self.insertPage(None, DUPLICATE, None, None, None, datetime.now())

                                        # add link to original page
                                        self.insertLink(pageID, originalPageID)

                                        # add url to frontier
                                        frontier.put(link)

                                        # continue to next url in frontier
                                        del self.webDriver.requests
                                        print(f"Worker {self.threadID}: {url} done...")
                                        continue
                        except(NoSuchElementException, StaleElementReferenceException):
                            pass

                        # check for duplicate content
                        originalPageID = self.findPageByContent(self.webDriver.page_source)
                        if originalPageID:
                            # is duplicate
                            if pageID:
                                # page already saved
                                self.updatePage(pageID, None, DUPLICATE, None, None, datetime.now())
                            else:
                                # save new page and remember id
                                pageID = self.insertPage(None, DUPLICATE, None, None, None, datetime.now())

                            # add link to original page
                            self.insertLink(pageID, originalPageID)

                            # continue to next url in frontier
                            del self.webDriver.requests
                            print(f"Worker {self.threadID}: {url} done...")
                            continue

                        # not duplicate
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, FRONTIER_HTML, self.webDriver.page_source, req.response.status_code, datetime.now())
                        else:
                            # save new page and remember id
                            pageID = self.insertPage(siteID, FRONTIER_HTML, url, self.webDriver.page_source, req.response.status_code, datetime.now())

                        # let through only pages that loaded successfully
                        if req.response.status_code != requests.codes.ok:
                            del self.webDriver.requests
                            print(f"Worker {self.threadID}: {url} done...")
                            continue
                    elif "text/plain" in content_type:
                        # TXT content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, TXT)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "application/pdf" in content_type:
                        # PDF content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, PDF)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "application/msword" in content_type:
                        # DOC content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, DOC)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type:
                        # DOCX content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, DOCX)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "application/vnd.ms-powerpoint" in content_type:
                        # PPT content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, PPT)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "application/vnd.openxmlformats-officedocument.presentationml.presentation" in content_type:
                        # PPTX content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, PPTX)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "image" in content_type:
                        # IMAGE content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # parse file name
                        filename = urlparse(url)

                        # insert image data
                        self.insertImage(pageID, os.path.basename(filename.path), content_type, datetime.now())

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "text/css" in content_type:
                        # CSS content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, CSS)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "text/csv" in content_type:
                        # CSV content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, CSV)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    elif "application/zip" in content_type:
                        # ZIP content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, ZIP)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                    else:
                        # unknown BINARY content
                        if pageID:
                            # page already saved
                            self.updatePage(pageID, siteID, BINARY, None, req.response.status_code, datetime.now())
                        else:
                            # save new page
                            pageID = self.insertPage(siteID, BINARY, url, None, req.response.status_code, datetime.now())

                        # insert page data
                        self.insertPageData(pageID, UNKNOWN)

                        # continue to next url in frontier
                        del self.webDriver.requests
                        print(f"Worker {self.threadID}: {url} done...")
                        continue
                else:
                    # no content header -> mark page as UNDEFINED
                    if pageID:
                        # page already saved
                        self.updatePage(pageID, siteID, UNDEFINED, None, req.response.status_code, datetime.now())
                    else:
                        # save new page
                        pageID = self.insertPage(siteID, UNDEFINED, url, None, req.response.status_code, datetime.now())

                    # continue to next url in frontier
                    del self.webDriver.requests
                    print(f"Worker {self.threadID}: {url} done...")
                    continue
            else:
                # some kind of error happened
                if pageID:
                    # page already saved
                    self.updatePage(pageID, siteID, NO_RESPONSE, None, None, datetime.now())
                else:
                    # save new page
                    pageID = self.insertPage(siteID, NO_RESPONSE, url, None, None, datetime.now())

                # continue to next url in frontier
                del self.webDriver.requests
                print(f"Worker {self.threadID}: {url} done...")
                continue

            # only if page is of HTML type
            # extract links

            # href
            elements = self.webDriver.find_elements_by_xpath("//*[@href]")
            for element in elements:
                try:
                    link = element.get_attribute('href')

                    # check if url allowed by robots.txt and if is from .gov.si
                    if self.isGov(link) and robot.is_allowed(USER_AGENT, link):
                        # canonicalize url
                        link = str(urlcanon.whatwg(urlcanon.parse_url(link)))

                        # add url to frontier
                        self.addUrlToFrontier(pageID, link)
                except(NoSuchElementException, StaleElementReferenceException):
                    continue

            # onclick
            elements = self.webDriver.find_elements_by_xpath("//*[@onclick]")
            for element in elements:
                try:
                    line = element.get_attribute('onclick')
                    if line:
                        link = ""
                        if "location.href='" in line:
                            rightLine = line.split("location.href='")[1]
                            link = rightLine.split("'")[0]
                        elif "document.location='" in line:
                            rightLine = line.split("document.location='")[1]
                            link = rightLine.split("'")[0]

                        if link != "":
                            # check if url allowed by robots.txt and if is from .gov.si
                            if self.isGov(link) and robot.is_allowed(USER_AGENT, link):
                                # canonicalize url
                                link = str(urlcanon.whatwg(urlcanon.parse_url(link)))

                                # add url to frontier
                                self.addUrlToFrontier(pageID, link)
                except(NoSuchElementException, StaleElementReferenceException):
                    continue

            # extract images
            elements = self.webDriver.find_elements_by_tag_name('img')
            for element in elements:
                try:
                    link = element.get_attribute('src')

                    # check if url allowed by robots.txt, if is from .gov.si and if src attribute has URL
                    if self.isGov(link) and robot.is_allowed(USER_AGENT, link) and re.match(self.urlValidator, link):
                        link = str(urlcanon.whatwg(urlcanon.parse_url(link)))

                        self.addUrlToFrontier(pageID, link)
                except(NoSuchElementException, StaleElementReferenceException):
                    continue

            del self.webDriver.requests
            print(f"Worker {self.threadID}: {url} done...")

        self.conn.close()
        self.webDriver.quit()
        print(f"Worker {self.threadID}: finished crawling.")

    def isGov(self, url):
        split_url = urlsplit(url)
        base = "{0.netloc}".format(split_url)

        if ".gov.si" in base or "gov.si" in base:
            return True
        else:
            return False

    def checkIPAccessTime(self, url):
        # check if already visited this server
        accessIPLock.acquire()
        ip = domainIPDict.get(url)
        if ip == None:
            # if not, save the server's IP, then add an access timestamp
            try:
                ip = socket.gethostbyname(url)
            except:
                accessIPLock.release()
                return None

            domainIPDict[url] = ip
            accessIPDict[ip] = time.time()
            accessIPLock.release()
            return True
        else:
            # if IP already visited, check if it was visited within a delay
            t = time.time() - accessIPDict[ip]
            if t < self.delay:
                accessIPLock.release()
                return False
            else:
                accessIPDict[ip] = time.time()
                accessIPLock.release()
                return True

    def addUrlToFrontier(self, parentID, url):
        duplicatesLock.acquire()
        originalPageID = self.findPageByUrl(url)
        if originalPageID:
            # is duplicate
            duplicatesLock.release()

            # create new duplicate page
            pageID = self.insertPage(None, DUPLICATE, None, None, None, datetime.now())

            # create link from duplicate to original
            self.insertLink(pageID, originalPageID)

            # create link from parent to new page
            self.insertLink(parentID, pageID)
        else:
            # is new

            # create new blank page
            pageID = self.insertPage(None, FRONTIER, url, None, None, None)
            duplicatesLock.release()

            # create link from parent to new page
            self.insertLink(parentID, pageID)

            # add url to frontier
            frontier.put(url)

    def insertSite(self, site, robot_content, sitemap_content):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO crawldb.site (domain, robots_content, sitemap_content) VALUES (%s, %s, %s) RETURNING id;", (site, robot_content, sitemap_content))
            id = cursor.fetchone()[0]
        return id

    def insertPage(self, siteID, page_type, url, html_content, http_status_code, accessed_time):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;", (siteID, page_type, url, html_content, http_status_code, accessed_time))
            id = cursor.fetchone()[0]
        return id

    def insertLink(self, page1ID, page2ID):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO crawldb.link (from_page, to_page) VALUES (%s, %s);", (page1ID, page2ID))

    def insertPageData(self, pageID, data_type_code):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO crawldb.page_data (page_id, data_type_code, data) VALUES (%s, %s, %s);", (pageID, data_type_code, None))

    def insertImage(self, pageID, filename, content_type, accessed_time):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO crawldb.image (page_id, filename, content_type, data, accessed_time) VALUES (%s, %s, %s, %s, %s);", (pageID, filename, content_type, None, accessed_time))

    def updatePage(self, pageID, siteID, page_type, html_content, http_status_code, accessed_time):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE crawldb.page SET site_id = %s, page_type_code = %s, html_content = %s, http_status_code = %s, accessed_time = %s WHERE id = %s;", (siteID, page_type, html_content, http_status_code, accessed_time, pageID))

    def findPageByContent(self, content):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM crawldb.page WHERE html_content = %s;", (content,))

            try:
                page = cursor.fetchone()
                if page:
                    page = page[0]
            except psycopg2.ProgrammingError:
                page = None
        return page

    def findSiteByDomain(self, domain):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM crawldb.site WHERE domain = %s;", (domain,))

            try:
                site = cursor.fetchone()
            except psycopg2.ProgrammingError:
                site = None
        return site

    def findPageByUrl(self, url):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM crawldb.page WHERE url = %s", (url,))

            try:
                page = cursor.fetchone()
                if page:
                    page = page[0]
            except psycopg2.ProgrammingError:
                page = None
        return page

    def deletePageByUrl(self, url):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM crawldb.page WHERE url = %s", (url,))

    def deleteLinkByID(self, id):
        with dataLock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM crawldb.link WHERE from_page = %s OR to_page = %s;", (id, id))

    def connectDB(self):
        conn = psycopg2.connect(host="localhost", user="postgres", password="postgres", database="crawler")
        conn.autocommit = True
        return conn



print("Started crawling...")
workers = []
for i in range(workers_num):
    workers.append(Worker(i + 1, webdriver.Chrome(WEB_DRIVER_LOCATION, options=options)))
    workers[i].start()
