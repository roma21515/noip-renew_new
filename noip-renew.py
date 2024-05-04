#!/usr/bin/env python3
# Copyright 2017 loblab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re, os, sys, time
from argparse import ArgumentParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

from mail import buildService, verifyCode

LOGIN_URL = "https://www.noip.com/login"
HOST_URL = "https://my.noip.com/dynamic-dns"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:64.0) Gecko/20100101 Firefox/64.0"

class Robot:

  def __init__(self, username: str, password: str, token: str):
    self.token = token
    self.username = username
    self.password = password

    options = webdriver.ChromeOptions()
    #added for Raspbian Buster 4.0+ versions. Check https://www.raspberrypi.org/forums/viewtopic.php?t=258019 for reference.
    options.add_argument("disable-features=VizDisplayCompositor")
    options.add_argument("headless")
    options.add_argument("no-sandbox") # need when run in docker
    options.add_argument("window-size=1200x800")
    options.add_argument(f"user-agent={USER_AGENT}")
    if 'https_proxy' in os.environ:
      options.add_argument("proxy-server=" + os.environ['https_proxy'])
    browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    browser.set_page_load_timeout(90) # Extended timeout for Raspberry Pi.

    self.browser = browser

  def login(self):
    logging.info(f"Opening {LOGIN_URL}...")
    self.browser.get(LOGIN_URL)

    logging.info("Logging in...")
    ele_usr = self.browser.find_element(By.NAME ,"username")
    ele_pwd = self.browser.find_element(By.NAME, "password")
    ele_usr.send_keys(self.username)
    ele_pwd.send_keys(self.password)

    self.browser.find_element(By.ID, "clogs-captcha-button").click()

    if "noip.com/2fa/verify" in self.browser.current_url:
      attempts = 0
      now = int(time.time())
      service = buildService(self.token)
      
      if not service:
        return logging.error(f"Gmail API service not being built, script will end here.")
      
      logging.info(f"Gmail API service built, start fetching emails...")

      while True:
        attempts += 1
        if attempts > 30:
          logging.warning(f"Failed to get verification code (timeout)")
          return None
        
        logging.info(f"Attempting to get verification code from Gmail API ({attempts})")
        code = verifyCode(service, now)

        if code: break # Exit check loop if code is vaild
        time.sleep(5) # Prevent too many requests 
        
        # Click "resend email" button if it's enabled
        resendBtn = self.browser.find_element(By.ID, "resend")
        if (resendBtn.is_enabled()) : resendBtn.click()

      logging.info(f"Successfully got the verification code !")
      input2fa = self.browser.find_element(By.ID, "otp-input").find_elements(By.TAG_NAME, "input")
      
      for index, element in enumerate(input2fa):
        element.send_keys(str(code)[index])

      logging.info(f"Current login URL = {self.browser.current_url}")
      self.browser.find_element(By.NAME, "submit").click()
    
    logging.debug(f"Current wait URL = {self.browser.current_url}")
    self.browser.refresh() # Refresh page to make sure page be redirect
    try: # Wait for dashboard to load
      logging.debug(f"Current wait URL = {self.browser.current_url}")
      WebDriverWait(self.browser, 30).until(EC.presence_of_element_located((By.ID, "app")))
    except TimeoutException:
      return logging.error("Cannot load dashboard page, login may not success")

    logging.info("Login successfuly")
    return True

  def updateHosts(self):
    count = 0
    iteration = 1
    next_renewal = []

    self.__openHostsPage()
    hosts = self.fetchHosts()
    for host in hosts:
      hostLink = self.__fetchHostLink(host, iteration) # This is for if we wanted to modify our Host IP.
      hostBtn = self.__fetchHostButton(host, iteration) # This is the button to confirm our free host
      expDays = self.__fetchHostExpirationDays(host, iteration)
      hostName = hostLink.text
      next_renewal.append(expDays)
      logging.info(f"{hostName} expires in {str(expDays)} days")

      if self.__updateHost(hostBtn, hostName):
        count += 1
      
      iteration += 1
    self.browser.save_screenshot("results.png")
    logging.info(f"Confirmed hosts: {count}")

    return True

  def __openHostsPage(self):
    logging.info(f"Opening {HOST_URL}...")
    self.browser.get(HOST_URL)
    try: 
      WebDriverWait(self.browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME,'table-striped-row')))
    except TimeoutException:
      logging.error("Timeout to wait for element \"table-striped-row\", host page may not load properly")
      return
    logging.info("Host page loaded successfully")

    # print("I wanna close")
    # time.sleep(1000)

  def __updateHost(self, hostBtn: WebElement, hostName: str) -> bool:
    if hostBtn == None:
      logging.info(f"Host: {hostName} do not need to update")
      return False
    
    hostBtn.click()
    logging.info(f"Host: {hostName} has been updated.")
    time.sleep(3)

    intervention = False
    try:
      if self.browser.find_elements(By.XPATH, "//h2[@class='big']")[0].text == "Upgrade Now":
        intervention = True
    except:
      pass

    if intervention:
      raise Exception("Manual intervention required. Upgrade text detected.")

    self.browser.save_screenshot(f"{hostName}_success.png")

  @staticmethod
  def __fetchHostExpirationDays(host: 'WebElement', iteration):
    matches = host.find_elements(By.XPATH, ".//a[@class='no-link-style']")
    if not len(matches): return 0
    return int(re.search(r"\d+", matches[0]))

  @staticmethod
  def __fetchHostLink(host: 'WebElement', iteration):
    return host.find_element(By.XPATH, r".//a[@class='link-info cursor-pointer']")

  @staticmethod
  def __fetchHostButton(host: 'WebElement', iteration):
    try: 
      return host.find_element(By.XPATH, r".//following-sibling::td[4]/button[contains(@class, 'btn')]")
    except:
      logging.info("Host \"confirm\" button not found")
      return None 

  def fetchHosts(self):
    host_tds = self.browser.find_elements(By.XPATH, "//td[@data-title=\"Host\"]")
    if len(host_tds) == 0:
      raise Exception("No hosts or host table rows not found")
    return host_tds

  def renew(self):
    self.login()
    self.updateHosts()
    self.browser.quit()

def main():
  logging.basicConfig(
    level = logging.INFO,
    format = '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt = '%Y/%m/%d %I:%M:%S'
  )

  parser = ArgumentParser()

  parser.add_argument("-u", "--username")
  parser.add_argument("-p", "--password")
  parser.add_argument("-t", "--token-path", default="token.json")
  parser.add_argument("-e", "--environment-variable", action='store_true')
  parser.add_argument("-r", "--max-retry", default=30)

  args = parser.parse_args()

  if not ( (args.username and args.password) or (args.environment_variable) ):
    if not (args.username or args.password or args.environment_variable):
      parser.error("Please provide your login information with [\"-u\" and \"-p\"] or [\"-e\"] ")

    if args.password ^ args.username: 
      parser.error("Please provide both username and password")
    
  token = args.token_path if not args.environment_variable else None
  username = args.username if (args.username) else os.environ.get("username")
  password = args.password if (args.password) else os.environ.get("password")

  if not (username and password):
    parser.error("Environment variables for username and password not found")

  return Robot(username, password, token).renew()

if __name__ == "__main__": sys.exit(main())