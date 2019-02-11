#!/usr/bin/python

# Read a file of JSON data and insert data into elasticsearch

import argparse
import json
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
    with open(infile,'r') as f:
        for line in f:
            j_content = json.loads(line)
            yield {
                "_index": es_index,
                "_type": "document",
                "doc": j_content
            }


bulk(es, genLoadJson())