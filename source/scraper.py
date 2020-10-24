#!/usr/bin/env python3
'''
A job portal web scraper, to extract information about
the job status in Catalonia. Data extracted just with
educative and informative efforts.

Sources:
    http://es.indeed.com
'''

import argparse
import configparser
import csv

from boards import indeed, linkedin
from xvfbwrapper import Xvfb

# default values for portals
VALID_PORTALS = [ 'indeed', 'linkedin' ]
INDEED_PORTAL = 'indeed'
LINKEDIN_PORTAL = 'linkedin'
OUTFILE = 'jobs.csv'

def parse_args():
    '''Parses command line arguments'''

    parser = argparse.ArgumentParser(formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--portal',
            help=("Job portal where to search. Possible values are: %s."
                "Do not pass it to do a complete scrape of all sites" % ','.join(VALID_PORTALS)),
            choices=VALID_PORTALS, type=str)
    parser.add_argument('-o', '--outfile', default=OUTFILE, type=str)
    arguments = parser.parse_args()
    return arguments

class JobPortalScraper():
    '''Main class for portal scraper'''

    def __init__(self, portal, outfile):
        config = configparser.ConfigParser()
        config.read('config.ini')
        #self.infojobs_url = config['urls']['infojobs_url']
        self.indeed_url = config['urls']['indeed_url']
        self.linkedin_url = config['urls']['linkedin_url']

        self.portal = portal
        self.outfile = outfile
        self.all_portals = VALID_PORTALS

    def start(self):
        display = Xvfb()
        display.start()

        # check the portals to use
        if self.portal is None:
            portals = self.all_portals
        else:
            portals = [ self.portal, ]

        # iterate for all portals and start its own parser
        jobs_all_portals = []
        for portal in portals:
            if portal == INDEED_PORTAL:
                parser_indeed = indeed.IndeedPortalParser(self.indeed_url)
                jobs = parser_indeed.get_jobs()
            elif portal == LINKEDIN_PORTAL:
                parser_linkedin = linkedin.LinkedInPortalParser(self.linkedin_url)
                jobs = parser_linkedin.get_jobs()

            if jobs:
                jobs_all_portals = jobs_all_portals + jobs

        # now write to outfile
        with open(self.outfile, "w") as csvfile:
            fieldnames = ["title", "city", "province", "price_start", "price_end", "price_interval",
                    "price_currency", "description", "date", "expertise", "type", "functions",
                    "sectors", "portal"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in jobs_all_portals:
                writer.writerow({'title':item["title"], 'city':item["city"],
                    'province': item["province"], "price_start": item["price_start"],
                    "price_end": item["price_end"], "price_interval": item["price_interval"],
                    "price_currency": item["price_currency"], "description":item["description"],
                    "date": item["date"], "expertise": item.get("expertise", ""),
                    "type": item.get("type", ""), "functions": item.get("functions", ""),
                    "sectors": item.get("sectors", ""), "portal": item["portal"]})
        display.stop()

if __name__ == '__main__':
    args = parse_args()
    jobPortalScraper = JobPortalScraper(args.portal, args.outfile)
    jobPortalScraper.start()
