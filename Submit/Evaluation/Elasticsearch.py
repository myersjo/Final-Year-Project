#!/usr/bin/python

import time
import json
from elasticsearch import Elasticsearch # install via "$ sudo pip install elasticsearch"
es = Elasticsearch()

index="records-fresh-ie-20180316"

def searchIp(ip):
    query = "doc.ip: {}".format(ip)
    result = es.search(index = index,
        q=query,
        _source=False)
    # print(result)
    return result

def searchP443Fingerprint(fp):
    query = "doc.p443.data.http.response.request.tls_handshake.server_certificates.certificate.parsed.subject_key_info.fingerprint_sha256.keyword: {}".format(fp)
    result = es.search(index = index,
        q=query,
        _source=False)
    # print(result)
    return result

def searchP443FingerprintGroupByCipherSuite(fp):
    body={
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "doc.p443.data.http.response.request.tls_handshake.server_certificates.certificate.parsed.subject_key_info.fingerprint_sha256.keyword: {}".format(fp),
                            "analyze_wildcard": True,
                            "default_field": "*"
                        }
                    }
                ]
            }
        },
        "aggs": {
            "cipherSuite": {
                "terms": {
                    "field": "doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name.keyword",
                    "size": 100,
                    "order": {
                    "_count": "desc"
                    }
                }
            }
        }
    }
    result = es.search(index = index,
        body=body,
        _source=False)
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
        result = searchP443Fingerprint(fp)
        endTime=time.time()
        timeTaken=endTime-startTime
        print("    {}: {}s    {} matches found".format(i, timeTaken, result["hits"]["total"]))
        avgTime=((avgTime*i)+timeTaken)/(i+1)
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
        print("    {}: {}s    {} matches found".format(i, timeTaken, result["hits"]["total"]))
        cipherSuites=result["aggregations"]["cipherSuite"]["buckets"]
        for suite in cipherSuites:
            print("        {}: {}".format(suite["key"], suite["doc_count"]))
        avgTime=((avgTime*i)+timeTaken)/(i+1)
    print("  Avg time taken: {}s".format(avgTime))

def runTests():
    searchIpTest()
    searchP443FingerprintTest()
    searchP443FingerprintGroupByCipherSuiteTest()

runTests()