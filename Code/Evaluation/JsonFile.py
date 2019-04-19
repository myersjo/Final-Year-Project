#!/usr/bin/python

import time
import json
import gc

infile="/home/stephen/data/smtp/runs/IE-20180316-181141/records.fresh"

def searchIp(ip):
    with open(infile,'r') as f:
        for line in f:
            j_content = json.loads(line)
            if (j_content['ip']==ip):
                return j_content
    
    # print(result)
    return result

def searchP443Fingerprint(fp):
    result=[]
    with open(infile,'r') as f:
        for line in f:
            j_content = json.loads(line)
            fprint=""
            try:
                fprint=j_content['p443']['data']['http']['response']['request']['tls_handshake']['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256']
            except:
                pass
            if (fprint and fprint==fp):
                result.append(j_content)
    
    # print(result)
    return result

def searchP443FingerprintGroupByCipherSuite(fp):
    result={}
    with open(infile,'r') as f:
        for line in f:
            j_content = json.loads(line)
            fprint=""
            try:
                fprint=j_content['p443']['data']['http']['response']['request']['tls_handshake']['server_certificates']['certificate']['parsed']['subject_key_info']['fingerprint_sha256']
            except:
                pass
            if (fprint and fprint==fp):
                cipherSuite=j_content['p443']['data']['http']['response']['request']['tls_handshake']['server_hello']['cipher_suite']['name']
                if not cipherSuite in result:
                    result[cipherSuite]=[]
                result[cipherSuite].append(j_content)
    
    # print(result)
    return result


def searchIpTest():
    print("Search IP Test:")
    avgTime = 0
    ip = "34.240.5.183"
    for i in range(5):
        startTime=time.time()
        searchIp(ip)
        endTime=time.time()
        timeTaken=endTime-startTime
        print("    {}: {}s".format(i, timeTaken))
        avgTime=((avgTime*i)+timeTaken)/(i+1)
    print("  Avg time taken: {}s".format(avgTime))

def searchP443FingerprintTest():
    print("Search P443 Fingerprint Test:")
    avgTime = 0
    fp = "9f0050378fa2a1389b35cf74e0f1063ad42eaebc5a324b10c6aacf3ab08f7a94"
    for i in range(5):
        startTime=time.time()
        result=searchP443Fingerprint(fp)
        endTime=time.time()
        timeTaken=endTime-startTime
        print("    {}: {}s    {} matches found".format(i, timeTaken, len(result)))
        avgTime=((avgTime*i)+timeTaken)/(i+1)
        gc.collect()
    print("  Avg time taken: {}s".format(avgTime))

def searchP443FingerprintGroupByCipherSuiteTest():
    print("Search P443 Fingerprint, Group By Cipher Suite Test:")
    avgTime = 0
    fp = "9f0050378fa2a1389b35cf74e0f1063ad42eaebc5a324b10c6aacf3ab08f7a94"
    for i in range(5):
        startTime=time.time()
        result = searchP443FingerprintGroupByCipherSuite(fp)
        endTime=time.time()
        timeTaken=endTime-startTime
        matches = 0
        for suite in result:
            matches += len(result[suite])
        print("    {}: {}s    {} matches found".format(i, timeTaken, matches))
        for suite in result:
            print("        {}: {}".format(suite, len(result[suite])))
        avgTime=((avgTime*i)+timeTaken)/(i+1)
    print("  Avg time taken: {}s".format(avgTime))

def runTests():
    # searchIpTest()
    # searchP443FingerprintTest()
    searchP443FingerprintGroupByCipherSuiteTest()

runTests()