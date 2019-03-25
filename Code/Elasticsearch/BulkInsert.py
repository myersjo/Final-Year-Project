#!/usr/bin/python

# Read a file of JSON data and insert data into elasticsearch

# python Final-Year-Project/Code/Elasticsearch/BulkInsert.py -i av-noip-2018-records.fresh --index av-records-fresh-geo-ie-20180316 -rd 2018-03-16 --cc IE

import argparse
import json
import time,datetime
import subprocess, os, sys
from elasticsearch import Elasticsearch # install via  "$ sudo pip install elasticsearch"
from elasticsearch.helpers import bulk

# from https://github.com/sftcd/surveys ...
# locally in $HOME/code/surveys
def_surveydir=os.environ['HOME']+'/code/surveys'
sys.path.insert(0,def_surveydir)

from SurveyFuncs import *

# default value
infile="records.fresh"
es_index="records-fresh"
run_date=datetime.date.today()
country_code="IE"

# command line arg handling
argparser=argparse.ArgumentParser(description='Insert JSON Data to Elasticsearch')
argparser.add_argument('-i','--input',     
                    dest='infile',
                    help='JSON File to be inserted')
argparser.add_argument('--index',     
                    dest='es_index',
                    help='Elasticsearch index to be inserted to')
argparser.add_argument('-rd','--rundate',     
                    dest='run_date',
                    help='Run date to be used for Kibana (YYYY-MM-DD)')
argparser.add_argument('-cc','--countrycode',     
                    dest='country_code',
                    help='Two letter country code to be used for Kibana')
args=argparser.parse_args()

if args.infile is not None:
    infile=args.infile
if args.es_index is not None:
    es_index=args.es_index
if args.run_date is not None:
    date=args.run_date
    ymd=date.split('-')
    run_date=datetime.date(int(ymd[0]),int(ymd[1]),int(ymd[2]))
if args.country_code is not None:
    country_code=args.country_code

es = Elasticsearch()
mm_setup()

def genLoadJson():
    lines_read=0
    with open(infile,'r') as f:
        for line in f:
            status = subprocess.check_output(["sudo", "systemctl", "show", "-p", "SubState", "--value", "elasticsearch.service"])
            if "running" not in status:
                subprocess.call(["sudo", "systemctl", "start", "elasticsearch.service"])
                print("[{}] {} lines read. Restarting failed Elasticsearch...".format(datetime.datetime.utcnow(), lines_read))
                time.sleep(20)
            if lines_read % 100 == 0:
                print("[{}] {} lines read".format(datetime.datetime.now(), lines_read))
                time.sleep(1)
            j_content = json.loads(line)
            ip = j_content['ip']
            geoinfo = mm_info(ip)
            j_content['country_code']=geoinfo['cc']
            # j_content['country_code']=country_code
            j_content['run_date']=run_date.strftime('%Y-%m-%d')
            geolocation = { "location": { "lat": geoinfo['lat'], "lon": geoinfo['long']}}
            # j_content['geoip']['location']['lat']=geoinfo['lat']
            # j_content['geoip']['location']['lon']=geoinfo['lon']
            j_content['geoip']=geolocation
            j_content['asn']=geoinfo['asn']
            j_content['asndec']=geoinfo['asndec']

            lines_read += 1
            time.sleep(0.5)
            yield {
                "_index": es_index,
                "_type": "document",
                "doc": j_content
            }

print("[{}] Starting...".format(datetime.datetime.utcnow()))
(successful_actions, errors) = bulk(es, genLoadJson(), chunk_size=50, request_timeout=30, max_chunk_bytes=5000000, max_retries=3, raise_on_error=False, raise_on_exception=False, stats_only=True)
print("[{}] Finished with {} successful actions ".format(datetime.datetime.now(), successful_actions))
