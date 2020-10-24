from datetime import datetime, timedelta
from math import floor
import re

from bs4 import BeautifulSoup

from boards import helpers
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CLASS_JOB_TITLE="jobsearch-JobInfoHeader-title"
XPATH_JOB_LOCATION="(//div[contains(@class, 'jobsearch-InlineCompanyRating')]/div)[last()]"
XPATH_JOB_PRICE="//div[contains(@class, 'jobsearch-JobMetadataHeader-item')]/span"
ID_JOB_DESCRIPTION="jobDescriptionText"
CLASS_JOB_FOOTER="jobsearch-JobMetadataFooter"
XPATH_JOB_LINK="/html/body/table[2]/tbody/tr/td/table/tbody/tr/td[1]/div[*]/h2/a"
ID_PAGE_LOADED="resultsBodyContent"
ID_TOTAL_JOBS="searchCountPages"
XPATH_DETAIL_LOADED="/html/body/div[1]/div[2]/div[3]"
JOB_PORTAL="indeed"
ITEMS_PER_PAGE=10
MAX_PAGES=70

class IndeedPortalParser:
    def __init__(self, url):
        self.url = url
        self.browser = None

    def retrieve_element(self, selector_type, selector):
        '''extracts an element from webdriver'''
        try:
            if selector_type == "class":
                element = self.browser.find_element_by_class_name(selector)
            elif selector_type == "xpath":
                element = self.browser.find_element_by_xpath(selector)
            else:
                element = self.browser.find_element_by_id(selector)

            if element:
                return element.get_attribute("innerHTML").strip()
        except:
            pass

        return None

    def get_job_data(self, url):
        job_detail = {}
        if self.download_url(url, "detail"):
            title = self.retrieve_element("class", CLASS_JOB_TITLE)
            location = self.retrieve_element("xpath", XPATH_JOB_LOCATION)
            price = self.retrieve_element("xpath", XPATH_JOB_PRICE)
            description = self.retrieve_element("id", ID_JOB_DESCRIPTION)
            date_footer = self.retrieve_element("class", CLASS_JOB_FOOTER)

            soup = BeautifulSoup(date_footer, features="html.parser")
            date_footer = soup.get_text()

            # cleanup title and description
            job_detail["title"] = helpers.cleanup_text(title)
            job_detail["description"] = helpers.cleanup_text(description)

            # location
            job_detail["city"] = None
            job_detail["province"] = None
            if location is not None:
                location = re.sub(r'\d+', '', location)

                items_location=location.split(",")
                if len(items_location)==2:
                    city_items = items_location[0].strip().split(" ")
                    if len(city_items)==2:
                        job_detail["city"] = items_location[1].strip()
                    else:
                        job_detail["city"] = items_location[0].strip()

                    province = items_location[1].replace("provincia", "")
                    job_detail["province"] = province.strip()
                else:
                    job_detail["province"] = items_location[0].strip()

            # price
            job_detail["price_start"] = None
            job_detail["price_end"] = None
            job_detail["price_interval"] = None
            job_detail["price_currency"] = "euro"

            # first check interval
            if price is not None:
                if price.endswith("al mes"):
                    job_detail["price_interval"] = "monthly"
                    price = price.replace("al mes", "")
                elif price.endswith("al año"):
                    job_detail["price_interval"] = "yearly"
                    price = price.replace("al año", "")
                elif price.endswith("al día"):
                    job_detail["price_interval"] = "daily"
                    price = price.replace("al día", "")
                elif price.endswith("por hora"):
                    job_detail["price_interval"] = "hourly"
                    price = price.replace("por hora", "")
                elif price.endswith("por semana"):
                    job_detail["price_interval"] = "weekly"
                    price = price.replace("por semana", "")

                # now check range
                price_items = price.split("-")
                if len(price_items)==2:
                    job_detail["price_start"] = helpers.parse_number(price_items[0].strip())
                    job_detail["price_end"] = helpers.parse_number(price_items[1].strip())
                else:
                    job_detail["price_start"] = helpers.parse_number(price_items[0].strip())

            # just get the number
            days_ago = re.findall(r"\d+", date_footer )
            days_to_substract = 0
            if days_ago:
                if len(days_ago)>0:
                    days_to_substract = int(days_ago[0])
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
                            EC.presence_of_element_located((By.ID, ID_PAGE_LOADED)))
                else:
                    WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.XPATH, XPATH_DETAIL_LOADED)))
                return True
            except TimeoutException:
                print("Timed out waiting for page")
        return False

    def get_total_jobs(self, url):
        '''Queries the initial page for the total number of jobs'''
        current_url = str(url).format(0)
        if self.download_url(current_url, "main"):
            num_jobs_element  = self.browser.find_element_by_id(ID_TOTAL_JOBS)
            if num_jobs_element is not None:
                num_jobs_content = num_jobs_element.get_attribute("innerHTML")

                # now split the text and retrieve total jobs
                items = num_jobs_content.split()
                total_jobs = items[3]
                self.browser.quit()
                return int(total_jobs.replace(".", ""))

        self.browser.quit()
        return 0

    def get_jobs(self):
        total_jobs = self.get_total_jobs(self.url)
        num_pages = floor(total_jobs/ITEMS_PER_PAGE)
        if num_pages > MAX_PAGES:
            num_pages=MAX_PAGES

        job_links = []
        for i in range(0,num_pages):
            index=i*10
            current_url = str(self.url).format(index)
            print("Parsing {}".format(current_url))
            if not self.download_url(current_url, "main"):
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
