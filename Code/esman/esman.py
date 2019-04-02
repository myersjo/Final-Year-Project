import click
import argparse
import csv
import time,datetime
import json
import subprocess
from Common import *

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group()
def general():
    pass

def extractData(csv_infile,json_infile,outfile,col,try_ip, debug):
    try:
        output_file = open(outfile, 'w')
    except:
        timestampPrint("Can't open file {}".format(outfile))
        return
    row_count = 0
    total_records = 0
    company_match_count=0
    start = datetime.datetime.now()
    timestampPrint("Starting...")
    num_lines = getNumLines(csv_infile)
    
    with open(csv_infile,'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        with click.progressbar(csv_reader, length=num_lines, label="Searching {}".format(json_infile)) as bar:
            for row in bar:
                domain = row[col]
                ip = row[col+1]

                if domain is None or domain=='':
                    if debug:
                        timestampPrint("Row {} has an empty domain".format(row_count))
                else:
                    if debug:
                        timestampPrint("{}: Doing {} ".format(row_count, domain))

                    record_count=0
                    with open(json_infile, 'r') as json_file:
                        for record in json_file:
                            if(record.find(domain)) != -1:
                                j_content = json.loads(record)
                                j_content['company'] = row[col-1]
                                j_content['domain'] = domain
                                jstr=json.dumps(j_content)
                                output_file.write(jstr+"\n")
                                record_count += 1

                    if record_count == 0 and try_ip: # try IP instead of domain
                        if debug:
                            timestampPrint("    No records matching domain, trying IP")
                        with open(json_infile, 'r') as json_file:
                            for record in json_file:
                                if(record.find(ip)) != -1:
                                    j_content = json.loads(record)
                                    j_content['company'] = row[col-1]
                                    j_content['ip'] = ip
                                    jstr=json.dumps(j_content)
                                    output_file.write(jstr+"\n")
                                    record_count += 1

                    if debug:
                        timestampPrint("\t{} matching records found".format(record_count))
                    row_count += 1
                    total_records += record_count
                    if record_count > 0:
                        company_match_count += 1

    end = datetime.datetime.now()
    diff = end - start
    print "\n[{}] Finished in {} with {} matching records found for {} companies".format(end, diff, total_records, company_match_count)
    output_file.close()

@general.command(context_settings=CONTEXT_SETTINGS)
@click.option('-c','--csvinfile','csv_infile',required=True,help='CSV file containing list of domains')
@click.option('-j','--jsoninfile','json_infile',required=True,help='JSON file containing list of scan records')
@click.option('-o','--output_file','outfile',required=True,help='JSON file in which to put records (one per line)')
@click.option('--col','col',default=1,help='Column from input file that has the URL (default = 1)')
@click.option('--tryip','try_ip',is_flag=True,help="If set, searches json_infile for IP if no records match domain")
@click.option('--debug','debug',is_flag=True,help="If set, turns on verbose logging")
def extractSubset(csv_infile,json_infile,outfile,col,try_ip, debug):
    extractData(csv_infile,json_infile,outfile,col,try_ip, debug)

@general.command(context_settings=CONTEXT_SETTINGS)
def installDeps():
    timestampPrint('Installing dependencies')
    subprocess.call("../install.sh", shell=True)