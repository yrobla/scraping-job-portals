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

from boards import indeed

# default values for portals
VALID_PORTALS = [ 'indeed' ]
INDEED_PORTAL = 'indeed'
OUTFILE = 'jobs.csv'

def parse_args():
    '''Parses command line arguments'''

    parser = argparse.ArgumentParser(formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--portal',
            help=("Job portal where to search. Possible values are: indeed."
                "Do not pass it to do a complete scrape of all sites"),
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
        self.portal = portal
        self.outfile = outfile
        self.all_portals = VALID_PORTALS

    def start(self):
        # check the portals to use
        if self.portal is None:
            portals = self.all_portals
        else:
            portals = [ self.portal, ]

        # iterate for all portals and start its own parser
        jobs_all_portals = []
        for portal in portals:
            #if portal == INFOJOBS_PORTAL:
            #    parser_infojobs = infojobs.InfojobsPortalParser(self.infojobs_url)
            #    jobs = parser_infojobs.get_jobs()

            if portal == INDEED_PORTAL:
                parser_indeed = indeed.IndeedPortalParser(self.indeed_url)
                jobs = parser_indeed.get_jobs()

                if jobs:
                    jobs_all_portals = jobs_all_portals + jobs

        # now write to outfile
        with open(self.outfile, "w") as csvfile:
            fieldnames = ["title", "city", "province", "price_start", "price_end", "price_interval",
                    "price_currency", "description", "date", "portal"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in jobs_all_portals:
                writer.writerow({'title':item["title"], 'city':item["city"],
                    'province': item["province"], "price_start": item["price_start"],
                    "price_end": item["price_end"], "price_interval": item["price_interval"],
                    "price_currency": item["price_currency"], "description":item["description"],
                    "date": item["date"], "portal": item["portal"]})


if __name__ == '__main__':
    args = parse_args()
    jobPortalScraper = JobPortalScraper(args.portal, args.outfile)
    jobPortalScraper.start()
