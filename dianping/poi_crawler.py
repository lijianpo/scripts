import time
import re
import os
import sys
import urllib
from getopt import *
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

class TimeoutList:
    page_index_list = []
    page_url_list = []
    def append(self, page_url, page_index):
        if len(self.page_index_list) > 0 and self.page_index_list[-1] == page_index - 1:
            self.page_index_list.pop()
            self.page_url_list.pop()
            return False
        else:
            self.page_index_list.append(page_index)
            self.page_url_list.append(page_url)
            return True
    def get_page_url_list(self):
        for page_url in self.page_url_list:
            yield page_url
    def clear(self):
        self.page_index_list.clear()
        self.page_url_list.clear()

class Crawler:
    city_list = []
    valid_category_url_list = []
    def __init__(self, chromedriver_path, home_url):
        self.driver = webdriver.Chrome(chromedriver_path)
        self.driver.set_page_load_timeout(30)
        self.home_url = home_url
        self.regexcategory = r"search/category/[0-9]+/[0-9]+/g[0-9]+"
        self.regex_citylist = urllib.parse.urljoin(home_url, "[a-z]+")
        self.city_list_url = urllib.parse.urljoin(home_url, "citylist")
    def get_finish_city_path(self):
        return os.path.join(self.outputdir, "finish_city.txt")
    def set_output_dir(self, outputdir):
        self.outputdir = outputdir
    def remove_finish_city(self):
        if os.path.isfile(self.get_finish_city_path()):
            f = open(self.get_finish_city_path(), "r")
            for line in f:
                city = line.strip("\n")
                if city in self.city_list:
                    self.city_list.remove(city)
            f.close()
    def get_cities(self, city):
        if not city:
            self.get_all_city_list()
        else:
            citylist = city.strip("\n").split(",")
            for city in citylist:
                self.city_list.append(city)
        self.remove_finish_city()
    def get_all_city_list(self):
        self.driver.get(self.city_list_url);
        time.sleep(5)
        contain_element = self.driver.find_element_by_id('divPY')
        urls = contain_element.find_elements_by_xpath(".//a")
        for url in urls:
            try:
                href = url.get_attribute("href")
                if re.search(self.regex_citylist, href):
                    city = href[24:]
                    if city not in self.city_list:
                        self.city_list.append(city)
                        print("Prased city: [%s].." % city)
            except Exception as e:
                pass    
    def quit(self):
        self.driver.quit()
    def fetch_root(self, outputdir, city):
        self.set_output_dir(outputdir)
        self.get_cities(city)
        self.fetch_all_cities()
        self.quit()
    def fetch_all_cities(self):
        for city in self.city_list:
            print("Now, fetching city: [%s] .." % city)
            self.fetch_city(city)
            f = open(self.get_finish_city_path(), "a", encoding='utf-8')
            f.write(city + "\n")
            f.close()
    def makesure_directory_exist(self, directory_path):
        if not os.path.isdir(directory_path):
            os.mkdir(directory_path)
    def get_valid_url(self, root_path, page_index):
        if page_index == 0:
            return ""    
        elif page_index == 1:
            return root_path
        else:
            return root_path + "p" + str(page_index)
    def wait_for_loading_finish(self):
        wait_webelement = WebDriverWait(self.driver, 30).until(lambda brow: brow.find_element_by_id("shop-all-list"))
    def get_item_entry_by_link(self, page_url):
        self.driver.get(page_url)
        self.wait_for_loading_finish()
        shoplist = self.driver.find_element_by_id('shop-all-list')
        item_elements = shoplist.find_elements_by_xpath('.//li')
        for item in item_elements:
            item_entry = []
            tit = item.find_element_by_xpath('.//a[@data-hippo-type="shop"]')
            #id
            href = tit.get_attribute("href")
            shopid = href[href.rfind('/')+1:]
            item_entry.append(shopid)
            #title 
            shoptitle = tit.get_attribute("title")
            item_entry.append(shoptitle)
            tag_addr = item.find_element_by_class_name("tag-addr")
            #address
            addr = tag_addr.find_element_by_class_name("addr")
            item_entry.append(addr.text)
            #tags
            lst = tag_addr.find_elements_by_xpath(".//a")
            for ls in lst:
                href = ls.get_attribute("href")
                tag = ls.text
                item_entry.append(tag)
                item_entry.append(href[40:])
            yield "\t".join(item_entry)
    def write_log(self, err_log_path, err_msg, prefix):
        f = open(err_log_path, "a", encoding='utf-8')
        f.write(prefix + err_msg + "\n")
        f.close()
    def parse_valid_category_url_list(self, city, valid_urls_path):
        city_home_url = os.path.join(self.home_url, city)
        self.driver.get(city_home_url);
        time.sleep(5)
        linkelems = self.driver.find_elements_by_xpath('//a')
        for linkelem in linkelems:
            try:
                href = linkelem.get_attribute("href")
                if re.search(self.regexcategory, href):
                    if href not in self.valid_category_url_list:
                        self.valid_category_url_list.append(href)
            except Exception:
                pass    
        self.valid_category_url_list.sort()
        valid_url_file = open(valid_urls_path, "w", encoding='utf-8')
        for valid_category_url in self.valid_category_url_list:
            valid_url_file.write(valid_category_url + "\n")
        valid_url_file.close()
    def remove_finish_pages(self, finish_log_path):
        if os.path.isfile(finish_log_path):
            f = open(finish_log_path, "r")
            for line in f:
                finished_page = line.strip("\n")
                if finished_page in self.valid_category_url_list:
                    self.valid_category_url_list.remove(finished_page)
            f.close()
    def fetch_city(self, city):
        current_output_dir = os.path.join(self.outputdir, city)
        self.makesure_directory_exist(current_output_dir)
        item_entry_path = os.path.join(current_output_dir, "items.txt")
        logfile_path = os.path.join(current_output_dir, "timeout_err.log")
        finish_log_path = os.path.join(current_output_dir, "finish.log")
        valid_urls_path = os.path.join(current_output_dir, "valid_urls.log")
        # Get all valid category url list.
        self.parse_valid_category_url_list(city, valid_urls_path)
        self.remove_finish_pages(finish_log_path)
        self.fetch_items(item_entry_path, logfile_path, finish_log_path)
    def fetch_items(self, item_entry_path, logfile_path, finish_log_path):
        timeout_list = TimeoutList()
        for link in self.valid_category_url_list:
            print("Now, fetch url: %s" % link)
            f = open(item_entry_path, "a", encoding='utf-8')
            f.write("\n#################  BEGIN OF BLOCK [%s]  #################\n" % link[40:])
            for i in range(51):
                try:
                    tmpcurlink = self.get_valid_url(link, i)
                    if not tmpcurlink:
                        continue
                    print("Page %d\t--\t" % i, end='')
                    for item_entry in self.get_item_entry_by_link(tmpcurlink):
                        f.write(item_entry + "\n")
                    print("Done.")
                except TimeoutException:
                    if timeout_list.append(tmpcurlink, i):
                        print("timeout.")
                        continue
                    else:
                        print("timeout again. Done.")
                        break
                except Exception as e:
                    print(e)
                    print("Error. Done.")
                    self.write_log(logfile_path, tmpcurlink, "err: ")
            # Handle timeout list
            for tmpcurlink in timeout_list.get_page_url_list():
                try:
                    print("Now, retry timeout page: %s" % tmpcurlink)
                    for item_entry in self.get_item_entry_by_link(tmpcurlink):
                        f.write(item_entry + "\n")
                    print("Done.")
                except TimeoutException as e:
                    print("Timeout again. Done.")
                    self.write_log(logfile_path, tmpcurlink, "timeout: ")
                except Exception as e:
                    print(e)
                    print("Error, Done.")
                    self.write_log(logfile_path, tmpcurlink, "err: ")
            timeout_list.clear()
            self.write_log(finish_log_path, link, "")
            f.write("#################  END OF BLOCK [%s]  #################\n" % link[40:])
            f.close()

def main():
    chromedriver_path = ""
    outputdir_path = ""
    home_url = ""
    city = ""
    usage = "Usage:\n  crawer.py -d chrome_driver_path -h website_homepage -o output_dir_path -c city1,city2,city3"
    try:
        opts, args = getopt(sys.argv[1:], "d:o:h:c:", ["driver=", "output=", "homepage=", "city="])
        if len(sys.argv) <= 1:
            print(usage)
            sys.exit(0)
        for opt, arg in opts:
            if opt in ("-d", "--driver"):
                chromedriver_path = arg
            elif opt in ("-o", "--output"):
                outputdir_path = arg
            elif opt in ("-h", "--homepage"):
                home_url = arg
            elif opt in ("-c", "--city"):
                city = arg
            else:
                print("Invalid param: %s", opt)
                sys.exit(-1)
    except Exception as e:
        print(e)
        print(usage)
        sys.exit(-1)
    crawler = Crawler(chromedriver_path, home_url)
    crawler.fetch_root(outputdir_path, city)

if __name__ == "__main__":
    main()
