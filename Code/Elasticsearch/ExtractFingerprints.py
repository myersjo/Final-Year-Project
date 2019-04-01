#!/usr/bin/python

# Elasticsearch version of SameKeys.py
# from https://github.com/sftcd/surveys

import os, sys, argparse, tempfile, gc
import json
import jsonpickle # install via  "$ sudo pip install -U jsonpickle"
import time, datetime
from dateutil import parser as dparser  # for parsing time from comand line and certs
import pytz # for adding back TZ info to allow comparisons

from elasticsearch import Elasticsearch # install via "$ sudo pip install elasticsearch"
from elasticsearch.helpers import scan, bulk
es = Elasticsearch(timeout=60)


# from https://github.com/sftcd/surveys ...
# locally in $HOME/code/surveys
def_surveydir=os.environ['HOME']+'/code/surveys'
sys.path.insert(0,def_surveydir)
from SurveyFuncs import *  

# default values
index="av-records-fresh-geo-ie-20180316"
fp_index="av-fingerprints-20180316"
UPDATE_ELASTICSEARCH=True # Used for testing - if False, data is retrieved from ES, but no inserts/updates are sent

def timestampPrint(message):
    print('[{}] {} '.format(datetime.datetime.now(), message))

def newFprintRec():
    fprec={}
    fprec['ip'] = ""
    fprec['fprint'] = ""
    fprec['run_date'] = ""
    fprec['p22'] = 0
    fprec['p25'] = 0
    fprec['p110'] = 0
    fprec['p143'] = 0
    fprec['p443'] = 0
    fprec['p587'] = 0
    fprec['p993'] = 0
    return fprec

def toESDocs(fprecs, index):
    docs=[]
    for fp in fprecs:
        doc={}
        doc['_index']=index
        doc['_type']="document"
        doc['doc']=fprecs[fp]
        docs.append(doc)
    return docs

# command line arg handling 
argparser=argparse.ArgumentParser(description='Scan records for collisions')
argparser.add_argument('-i','--input',     
                    dest='index',
                    help='Elasticsearch index containing list of IPs')
argparser.add_argument('--fpindex',     
                    dest='fp_index',
                    help='Elasticsearch fingerprint index')
argparser.add_argument('-p','--ports',     
                    dest='portstring',
                    help='comma-sep list of ports to scan')
argparser.add_argument('-s','--scandate',     
                    dest='scandatestring',
                    help='time at which to evaluate certificate validity')
argparser.add_argument('-c','--country',     
                    dest='country',
                    help='country in which we\'re interested, use XX if you don\'t care, default is IE')
argparser.add_argument('-f','--fps',     
                    dest='fpfile',
                    help='pre-existing fingerprints file')
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
if args.country is not None:
    country=args.country
    print >>sys.stderr, "Doing a " + country + "run"

if args.index is not None:
    index=args.index

if args.fp_index is not None:
    fp_index=args.fp_index

# this is an array to hold the set of keys we find
fingerprints=[]
overallcount=0
badcount=0
goodcount=0

# encoder options
jsonpickle.set_encoder_options('json', sort_keys=True, indent=2)
jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=2)

# it can happen that we run out of memory after we've done all of the
# dns stuff, in such a case, it's nice to be able to re-start from the
# fingerprints.json file to save the time of re-doing all those dns
# queries, this branch does that
if args.fpfile is not None:
    pass
# TODO: Update
    # # read fingerprints from fpfile
    # fpf=open(args.fpfile,"r")
    # f=getnextfprint(fpf)
    # print f
    # fpcount=0
    # while f:
    #     fingerprints.append(f)
    #     fpcount+=1
    #     if fpcount % 100 == 0:
    #         print >>sys.stderr, "Read " + str(fpcount) + " fingerprints from " + args.fpfile
    #     f=getnextfprint(fpf)
    # fpf.close()
