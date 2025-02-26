#!/usr/bin/python
# 
# Copyright (C) 2018 stephen.farrell@cs.tcd.ie
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Read a CSV, one (default last) column of which is a URL, then append
# a bunch of Web derived values to the row and write out to the output 
# file

import csv
import dns.resolver #import the module

import os, sys, argparse, tempfile, gc
import json
import jsonpickle # install via  "$ sudo pip install -U jsonpickle"
import time, datetime
from dateutil import parser as dparser  # for parsing time from comand line and certs
import pytz # for adding back TZ info to allow comparisons
import subprocess

# from https://github.com/sftcd/surveys ...
# locally in $HOME/code/surveys
def_surveydir=os.environ['HOME']+'/code/surveys'
sys.path.insert(0,def_surveydir)

#codedir=os.path.dirname(os.path.realpath(__file__))
#pdir=os.path.dirname(codedir)
#sys.path.insert(0,pdir)

from SurveyFuncs import *


myResolver = dns.resolver.Resolver() #create a new instance named 'myResolver'

# command line arg handling 
argparser=argparse.ArgumentParser(description='Read a CSV, one (default last) column of which is a URL, then append a bunch of Web derived values to the row and write out to the output file')
argparser.add_argument('-i','--infile',     
                    dest='infile',
                    help='CSV file containing list of domains')
argparser.add_argument('-o','--output_file',     
                    dest='outfile',
                    help='CSV file in which to put records (one per line)')
argparser.add_argument('-c','--col',     
                    dest='col',
                    help='column from input file that has the URL')
argparser.add_argument('-s','--scandate',     
                    dest='scandatestring',
                    help='time at which to evaluate certificate validity')
args=argparser.parse_args()

# scandate is needed to determine certificate validity, so we support
# the option to now use "now"
if args.scandatestring is None:
    scandate=datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    #print >> sys.stderr, "No (or bad) scan time provided, using 'now'"
else:
    scandate=dparser.parse(args.scandatestring).replace(tzinfo=pytz.UTC)
    print >> sys.stderr, "Scandate: using " + args.scandatestring + "\n"


def_country='IE'
country=def_country

def wr_dummy(row,wr):
    dummy=[]
    # port 80
    # analysis[port]['status_code']=-1
    dummy.append(-1)
    # analysis[port]['body_len']=-1
    dummy.append(-1)
    # port 443, no SNI
    # analysis[port]['status_code']=-1
    dummy.append(-1)
    # analysis[port]['body_len']=-1
    dummy.append(-1)
    # analysis[port]['names']=''
    dummy.append('')
    # analysis[port]['fp']=''
    dummy.append('')
    # analysis[port]['timely']=-1
    dummy.append(-1)
    # analysis[port]['self_signed']=-1
    dummy.append(-1)
    # analysis[port]['rsalen']=-1
    dummy.append(-1)
    # analysis[port]['cipher_suite']=-1
    dummy.append(-1)
    # analysis[port]['browser_trusted']=-1
    dummy.append(-1)
    # port 443, with SNI
    # analysis[port]['status_code']=-1
    dummy.append(-1)
    # analysis[port]['body_len']=-1
    dummy.append(-1)
    # analysis[port]['names']=''
    dummy.append('')
    # analysis[port]['fp']=''
    dummy.append('')
    # analysis[port]['timely']=-1
    dummy.append(-1)
    # analysis[port]['self_signed']=-1
    dummy.append(-1)
    # analysis[port]['rsalen']=-1
    dummy.append(-1)
    # analysis[port]['cipher_suite']=-1
    dummy.append(-1)
    # analysis[port]['browser_trusted']=-1
    dummy.append(-1)
    row += dummy
    wr.writerow(row)

