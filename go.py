from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import cfg

driver = webdriver.Firefox()

# Log into ZyBooks
driver.get("https://learn.zybooks.com/signin")
driver.find_element(By.ID, "ember10").send_keys(cfg.USR)
driver.find_element(By.ID, "ember12").send_keys(cfg.PWD)
driver.find_element(By.CLASS_NAME, "signin-button").click()

# Select a Book
WebDriverWait(driver, 10).until(lambda x: x.find_element(By.CLASS_NAME, "heading"))
books = driver.find_elements(By.CLASS_NAME, "zybook")
names = driver.find_elements(By.CLASS_NAME, "heading")
names.pop() # Removes default ZyBook
p = "Please select a book:"
for z in range(0, len(names)):
    p += "\n" + str(z+1) + ". " + names[z].text
selection = input(p + "\n")
books[int(selection)-1].click()
