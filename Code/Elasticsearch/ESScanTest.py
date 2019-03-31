import json
from elasticsearch import Elasticsearch # install via "$ sudo pip install elasticsearch"
from elasticsearch.helpers import scan

es = Elasticsearch()

index = "av-records-fresh-geo-ie-20180316"

records = scan(es,
        query={"query": {"match_all": {}}},
        index=index,
        scroll="5m",
        size="5")

for record in records:
    # print record
    j_content = record["_source"]["doc"]
    print(j_content["ip"])