def run_zgrab(pparms, port, path, ztimeout, host, addr):
    cmd='zgrab '+  pparms[port] + " -http " + path + " " + ztimeout
    print "cmd: " + cmd
    proc=subprocess.Popen(cmd.split(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    # 443 is different due to SNI, need to provide host, not address
    if port=='443-with-sni':
        #print "doing: port: " + port + " |" + host + "| " + cmd
        # man it took me a while to figure that "\n" below was needed;-(
        pc=proc.communicate(input=host + "\n")
    else:
        #print "doing: port: " + port + " |" + str(addr) + "| " + cmd
        pc=proc.communicate(input=str(addr).encode())
    lines=pc[0].split('\n')
    return lines, pc, cmd

def usage():
    print >>sys.stderr, "usage: " + sys.argv[0] + " -i <in.csv> -o <out.csv> [-c <col1>]"
    print >>sys.stderr, "    Read a CSV, one (default last) column of which is a URL, then append a "
    print >>sys.stderr, "    bunch of Web derived values to the row and write out to the output file"
    sys.exit(1)

if args.infile is None:
    usage()

if args.outfile is None:
    usage()

col=-1
if args.col:
    col=int(args.col)

of=open(args.outfile,'w')
wr=csv.writer(of)

count=0

# encoder options
jsonpickle.set_encoder_options('json', sort_keys=True, indent=2)
jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=2)

# default timeout for zgrab, in seconds
ztimeout=' --timeout 4'
# port parameters
pparms={ 
        '80': '-port 80',
        '443-with-sni': '--port 443 --lookup-domain --tls',
        '443': '-port 443 -tls',
        }

with open(args.infile, 'r') as f:
    r = csv.reader(f)
    for row in r:
        url=row[col]
        analysis={}
        if url is None or url=='':
            print "Row " + str(count) + " has an empty URL"
            # add dummy cols to row, 
            wr_dummy(row,wr)
        else:
            print "Doing " + url
            # figure hostname from url
            # and figure pathname from url
            if "//" in url:
                hoststart=url.find("//")+2
                hostend=url.find("/",hoststart+1)
                if hostend==-1:
                    host=url[hoststart:]
                    path='/'
                else:
                    host=url[hoststart:hostend]
                    path=url[hostend:]
                #print str(hoststart), str(hostend), host, path
            else:
                # assume DNS name
                host=url
                path='/'
            # figure IP addr from hostname
            try:
                answer = myResolver.query(host, "A") 
                for rdata in answer: 
                    #pick last one
                    addr=rdata
            except:
                wr_dummy(row,wr)
                print >>sys.stderr, sys.argv[0] + " DNS exception:" + str(e) + "host: " + host 
                # we're done with this host...
                continue
            #print "addr: " + str(addr)
            analysis['ip']=str(addr)
            analysis['host']=host
            # place to accumulate values for csv row
            csvals=[]
            # do HTTP, then HTTP and TLS with SNI, then HTTP and TLS without SNI
            for port in [ "80", "443", "443-with-sni" ]:
                analysis[port]={}
                # fill in what we can or a dummy value so csv col count is ok
                # even if we hit an exception
                analysis[port]['host']=host
                analysis[port]['ip']=str(addr)
                analysis[port]['status_code']=-1
                analysis[port]['body_len']=-1
                analysis[port]['names']=''
                analysis[port]['fp']=''
                analysis[port]['timely']=-1
                analysis[port]['self_signed']=-1
                analysis[port]['rsalen']=-1
                analysis[port]['cipher_suite']=-1
                analysis[port]['browser_trusted']=-1

                try:
                    reserr=False # set if we don't get an HTTP response
                    # cmd='zgrab '+  pparms[port] + " -http " + path + " " + ztimeout
                    # print "cmd: " + cmd
                    # proc=subprocess.Popen(cmd.split(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    # # 443 is different due to SNI, need to provide host, not address
                    # if port=='443-with-sni':
                    #     #print "doing: port: " + port + " |" + host + "| " + cmd
                    #     # man it took me a while to figure that "\n" below was needed;-(
                    #     pc=proc.communicate(input=host + "\n")
                    # else:
                    #     #print "doing: port: " + port + " |" + str(addr) + "| " + cmd
                    #     pc=proc.communicate(input=str(addr).encode())
                    # lines=pc[0].split('\n')
                    lines,pc,cmd=run_zgrab(pparms, port, path, ztimeout, host, addr)
                    #print "pc: " + str(pc)
                    jinfo=json.loads(lines[1])
                    jres=json.loads(lines[0])
                    if 'response' in jres['data']['http']:
                        body=jres['data']['http']['response']['body']
                        analysis[port]['status_code']=jres['data']['http']['response']['status_code']
                    elif 'error' in jres:
                        host = 'www.' + host
                        lines,pc,cmd=run_zgrab(pparms, port, path, ztimeout, host, addr)
                        jinfo=json.loads(lines[1])
                        jres=json.loads(lines[0])
                        if 'response' in jres['data']['http']:
                            body=jres['data']['http']['response']['body']
                            analysis[port]['status_code']=jres['data']['http']['response']['status_code']
                        else:
                            print >>sys.stderr, "Error1 doing " + str(addr) + ":"+ port + " " + cmd
                            body=jres['error']
                            analysis[port]['status_code']=999
                            reserr=True
                    else:
                        print >>sys.stderr, "Unknown error doing " + str(addr) + ":"+ port + " " + cmd
                        print >>sys.stderr, jres
                        print >>sys.stderr, jinfo
                        body="Unknown"
                        analysis[port]['status_code']=666
                        reserr=True
                    # put host in there, as it's not by default if we didn't use it
                    jres['host']=host
                    jres['ip']=str(addr)
                    # also put it into port specifics, as we'll flatten that in a 'mo
                    if port=='80':
                        # do any port 80 specifics
                        pass
                    elif reserr == False and (port=='443-with-sni' or port=='443'):
                        # do tls specifics
                        if 'response' in jres['data']['http']:
                            th=jres['data']['http']['response']['request']['tls_handshake']
                            fp=th['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256'] 
                            cert=th['server_certificates']['certificate']
                            analysis[port]['fp']=fp
                            #print jsonpickle.encode(th)
                            # get_tls is from the surveys repo
                            get_tls('FreshGrab.py',port,th,jres['ip'],analysis[port],scandate)
                            #print analysis[port]
                            names={}
                            get_certnames(port,cert,names)
                            # flatten out them there names
                            flatnames=""
                            for k in names:
                                flatnames += str(names[k])
                                flatnames += ";"
                            analysis[port]['names']=flatnames
                        elif 'error' in jres:
                            print >>sys.stderr, "Error2 doing " + str(addr) + ":"+ port + " " + cmd
                            body=jres['error']
                            print body
                            analysis[port]['status_code']=999
                        else:
                            body="Unknown"
                            analysis[port]['status_code']=666
                    analysis[port]['body_len']=len(body)
                except Exception as e:
                    print >>sys.stderr, sys.argv[0] + " exception: " + str(e) + "host: " + host + " port: " + port 
                    print "pc: " + str(pc)
                    #sys.exit(1)

                # accumulate columns for csv
                # basic info for all ports
                csvals.append(analysis[port]['status_code'])
                csvals.append(analysis[port]['body_len'])
                if port != "80":
                    # add TLS stuff
                    csvals.append(analysis[port]['names'])
                    csvals.append(analysis[port]['fp'])
                    csvals.append(analysis[port]['timely'])
                    csvals.append(analysis[port]['self_signed'])
                    csvals.append(analysis[port]['rsalen'])
                    csvals.append(analysis[port]['cipher_suite'])
                    csvals.append(analysis[port]['browser_trusted'])

            #print row
            #print "Analysis:" 
            #print jsonpickle.encode(analysis)
            #print row
            row += csvals
            wr.writerow(row)

        count += 1
        if count % 10 == 0:
            print >>sys.stderr, "Did " + str(count) + " last: " + url
            # debug exit
            # sys.exit(0)

of.close()