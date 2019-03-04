	#!/usr/bin/python

# Read a file of JSON data and insert data into elasticsearch

import argparse
import json
import time,datetime
import subprocess
from elasticsearch import Elasticsearch # install via  "$ sudo pip install elasticsearch"
from elasticsearch.helpers import bulk

# default value
infile="records.fresh"
es_index="records-fresh"

# command line arg handling
argparser=argparse.ArgumentParser(description='Insert JSON Data to Elasticsearch')
argparser.add_argument('-i','--input',     
                    dest='infile',
                    help='JSON File to be inserted')
argparser.add_argument('--index',     
                    dest='es_index',
                    help='Elasticsearch index to be inserted to')
args=argparser.parse_args()

if args.infile is not None:
    infile=args.infile
if args.es_index is not None:
    es_index=args.es_index

es = Elasticsearch()

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
                time.sleep(10)
            j_content = json.loads(line)
            lines_read += 1
            time.sleep(1)
            yield {
                "_index": es_index,
                "_type": "document",
                "doc": j_content
            }

print("[{}] Starting...".format(datetime.datetime.utcnow()))
(successful_actions, errors) = bulk(es, genLoadJson(), chunk_size=50, request_timeout=30, max_chunk_bytes=5000000, max_retries=3, raise_on_error=False, raise_on_exception=False, stats_only=True)
print("[{}] Finished with {} successful actions ".format(datetime.datetime.now(), successful_actions))
