import httplib as httpclient
import json
import dateparser as dp
import plotly

from datetime import datetime
from elasticsearch import Elasticsearch
es = Elasticsearch()

# res = es.search(index="records-fresh-ie-*", body={"query": "SELECT doc.run_date as RunDate, COUNT(*) as Count FROM \"records-fresh-ie-*\" GROUP BY doc.run_date"})

connection = httpclient.HTTPConnection('localhost:9200')

headers = {'Content-type': 'application/json'}

body = {"query": "SELECT doc.run_date as RunDate, COUNT(*) as Count FROM \"records-fresh-ie-*\" GROUP BY doc.run_date"}
json_body = json.dumps(body)

connection.request('POST', '/_xpack/sql', json_body, headers)

response = connection.getresponse()
respBody = response.read()
print(respBody.decode())

respJson = json.loads(respBody)
print(respJson["rows"][0])

data = {}
for run in respJson["rows"]:
    date = dp.parse(run[0])
    print("Run Date: {} Count: {}".format(date.strftime('%Y-%m-%d'), run[1]))
    data["OverallCount"][""]

