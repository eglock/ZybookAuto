import sys
import json
import requests
import hashlib
import urllib.parse
import random
from datetime import datetime
from html.parser import HTMLParser

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

# Spoofs "time_spent" anywhere from 1 to 60 seconds.
def spend_time(auth, sec_id, act_id, part, code):
    global t_spfd
    t  = random.randint(1, 60)
    t_spfd += t
    return requests.post("https://zyserver2.zybooks.com/v1/zybook/{}/time_spent".format(code), json={"time_spent_records":[{"canonical_section_id":sec_id,"content_resource_id":act_id,"part":part,"time_spent":t,"timestamp":gen_timestamp()}],"auth_token":auth}).json()["success"]

# Gets current buildkey, used when generating md5 checksum
def get_buildkey():
    class Parser(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "meta" and attrs[0][1] == "zybooks-web/config/environment":
                self.data = json.loads(urllib.parse.unquote(attrs[1][1]))['APP']['BUILDKEY']
    p = Parser()
    p.feed(requests.get("https://learn.zybooks.com").text)
    return p.data

# Get current timestamp in correct format, with respect to time spent
def gen_timestamp():
    global t_spfd
    ct = datetime.now()
    d = 0
    h = ct.hour
    m = ct.minute + (t_spfd // 60)
    if m > 59:
        h += m // 60
        m %= 60
    if h > 23:
        d += h // 24
        h %= 24
    nt = ct.replace(day=ct.day+d, hour=h, minute=m)
    ts = nt.strftime("%Y-%m-%dT%H:%M.{}Z").format(str(random.randint(0, 999)).rjust(3, "0"))
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

def solve(act_id, sec_id, auth, part, code):
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
    spend_time(auth, sec_id, act_id, part, code)
    ts = gen_timestamp()
    chksm = gen_chksum(act_id, ts, auth, part)
    meta = {"isTrusted":True,"computerTime":ts}
    return requests.post(url, json={"part": part,"complete": True,"metadata":"{}","zybook_code":code,"auth_token":auth,"timestamp":ts,"__cs__":chksm}, headers=head).json()

def main():
    global t_spfd
    # Sign in to ZyBooks
    response = signin(cfg.USR, cfg.PWD)
    auth = response["session"]["auth_token"]
    usr_id = response["session"]["user_id"]
    t_spfd = 0 # Keeps track of total "time_spent" sent to server
    for attempt in range(3): # Try to reauthenticate three times before giving up
        while True:
            try:
                # Get all books and have user select one
                books = get_books(auth, usr_id)
                i = 1
                for book in books:
                    print(str(i) + ". " + book["title"])
                    i += 1
                print(str(i) + ". " + "[BATCH]")
                print(str(i+1) + ". " + "[EXIT]")
                while True:
                    selection = input("Select a Zybook: ")
                    try:
                        selection = int(selection)
                    except:
                        print("Please enter a number")
                        continue
                    if selection == i:
                        sys.exit(0) # Batch processing will go here
                    elif selection == i + 1:
                        sys.exit(0)
                    elif selection > i + 1 or selection < 1:
                        print("Invalid selection")
                        continue
                    else:
                        break
                book = books[int(selection)-1]
                # Get all chapters in selected book and have user select one
                code = book["zybook_code"]
                chapters = get_chapters(code, auth)
                for chapter in chapters:
                    print(str(chapter["number"]) + ". " + chapter["title"])
                print(str(chapters[-1]["number"]+1) + ". " + "[EXIT]")
                while True:
                    selection = input("Select a chapter: ")
                    try:
                        selection = int(selection)
                    except:
                        print("Please enter a number")
                        continue
                    if selection > chapters[-1]["number"] + 1 or selection < 1:
                        print("Invalid selection")
                        continue
                    elif selection == chapters[-1]["number"] + 1:
                        sys.exit(0)
                    else:
                        break
                chapter = chapters[selection-1]

                # Get all sections in selected chapter and have user select one
                sections = chapter["sections"]
                for section in sections:
                    print(str(section["canonical_section_number"]) + ". " + section["title"])
                print(str(sections[-1]["number"]+1) + ". " + "[EXIT]")
                while True:
                    selection = input("Select a section: ")
                    try:
                        selection = int(selection)
                    except:
                        print("Please enter a number")
                        continue
                    if selection > sections[-1]["number"] + 1 or selection < 1:
                        print("Invalid selection")
                        continue
                    elif selection == sections[-1]["number"] + 1:
                        sys.exit(0)
                    else:
                        break
                section = sections[selection-1]

                # Solves all problems in given section
                sec_id = section["canonical_section_id"]
                problems = get_problems(code, chapter["number"], section["canonical_section_number"], auth)
                p = 1
                for problem in problems:
                    act_id = problem["id"]
                    parts = problem["parts"]
                    if parts > 0:
                        for part in range(parts):
                            if solve(act_id, sec_id, auth, part, code):
                                print("Solved part {} of problem {}".format(part+1, p))
                            else:
                                print("Failed to solve part {} of problem {}".format(part+1, p))
                    else:
                        if solve(act_id, sec_id, auth, 0, code):
                            print("Solved problem {}".format(p))
                        else:
                            print("Failed to solve problem {}".format(p))
                    p += 1
            except Exception as e: # If an error occurs, try reauthenticating
                print("Ran into an error:\n" + str(e) +"\nAttempting to reauthenticate...")
                response = signin(cfg.USR, cfg.PWD)
                auth = response["session"]["auth_token"]
                usr_id = response["session"]["user_id"]
                break

if __name__ == "__main__":
    main()
