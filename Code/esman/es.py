import click

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

els = Elasticsearch()
mm_setup()

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group()
def elastic():
    pass

def genLoadJson(infile, es_index, run_date, country_code):
    lines_read=0
    res = subprocess.check_output(["sudo", "wc", "-l", infile])
    num_lines = int(res.split(' ')[0])
    with open(infile,'r') as f:
        with click.progressbar(f, length=num_lines) as bar:
            for line in bar:
                status = subprocess.check_output(["sudo", "systemctl", "show", "-p", "SubState", "--value", "elasticsearch.service"])
                if "running" not in status:
                    subprocess.call(["sudo", "systemctl", "start", "elasticsearch.service"])
                    print("\n[{}] {} lines read. Restarting failed Elasticsearch...".format(datetime.datetime.utcnow(), lines_read))
                    time.sleep(20)
                if lines_read % 100 == 0:
                    print("\n[{}] {} lines read".format(datetime.datetime.now(), lines_read))
                    time.sleep(1)
                j_content = json.loads(line)
                ip = j_content['ip']
                geoinfo = mm_info(ip)
                # j_content['country_code']=geoinfo['cc']
                j_content['country_code']=country_code
                j_content['run_date']=run_date.strftime('%Y-%m-%d')
                geolocation = { "location": { "lat": geoinfo['lat'], "lon": geoinfo['long']}}
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

@elastic.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--input', 'infile', required=True, help='JSON File to be inserted')
@click.option('--index', 'es_index', required=True, prompt=True, help='Elasticsearch index to be inserted to')
@click.option('-rd', '--rundate', 'run_date', type=click.DateTime(['%Y-%m-%d']), default=datetime.date.today().strftime('%Y-%m-%d'), help="Run date to be used for Kibana (YYYY-MM-DD)")
@click.option('-cc','--countrycode', 'country_code', default="IE", help='Two letter country code to be used for Kibana')
def insert(infile, es_index, run_date, country_code):
    print("[{}] Starting...".format(datetime.datetime.utcnow()))
    (successful_actions, errors) = \
        bulk(els, 
            genLoadJson(infile, es_index, run_date, country_code), 
            chunk_size=50, 
            request_timeout=30, 
            max_chunk_bytes=5000000, 
            max_retries=3, 
            raise_on_error=False, 
            raise_on_exception=False, 
            stats_only=True)
    print("[{}] Finished with {} successful actions ".format(datetime.datetime.now(), successful_actions))

@elastic.command(context_settings=CONTEXT_SETTINGS)
def viewAllIndices():
    indices = els.cat.indices(index='*',
        bytes='m',
        v=True)

    print(indices)


@elastic.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--index', 'index', required=True, prompt=True)
@click.confirmation_option()
def deleteIndex(index):
    try:
        els.indices.delete(index=index)
        click.echo('{} deleted'.format(index))
    except:
        click.echo('There was a problem deleting index {}'.format(index))
