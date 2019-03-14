import argparse
import csv
import time,datetime
import json

# Default values
csv_infile="AviationCompanies_DNS.csv"
json_infile="records.fresh"
outfile="av-records.fresh"
tryip=True
col=1

# Parse args
argparser=argparse.ArgumentParser(description='Read a CSV, one (default last) column of which is a URL, then extract matching records from a JSON file')
argparser.add_argument('-c','--csvinfile',     
                    dest='csv_infile',
                    help='CSV file containing list of domains')
argparser.add_argument('-j','--jsoninfile',     
                    dest='json_infile',
                    help='JSON file containing list of scan records')
argparser.add_argument('-o','--output_file',     
                    dest='outfile',
                    help='JSON file in which to put records (one per line)')
argparser.add_argument('--col',     
                    dest='col',
                    help='Column from input file that has the URL')
argparser.add_argument('--tryip',     
                    dest='try_ip',
                    help='True/False; if true, searches for IP if no records match domain. Default True')
args=argparser.parse_args()

if args.csv_infile is not None:
    csv_infile = args.csv_infile
if args.json_infile is not None:
    json_infile = args.json_infile
if args.outfile is not None:
    outfile = args.outfile
if args.col is not None:
    col = args.col
if args.try_ip is not None:
    if "false" in args.try_ip.lower():
        tryip = False

output_file = open(outfile, 'w')
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
