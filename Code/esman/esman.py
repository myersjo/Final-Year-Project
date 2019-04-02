import click
import argparse
import csv
import time,datetime
import json
from Common import *

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group()
def general():
    pass

def extractData(csv_infile,json_infile,outfile,col,try_ip):
    try:
        output_file = open(outfile, 'w')
    except:
        timestampPrint("Can't open file {}".format(outfile))
        return
    row_count = 0
    total_records = 0
    company_match_count=0
    start = datetime.datetime.now()
    print "[{}] Starting...".format(start)
    with open(csv_infile,'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            domain = row[col]
            ip = row[col+1]

            if domain is None or domain=='':
                print "Row {} has an empty domain".format(row_count)
            else:
                print "{}: Doing {} ".format(row_count, domain)

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

                if record_count == 0 and tryip: # try IP instead of domain
                    print "    No records matching domain, trying IP"
                    with open(json_infile, 'r') as json_file:
                        for record in json_file:
                            if(record.find(ip)) != -1:
                                j_content = json.loads(record)
                                j_content['company'] = row[col-1]
                                j_content['ip'] = ip
                                jstr=json.dumps(j_content)
                                output_file.write(jstr+"\n")
                                record_count += 1

                print("\t{} matching records found".format(record_count))
                row_count += 1
                total_records += record_count
                if record_count > 0:
                    company_match_count += 1

    end = datetime.datetime.now()
    diff = end - start
    print "[{}] Finished in {} with {} matching records found for {} companies".format(end, diff, total_records, company_match_count)
    output_file.close()

@general.command(context_settings=CONTEXT_SETTINGS)
@click.option('-c','--csvinfile','csv_infile',required=True,help='CSV file containing list of domains')
@click.option('-j','--jsoninfile','json_infile',required=True,help='JSON file containing list of scan records')
@click.option('-o','--output_file','outfile',required=True,help='JSON file in which to put records (one per line)')
@click.option('--col','col',default=1,help='Column from input file that has the URL')
@click.option('--tryip','try_ip',is_flag=True)
def extractSubset(csv_infile,json_infile,outfile,col,try_ip):
    extractData(csv_infile,json_infile,outfile,col,try_ip)

@general.command(context_settings=CONTEXT_SETTINGS)
def installDeps():
    timestampPrint('Installing dependencies')
    pass