else:
    bads={}
    # keep track of how long this is taking per ip
    peripaverage=0

    if UPDATE_ELASTICSEARCH:
        # Disable refresh to stop reindexing until complete
        es.indices.put_settings(index=index,
            body={ "index.refresh_interval": -1 })
        timestampPrint("Disabling ES refresh")

    # Generator to get records from ES, 'size' at a time
    records = scan(es,
        query={"query": {"match_all": {}}},
        index=index,
        scroll="2m",
        size="10")
    
    # with open(infile,'r') as f:
    for record in records:
        ipstart=time.time()
        badrec=False
        j_content = record["_source"]["doc"]
        somekey=False
        thisone=OneFP()
        thisone.ip_record=overallcount
        thisone.ip=j_content['ip'].strip()
        if 'writer' in j_content:
            thisone.writer=j_content['writer']

        try:
            if thisone.writer=="FreshGrab.py":
                asn=j_content['asn']
                asndec=int(j_content['asndec'])
                thisone.asn=asn
                thisone.asndec=asndec
                # print "Ip: {}  ASN: {}".format(thisone.ip, asn)
                if country != 'XX' and j_content['country_code'] != country:
                    badrec=True
                    print >>sys.stderr, "Bad country for ip",thisone.ip,"location:",j_content['location']['country_code'],"Asked for CC:",country
                    j_content['wrong_country']=j_content['location']['country_code'] 
            else:
                asn=j_content['autonomous_system']['name'].lower()
                asndec=int(j_content['autonomous_system']['asn'])
                thisone.asn=asn
                thisone.asndec=asndec
                if country != 'XX' and j_content['location']['country_code'] != country:
                    badrec=True
                    print >>sys.stderr, "Bad country for ip",thisone.ip,"location:",j_content['location']['country_code'],"Asked for CC:",country
                    j_content['wrong_country']=j_content['location']['country_code'] 
        except:
            # look that chap up ourselves
            mm_inited=False
            if not mm_inited:
                mm_setup()
                mm_inited=True
            asninfo=mm_info(thisone.ip)
            #print "fixing up asn info",asninfo
            thisone.asn=asninfo['asn']
            thisone.asndec=asninfo['asndec']
            if country != 'XX' and asninfo['cc'] != country:
                # just record as baddy if the country-code is (now) wrong?
                # mark it so we can revisit later too
                print >>sys.stderr, "Bad country for ip",thisone.ip,"asn:",asninfo['cc'],"Asked for CC:",country
                j_content['wrong_country']=asninfo['cc']
                badrec=True

        for pstr in portstrings:
            thisone.analysis[pstr]={}

        thisone.analysis['nameset']={}
        nameset=thisone.analysis['nameset']
        try:
            # name from reverse DNS
            rdnsrec=socket.gethostbyaddr(thisone.ip)
            rdns=rdnsrec[0]
            #print "FQDN reverse: " + str(rdns)
            nameset['rdns']=rdns
        except Exception as e: 
            #print >> sys.stderr, "FQDN reverse exception " + str(e) + " for record:" + thisone.ip
            #nameset['rdns']=''
            pass

        # name from banner
        try:
            p25=j_content['p25']
            if thisone.writer=="FreshGrab.py":
                #print p25['data']['banner']
                banner=p25['data']['banner'] 
            else:
                banner=p25['smtp']['starttls']['banner'] 
            ts=banner.split()
            if ts[0]=="220":
                banner_fqdn=ts[1]
                nameset['banner']=banner_fqdn
            elif ts[0].startswith("220-"):
                banner_fqdn=ts[0][4:]
                nameset['banner']=banner_fqdn
        except Exception as e: 
            #print >> sys.stderr, "FQDN banner exception " + str(e) + " for record:" + str(overallcount) + " ip:" + thisone.ip
            nameset['banner']=''

        try:
            if thisone.writer=="FreshGrab.py":
                fp=j_content['p22']['data']['xssh']['key_exchange']['server_host_key']['fingerprint_sha256'] 
                shk=j_content['p22']['data']['xssh']['key_exchange']['server_host_key']
                if shk['algorithm']=='ssh-rsa':
                    thisone.analysis['p22']['rsalen']=shk['rsa_public_key']['length']
                else:
                    thisone.analysis['p22']['alg']=shk['algorithm']
            else:
                fp=j_content['p22']['ssh']['v2']['server_host_key']['fingerprint_sha256'] 
                shk=j_content['p22']['ssh']['v2']['server_host_key']
                if shk['key_algorithm']=='ssh-rsa':
                    thisone.analysis['p22']['rsalen']=shk['rsa_public_key']['length']
                else:
                    thisone.analysis['p22']['alg']=shk['key_algorithm']
            fprint = { "port": 22, "fprint": fp }
            thisone.fprints.append(fprint)
            somekey=True
        except Exception as e: 
            #print >> sys.stderr, "p22 exception " + str(e) + " ip:" + thisone.ip
            pass

        try:
            if thisone.writer=="FreshGrab.py":
                tls=j_content['p25']['data']['tls']
                cert=tls['server_certificates']['certificate']
            else:
                tls=j_content['p25']['smtp']['starttls']['tls']
                cert=tls['certificate']
            fp=cert['parsed']['subject_key_info']['fingerprint_sha256'] 
            get_tls(thisone.writer,'p25',tls,j_content['ip'],thisone.analysis['p25'],scandate)
            get_certnames('p25',cert,nameset)
            fprint = { "port": 25, "fprint": fp }
            thisone.fprints.append(fprint)
            somekey=True
        except Exception as e: 
            #print >> sys.stderr, "p25 exception for:" + thisone.ip + ":" + str(e)
            pass

        try:
            if thisone.writer=="FreshGrab.py":
                cert=j_content['p110']['data']['tls']['server_certificates']['certificate']
                fp=j_content['p110']['data']['tls']['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256'] 
                get_tls(thisone.writer,'p25',j_content['p110']['data']['tls'],j_content['ip'],thisone.analysis['p110'],scandate)
            else:
                fp=j_content['p110']['pop3']['starttls']['tls']['certificate']['parsed']['subject_key_info']['fingerprint_sha256'] 
                cert=j_content['p110']['pop3']['starttls']['tls']['certificate']
                get_tls(thisone.writer,'p25',j_content['p110']['pop3']['starttls']['tls'],j_content['ip'],thisone.analysis['p110'],scandate)
            get_certnames('p110',cert,nameset)
            fprint = { "port": 110, "fprint": fp }
            thisone.fprints.append(fprint)
            somekey=True
        except Exception as e: 
            #print >> sys.stderr, "p110 exception for:" + thisone.ip + ":" + str(e)
            pass

        try:
            if thisone.writer=="FreshGrab.py":
                cert=j_content['p143']['data']['tls']['server_certificates']['certificate']
                fp=j_content['p143']['data']['tls']['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256'] 
                get_tls(thisone.writer,'p143',j_content['p143']['data']['tls'],j_content['ip'],thisone.analysis['p143'],scandate)
            else:
                cert=j_content['p143']['pop3']['starttls']['tls']['certificate']
                fp=j_content['p143']['imap']['starttls']['tls']['certificate']['parsed']['subject_key_info']['fingerprint_sha256']
                get_tls(thisone.writer,'p143',j_content['p143']['imap']['starttls']['tls'],j_content['ip'],thisone.analysis['p143'],scandate)
            get_certnames('p143',cert,nameset)
            fprint = { "port": 143, "fprint": fp }
            thisone.fprints.append(fprint)
            somekey=True
        except Exception as e: 
            #print >> sys.stderr, "p143 exception for:" + thisone.ip + ":" + str(e)
            pass

        try:
            if thisone.writer=="FreshGrab.py":
                fp=j_content['p443']['data']['http']['response']['request']['tls_handshake']['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256'] 
                cert=j_content['p443']['data']['http']['response']['request']['tls_handshake']['server_certificates']['certificate']
                get_tls(thisone.writer,'p443',j_content['p443']['data']['http']['response']['request']['tls_handshake'],j_content['ip'],thisone.analysis['p443'],scandate)
            else:
                fp=j_content['p443']['https']['tls']['certificate']['parsed']['subject_key_info']['fingerprint_sha256']
                cert=j_content['p443']['https']['tls']['certificate']
                get_tls(thisone.writer,'p443',j_content['p443']['https']['tls'],j_content['ip'],thisone.analysis['p443'],scandate)
            get_certnames('p443',cert,nameset)
            fprint = { "port": 443, "fprint": fp }
            thisone.fprints.append(fprint)
            somekey=True
        except Exception as e: 
            #print >> sys.stderr, "p443 exception for:" + thisone.ip + ":" + str(e)
            pass

        try:
            if thisone.writer=="FreshGrab.py":
                fp=j_content['p587']['data']['tls']['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256'] 
                cert=j_content['p587']['data']['tls']['server_certificates']['certificate']
                get_tls(thisone.writer,'p587',j_content['p587']['data']['tls'],j_content['ip'],thisone.analysis['p587'],scandate)
                somekey=True
                get_certnames('p587',cert,nameset)
                fprint = { "port": 587, "fprint": fp }
                thisone.fprints.append(fprint)
            else:
                # censys.io has no p587 for now
                pass
        except Exception as e: 
            #print >> sys.stderr, "p587 exception for:" + thisone.ip + ":" + str(e)
            pass

        try:
            if thisone.writer=="FreshGrab.py":
                fp=j_content['p993']['data']['tls']['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256'] 
                cert=j_content['p993']['data']['tls']['server_certificates']['certificate']
                get_tls(thisone.writer,'p993',j_content['p993']['data']['tls'],j_content['ip'],thisone.analysis['p993'],scandate)
            else:
                fp=j_content['p993']['imaps']['tls']['tls']['certificate']['parsed']['subject_key_info']['fingerprint_sha256']
                cert=j_content['p993']['imaps']['tls']['tls']['certificate']['parsed']
                get_tls(thisone.writer,'p993',j_content['p993']['imaps']['tls']['tls'],j_content['ip'],thisone.analysis['p993'],scandate)
            get_certnames('p993',cert,nameset)
            fprint = { "port": 993, "fprint": fp }
            thisone.fprints.append(fprint)
            somekey=True
        except Exception as e: 
            #print >> sys.stderr, "p993 exception for:" + thisone.ip + ":" + str(e)
            pass

        besty=[]
        nogood=True # assume none are good
        tmp={}
        # try verify names a bit
        for k in nameset:
            v=nameset[k]
            #print "checking: " + k + " " + v
            # see if we can verify the value as matching our give IP
            if v != '' and not fqdn_bogon(v):
                try:
                    rip=socket.gethostbyname(v)
                    if rip == thisone.ip:
                        besty.append(k)
                    else:
                        tmp[k+'-ip']=rip
                    # some name has an IP, even if not what we expect
                    nogood=False
                except Exception as e: 
                    #oddly, an NXDOMAIN seems to cause an exception, so these happen
                    #print >> sys.stderr, "Error making DNS query for " + v + " for ip:" + thisone.ip + " " + str(e)
                    pass
        for k in tmp:
            nameset[k]=tmp[k]
        nameset['allbad']=nogood
        nameset['besty']=besty

        if not badrec and somekey:
            goodcount += 1
            # fingerprints.append(thisone)
            # Add as nested doc
            docid = record['_id']
            docindex = record['_index']
            data = { "doc": { "fingerprints": thisone } }
            encodedData = jsonpickle.encode(data)
            # print(encodedData)
            # Update doc in ES with fprint data but don't reindex until next refresh
            # printOneFP(thisone)
            try:
                # pass
                # seenfps=[]
                # fprecs=[]
                # for fprint in thisone.fprints:
                #     if fprint['fprint'] in seenfps:
                #         i = seenfps.index(fprint['fprint'])
                #         port = fprint['port']
                #         fprecs[i][port] = 1
                #     else:
                #         fprec = newFprintRec()
                #         fprecs.append
                fprecs={}
                for fprint in thisone.fprints:
                    fp = fprint['fprint']
                    port = "p{}".format(fprint['port'])
                    if fp not in fprecs:
                        fprec = newFprintRec()
                        fprec['run_date']=args.scandatestring
                        fprec['fprint']=fp
                        fprec['ip']=thisone.ip
                        fprecs[fp] = fprec
                    fprecs[fp][port] = 1

                # for fp in fprecs:
                #     print(fprecs[fp])

                docs = toESDocs(fprecs, fp_index)

                # for doc in docs:
                #     print(doc)

                if UPDATE_ELASTICSEARCH:
                    es.update(index=docindex,
                        doc_type="document",
                        id=docid,
                        body=encodedData,
                        _source=False,
                        refresh="false")
                    
                    bulk(es, docs)

            except Exception as e:
                timestampPrint("ERROR: {}".format(e))
        else:
            bads[badcount]=j_content
            badcount += 1
        overallcount += 1

        # update average
        ipend=time.time()
        thistime=ipend-ipstart
        peripaverage=((overallcount*peripaverage)+thistime)/(overallcount+1)
        if overallcount % 5 == 0:
            print >> sys.stderr, "Reading fingerprints and rdns, did: " + str(overallcount) + \
                    " most recent ip " + thisone.ip + \
                    " average time/ip: " + str(peripaverage) \
                    + " last time: " + str(thistime)
        del j_content
        del thisone
    
    if UPDATE_ELASTICSEARCH:
        # Enable refresh again 
        es.indices.put_settings(index=index,
            body={ "index.refresh_interval": "60s" })
        timestampPrint("Enabling ES refresh")

    gc.collect()
    
    # # this gets crapped on each time (for now)
    # keyf=open('fingerprints.json', 'w')
    # bstr=jsonpickle.encode(fingerprints)
    # #bstr=jsonpickle.encode(fingerprints,unpicklable=False)
    # keyf.write(bstr)
    # del bstr
    # keyf.write("\n")
    # keyf.close()
    
    # this gets crapped on each time (for now)
    # in this case, these are the hosts with no crypto anywhere (except
    # maybe on p22)
    badf=open('dodgy.json', 'w')
    bstr=jsonpickle.encode(bads,unpicklable=False)
    badf.write(bstr + '\n')
    del bstr
    badf.close()
    del bads