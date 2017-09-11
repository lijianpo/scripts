# -*- coding: utf-8 -*-
# OS: windows
# Python: 3.4.3
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

# fill user info
# NOTE: Replace the chrome driver path with your local path.
chrome_driver_path = r"C:\Users\lijianpo\AppData\Local\Google\Chrome\Application\chromedriver.exe"
username = ""
password = ""

# check chrome driver
if not os.path.exists(chrome_driver_path):
	print("Can NOT find chrome driver path, please check.")
	sys.exit(1)

# init webdriver
driver = webdriver.Chrome(chrome_driver_path)
driver.set_page_load_timeout(30)
print("Starting chrome browser..")
driver.get("https://kyfw.12306.cn/otn/leftTicket/init")

# fill username and password
if username and password:
	driver.find_element_by_id("login_user").click()
	time.sleep(3)
	driver.find_element_by_id("username").send_keys(username)
	driver.find_element_by_id("password").send_keys(password)

# test if login already
login = False
while not login:
	try:
		print ("Wait for 3 seconds to login.")
		WebDriverWait(driver, 3).until(lambda browser: browser.find_element_by_id('regist_out'))
		logout_btn = driver.find_element_by_id('regist_out')
		if logout_btn.text == "退出":
			login = True
		else:
			time.sleep(3)
	except Exception as e:
		pass

print("You have login.")
try:
	WebDriverWait(driver, 5).until(lambda browser: browser.find_element_by_link_text('车票预订'))
	driver.find_element_by_link_text("车票预订").click()
except Exception as e:
	print("页面加载中...")
	pass

query_counter = 0
while True:
	try:
		WebDriverWait(driver, 1).until(lambda browser: browser.find_element_by_id('auto_query'))
		check_box = driver.find_element_by_id('auto_query')
		# test if auto submit checkbox is check.
		if check_box.is_selected():
			# query ticket
			try:
				query_button = driver.find_element_by_id("query_ticket")
				if query_button.text == "停止查询":
					# Stop query first, then new query
					query_button.click()
					query_button.click()
				elif query_button.text == "查询":
					query_button.click()
				query_counter += 1
				WebDriverWait(driver, 1).until(lambda browser: browser.find_element_by_link_text('提交'))
				driver.find_element_by_link_text('提交').click()
				print("已为您查询到了一张车票。。")
				time.sleep(60*30)
			except TimeoutException as e:
				print("已为你完成 %d 次查询.." % query_counter)
			except Exception as e:
				try:
					WebDriverWait(driver, 1).until(lambda browser: browser.find_element_by_id('qd_closeDefaultWarningWindowDialog_id'))
					print("网络繁忙..")
					driver.find_element_by_id('qd_closeDefaultWarningWindowDialog_id').click()
				except Exception as b:
					print("页面加载中..")
		else:
			print("Wait for auto query checkbox is checked..")
			time.sleep(2)
	except Exception:
			pass
