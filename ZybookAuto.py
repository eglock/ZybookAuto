from __future__ import annotations
import os
import sys
import json
import requests
import hashlib
import random
from typing import Union
from urllib import parse
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
    books = requests.get(f"https://zyserver.zybooks.com/v1/user/{usr_id}/items?items=%5B%22zybooks%22%5D&auth_token={auth}").json()
    if not books["success"]:
        raise Exception("Failed to get books")
    books = books["items"]["zybooks"]
    for book in books:
        if book["autosubscribe"]:
            books.remove(book)
    return books

# Gets chapters along with their sections
def get_chapters(code, auth):
    chapters = requests.get(f"https://zyserver.zybooks.com/v1/zybooks?zybooks=%5B%22{code}%22%5D&auth_token={auth}").json()
    return chapters["zybooks"][0]["chapters"]

# Returns all problems in a section
def get_problems(code, chapter, section, auth):
    problems = requests.get(f"https://zyserver.zybooks.com/v1/zybook/{code}/chapter/{chapter}/section/{section}?auth_token={auth}").json()
    return problems["section"]["content_resources"]

# Spoofs "time_spent" anywhere from 1 to 60 seconds.
def spend_time(auth, sec_id, act_id, part, code):
    global t_spfd
    t  = random.randint(1, 60)
    t_spfd += t
    return requests.post(f"https://zyserver2.zybooks.com/v1/zybook/{code}/time_spent", json={"time_spent_records":[{"canonical_section_id":sec_id,"content_resource_id":act_id,"part":part,"time_spent":t,"timestamp":gen_timestamp()}],"auth_token":auth}).json()["success"]

# Gets current buildkey, used when generating md5 checksum
def get_buildkey():
    class Parser(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, Union[str, None]]]) -> None:
            if tag == "meta" and attrs[0][1] == "zybooks-web/config/environment":
                self.data = json.loads(parse.unquote(attrs[1][1]))['APP']['BUILDKEY']
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
    ms = str(random.randint(0, 999)).rjust(3, "0")
    ts = nt.strftime(f"%Y-%m-%dT%H:%M.{ms}Z")
    return ts

# Generates md5 hash
def gen_chksum(act_id, ts, auth, part):
    md5 = hashlib.md5()
    md5.update(f"content_resource/{act_id}/activity".encode("utf-8"))
    md5.update(ts.encode("utf-8"))
    md5.update(auth.encode("utf-8"))
    md5.update(str(act_id).encode("utf-8"))
    md5.update(str(part).encode("utf-8"))
    md5.update("true".encode("utf-8"))
    md5.update(get_buildkey().encode("utf-8"))
    return md5.hexdigest()

# Solves a single part of a problem
def solve_part(act_id, sec_id, auth, part, code):
    url = f"https://zyserver.zybooks.com/v1/content_resource/{act_id}/activity"
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

# Solves all problems in given section
def solve_section(section, code, chapter, auth):
    sec_name = f"{chapter['number']}.{section['number']}"
    print(f"Starting section {sec_name}")
    sec_id = section["canonical_section_id"]
    try:
        problems = get_problems(code, chapter["number"], section["number"], auth)
    except KeyError as e:
        print(f"Failed solving {sec_name}")
        print(f"{str(e)} is missing, retrying with canonical section number...")
        try:
            problems = get_problems(code, chapter["number"], section["canonical_section_number"], auth)
            pass
        except KeyError:
            print(f"Failed solving {chapter['number']}.{section['canonical_section_number']}")
            return
    p = 1
    for problem in problems:
        act_id = problem["id"]
        parts = problem["parts"]
        if parts > 0:
            for part in range(parts):
                if solve_part(act_id, sec_id, auth, part, code):
                    print(f"Solved part {part+1} of problem {p}")
                else:
                    print(f"Failed to solve part {part+1} of problem {p}")
        else:
            if solve_part(act_id, sec_id, auth, 0, code):
                print(f"Solved problem {p}")
            else:
                print(f"Failed to solve problem {p}")
        p += 1

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
                    print(f"{i}. {book['title']}")
                    i += 1
                print(f"{i}. [EXIT]")
                while True:
                    selection = input("\nSelect a Zybook: ")
                    try:
                        selection = int(selection)
                    except:
                        print("Please enter a number")
                        continue
                    if selection == i:
                        sys.exit(0)
                    elif selection > i or selection < 1:
                        print("Invalid selection")
                        continue
                    else:
                        break
                book = books[int(selection)-1]

                # Get all chapters in selected book and have user select one
                code = book["zybook_code"]
                chapters = get_chapters(code, auth)
                print("\n")
                for chapter in chapters:
                    print(f'{chapter["number"]}. {chapter["title"]}')
                print(f'{chapters[-1]["number"] + 1}. [BATCH]')
                print(f'{chapters[-1]["number"] + 2}. [EXIT]')
                selection = input("\nSelect a chapter: ")
                while True:
                    try:
                        selection = int(selection)
                    except:
                        print("Please enter a number")
                        selection = input("\nSelect a chapter: ")
                        continue
                    if selection > chapters[-1]["number"] + 2 or selection < 1:
                        print("Invalid selection")
                        selection = input("\nSelect a chapter: ")
                        continue
                    elif selection == chapters[-1]["number"] + 1: # Batch processing
                        print("\nEnter the chapters/sections you want to solve separated by spaces:\n(e.g. \"1.1 1.2 1.3 4 5 6\" will solve sections 1 - 3 in chapter 1 and all of chapters 4 - 6)\n")
                        to_solve = input().split()
                        print("\n")
                        for x in to_solve:
                            if "." in x:
                                x = x.split(".")
                                try:
                                    x[0] = int(x[0])
                                    x[1] = int(x[1])
                                except:
                                    print("Invalid selection")
                                    break
                                if x[0] > chapters[x[0]-1]["sections"][-1]["canonical_section_number"] or x[0] < 1 or x[1] < 1:
                                    print(f'{x[1]} is not a section in chapter {x[0]}')
                                    break
                                chapter = chapters[x[0]-1]
                                section = chapter["sections"][x[1]-1]
                                solve_section(section, code, chapter, auth)
                            else:
                                try:
                                    x = int(x)
                                except:
                                    print("Invalid selection")
                                    break
                                if x > chapters[-1]["number"] + 1 or x < 1:
                                    print(f'{x} is an invalid chapter')
                                    break
                                chapter = chapters[x-1]
                                for section in chapter["sections"]:
                                    solve_section(section, code, chapter, auth)
                        continue
                    elif selection == chapters[-1]["number"] + 2:
                        sys.exit(0)
                    else:
                        break
                chapter = chapters[selection-1]

                # Get all sections in selected chapter and have user select one
                sections = chapter["sections"]
                print("\n")
                for section in sections:
                    print(f'{section["canonical_section_number"]}. {section["title"]}')
                print(f'{sections[-1]["number"]+1}. [EXIT]')
                while True:
                    selection = input("\nSelect a section: ")
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
                print("\n")
                solve_section(section, code, chapter, auth)
            except KeyboardInterrupt:
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
            except Exception as e: # If an error occurs, try reauthenticating
                print(f"\nRan into an error:\n{e}\nAttempting to reauthenticate...\n")
                response = signin(cfg.USR, cfg.PWD)
                auth = response["session"]["auth_token"]
                usr_id = response["session"]["user_id"]
                break

if __name__ == "__main__":
    main()
