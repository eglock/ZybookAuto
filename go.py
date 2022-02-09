from selenium import webdriver
from selenium.webdriver.common.by import By

import cfg

driver = webdriver.Firefox()

driver.get("https://learn.zybooks.com/signin")
driver.find_element(By.ID, "ember10").send_keys(cfg.USR)
driver.find_element(By.ID, "ember12").send_keys(cfg.PWD)
driver.find_element(By.CLASS_NAME, "signin-button").click()