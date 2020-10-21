from datetime import datetime, timedelta
import re

from boards import helpers
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

XPATH_JOB_TITLE="//h1[@class='topcard__title']"
XPATH_JOB_LOCATION="//span[contains(@class, 'topcard__flavor--bullet')]"
CLASS_JOB_DESCRIPTION="show-more-less-html__markup"
XPATH_JOB_DATE="//span[@class='topcard__flavor--metadata posted-time-ago__text']"
XPATH_JOB_EXPERTISE="/html/body/main/section[1]/section[3]/ul/li[1]/span"
XPATH_JOB_TYPE="/html/body/main/section[1]/section[3]/ul/li[2]/span"
XPATH_JOB_FUNCTIONS="//li[@class='job-criteria__item'][3]/span"
XPATH_JOB_SECTORS="//li[@class='job-criteria__item'][4]/span"
XPATH_JOB_LINK="//a[contains(@class, 'result-card__full-card-link')]"
ID_TOTAL_JOBS="searchCountPages"
XPATH_DETAIL_LOADED="/html/body/main/section[1]"
JOB_PORTAL="linkedin"
ITEMS_PER_PAGE=25
MAX_PAGES=int(1000/ITEMS_PER_PAGE)

class LinkedInPortalParser:
    def __init__(self, url):
        self.url = url
        self.browser = None

    def retrieve_element(self, selector_type, selector, single=True):
        '''extracts an element from webdriver'''
        try:
            if selector_type == "class":
                if single:
                    element = self.browser.find_element_by_class_name(selector)
                else:
                    elements = self.browser.find_elements_by_class_name(selector)
            elif selector_type == "xpath":
                if single:
                    element = self.browser.find_element_by_xpath(selector)
                else:
                    elements = self.browser.find_elements_by_xpath(selector)
            else:
                if single:
                    element = self.browser.find_element_by_id(selector)
                else:
                    elements = self.browser.find_elements_by_id(selector)

            if single and element:
                return element.get_attribute("innerHTML").strip()
            if not single and elements:
                element_list = []
                for item in elements:
                    element_list.append(item.get_attribute("innerHTML").strip())
                return ",".join(element_list)
        except:
            pass

        return None

    def get_job_data(self, url):
        job_detail = {}
        if self.download_url(url, "detail"):
            title = self.retrieve_element("xpath", XPATH_JOB_TITLE)
            location = self.retrieve_element("xpath", XPATH_JOB_LOCATION)
            description = self.retrieve_element("class", CLASS_JOB_DESCRIPTION)
            job_detail["expertise"] = self.retrieve_element("xpath", XPATH_JOB_EXPERTISE)
            job_detail["type"] = self.retrieve_element("xpath", XPATH_JOB_TYPE)
            job_detail["functions"] = self.retrieve_element("xpath", XPATH_JOB_FUNCTIONS, False)
            job_detail["sectors"] = self.retrieve_element("xpath", XPATH_JOB_SECTORS, False)
            job_date = self.retrieve_element("xpath", XPATH_JOB_DATE)

            # cleanup title and description
            job_detail["title"] = helpers.cleanup_text(title)
            if description is not None:
                job_detail["description"] = helpers.cleanup_text(description)
            else:
                job_detail["description" ] = None

            # location
            job_detail["city"] = None
            job_detail["province"] = None
            if location is not None:
                items_location=location.split(" ")
                if len(items_location)>0:
                    job_detail["province"] = items_location[0].strip()

            # no price, nearly any offer shows it
            job_detail["price_start"] = None
            job_detail["price_end"] = None
            job_detail["price_interval"] = None
            job_detail["price_currency"] = "euro"

            # just get the number
            job_detail["date"]=None
            if job_date:
                days_ago = re.findall(r'\d+', job_date )
                days_to_substract = 0
                if days_ago:
                    if len(days_ago)>0:
                        if job_date.endswith("días") or job_date.endswith("día"):
                            days_to_substract = int(days_ago[0])
                        elif job_date.endswith("semanas") or job_date.endswith("semana"):
                            days_to_substract=int(days_ago[0])*7
                        elif job_date.endswith("meses") or job_date.endswith("mes"):
                            days_to_substract=int(days_ago[0])*30
                job_detail["date"]=(
                        datetime.today() - timedelta(days=days_to_substract)).strftime('%Y-%m-%d')

            # add portal
            job_detail["portal"]=JOB_PORTAL
            self.browser.quit()
            return job_detail

        return None

    def download_url(self, url, download_type):
        '''Downloads the given url and waits until complete'''
        self.browser = helpers.download_url(url)
        if self.browser:
            try:
                if download_type=="main":
                    WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.XPATH, XPATH_JOB_LINK)))
                else:
                    WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.XPATH, XPATH_DETAIL_LOADED)))
                return True
            except TimeoutException:
                print("Timed out waiting for page")
        return False

    def get_jobs(self):
        '''extracts all jobs from the page'''

        job_links = []
        for i in range(0, MAX_PAGES):
            start = i*ITEMS_PER_PAGE
            print("Parsing %s" % self.url.format(start))
            if not self.download_url(self.url.format(start), "main"):
                continue
            # now collect all links
            job_entries = self.browser.find_elements_by_xpath(XPATH_JOB_LINK)
            if job_entries is not None:
                for item in job_entries:
                    entry_link = item.get_attribute("href")
                    if entry_link is not None:
                        job_links.append(entry_link)
            self.browser.quit()

        # iterate over each job link and parse the content
        job_entries = []
        for link in job_links:
            print("Parsing job detail %s" % link)
            job_data = self.get_job_data(link)
            if job_data:
                job_entries.append(job_data)

        # return content
        return job_entries
