import json
import requests
import hashlib
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
import random

import cfg

# POST request to signin with credentials provided in cfg.py
def signin(usr, pwd):
    signin = requests.post("https://zyserver.zybooks.com/v1/signin", json={"email": usr, "password": pwd}).json()
    if not signin["success"]:
        raise Exception("Failed to sign in")
    return signin

# Return all books along with their metadata
def get_books(auth, usr_id):
    books = requests.get("https://zyserver.zybooks.com/v1/user/{}/items?items=%5B%22zybooks%22%5D&auth_token={}".format(usr_id, auth)).json()
    if not books["success"]:
        raise Exception("Failed to get books")
    books = books["items"]["zybooks"]
    for book in books:
        if book["autosubscribe"]:
            books.remove(book)
    return books

# Gets chapters along with their sections
def get_chapters(code, auth):
    chapters = requests.get("https://zyserver.zybooks.com/v1/zybooks?zybooks=%5B%22{}%22%5D&auth_token={}".format(code, auth)).json()
    return chapters["zybooks"][0]["chapters"]

# Returns all problems in a section
def get_problems(code, chapter, section, auth):
    problems = requests.get("https://zyserver.zybooks.com/v1/zybook/{}/chapter/{}/section/{}?auth_token={}".format(code, chapter, section, auth)).json()
    return problems["section"]["content_resources"]

# Gets current buildkey, used when generating md5 checksum
def get_buildkey():
    site = requests.get("https://learn.zybooks.com")
    soup = BeautifulSoup(site.text, "html.parser")
    buildkey = soup.find(attrs={"name":"zybooks-web/config/environment"})["content"]
    buildkey = json.loads(urllib.parse.unquote(buildkey))['APP']['BUILDKEY']
    return buildkey

# Get current timestamp in correct format
def gen_timestamp():
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M.{}Z").format(str(random.randint(0, 999)).rjust(3, "0"))
    return ts

# Generates md5 hash
def gen_chksum(act_id, ts, auth, part):
    md5 = hashlib.md5()
    md5.update("content_resource/{}/activity".format(act_id).encode("utf-8"))
    md5.update(ts.encode("utf-8"))
    md5.update(auth.encode("utf-8"))
    md5.update(str(act_id).encode("utf-8"))
    md5.update(str(part).encode("utf-8"))
    md5.update("true".encode("utf-8"))
    md5.update(get_buildkey().encode("utf-8"))
    return md5.hexdigest()

def solve(act_id, auth, part, code):
    url = "https://zyserver.zybooks.com/v1/content_resource/{}/activity".format(act_id)
    head = {
        "Host": "zyserver.zybooks.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Origin": "https://learn.zybooks.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://learn.zybooks.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }
    ts = gen_timestamp()
    chksm = gen_chksum(act_id, ts, auth, part)
    meta = {"isTrusted":True,"computerTime":ts}
    return requests.post(url, json={"part": part,"complete": True,"metadata":"{}","zybook_code":code,"auth_token":auth,"timestamp":ts,"__cs__":chksm}, headers=head).json()

def main():
    # Sign in to ZyBooks
    response = signin(cfg.USR, cfg.PWD)
    auth = response["session"]["auth_token"]
    usr_id = response["session"]["user_id"]

    # Get all books and have user select one
    books = get_books(auth, usr_id)
    i = 1
    for book in books:
        print(str(i) + ". " + book["title"])
        i += 1
    book = books[int(input("Select a Zybook: "))-1]

    # Get all chapters in selected book and have user select one
    code = book["zybook_code"]
    chapters = get_chapters(code, auth)
    for chapter in chapters:
        print(str(chapter["number"]) + ". " + chapter["title"])
    chapter = chapters[int(input("Select a chapter: "))-1]

    # Get all sections in selected chapter and have user select one
    sections = chapter["sections"]
    for section in sections:
        print(str(section["canonical_section_number"]) + ". " + section["title"])
    section = sections[int(input("Select a section: "))-1]

    # Solves all problems in given section
    problems = get_problems(code, chapter["number"], section["canonical_section_number"], auth)
    for problem in problems:
        act_id = problem["id"]
        parts = problem["parts"]
        if parts > 0:
            for part in range(parts):
                print(solve(act_id, auth, part, code))
        else:
            print(solve(act_id, auth, 0, code))

if __name__ == "__main__":
    main()