/_search/
curl -X PUT "localhost:9200/customer?pretty"
curl -X GET "localhost:9200/_cat/indices?v"

curl -X PUT "localhost:9200/customer/_doc/1?pretty" -H 'Content-Type: application/json' -d'
{
  "name": "John Doe"
}
'


curl -X PUT "localhost:9200/records-fresh/_doc/?pretty" -H 'Content-Type: application/json' -d

curl -X PUT "localhost:9200/records-fresh?pretty"
curl -X GET "localhost:9200/_cat/indices?v"

curl -X DELETE "localhost:9200/twitter?pretty"
curl -X GET "localhost:9200/_cat/indices?v"

curl -X PUT "localhost:9200/customer/_doc/1?pretty" -H 'Content-Type: application/json' -d'
{
  "name": "John Doe"
}
'

curl -X GET "localhost:9200/records-fresh/_search" -H 'Content-Type: application/json' -d'
{
  "query": { "match_all": {} }
}
'

curl -X GET "localhost:9200/records-fresh/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": { "multi_match": { "query": "cf2e357d638641ccb283cdd2c157a8c41b790ca751ec8f96970687684092a910", "fields": []} }, "_source": false
}
'

curl -X GET "localhost:9200/records-fresh/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": { "multi_match": { "query": "25f18e1873122f3ae6074a24dfcb039fd84fe71d265f3dc2ff3ed392be46ff0a", "fields": []} }, "_source": false
}
'

curl -X POST "localhost:9200/records-fresh/_doc?pretty" -H 'Content-Type: application/json' -d @

curl -X PUT "localhost:9200/records-fresh-v2.3/_settings" -H 'Content-Type: application/json' -d'
{
  "index.mapping.total_fields.limit": 5000
}
'

curl -X GET "localhost:9200/logstash-2019.02.14/_search" -H 'Content-Type: application/json' -d'
{
  "query": { "match_all": {} }, "_source": false
}
'

curl -X PUT "localhost:9200/av-records-fresh-noip-ie-20171130?pretty" -H 'Content-Type: application/json' -d'
{
    "settings" : {
        "index" : {
            "number_of_shards" : 1, 
            "mapping.total_fields.limit": 5000
        }
    }
}
'

curl -X GET "localhost:9200/_cat/thread_pool"
curl -X GET "localhost:9200/_cat/shards"
curl -X DELETE "localhost:9200/records-fresh-v2.3?pretty"

curl -X DELETE "localhost:9200/records-fresh-v1.1?pretty"
curl -X DELETE "localhost:9200/records-fresh-v1.3?pretty"
curl -X DELETE "localhost:9200/records-fresh-v1.4?pretty"
curl -X DELETE "localhost:9200/records-fresh-v2.1?pretty"
curl -X DELETE "localhost:9200/records-fresh-20190115?pretty"

#less records.fresh | json_pp | less
#less records.fresh | grep "82.141.246.117" | json_pp > /home/jordan/data/sample-records-c1-1.json

curl -X GET "localhost:9200/records-fresh-ie-20190115/_search?pretty&size=1" -H 'Content-Type: application/json' -d'
{
  "query": { "match_all": {} },
  "_source": ["p443.data.http.response.tls_handshake.server_certificates.validation.browser_trusted"]
}
'

curl -X GET "localhost:9200/records-fresh-ie-20190115/_search?pretty&size=5" -H 'Content-Type: application/json' -d'
{
  "query": { 
	"term": {
	  "doc.p443.data.http.response.request.tls_handshake.server_certificates.validation.browser_trusted": "true"
	} 
  },
  "_source": [ "doc.ip", "doc.p443.data.http.response.request.tls_handshake*" ]
}
'

curl -X GET "localhost:9200/records-fresh-ie-20190115/_search?pretty&size=5" -H 'Content-Type: application/json' -d'
{
  "query": { 
	"term": {
	  "doc.p443.data.http.response.request.tls_handshake.server_certificates.validation.browser_trusted": "true"
	} 
  },
  "_source": [ "doc.ip"]
}
'

curl -X GET "localhost:9200/records-fresh-ie-20180316/_search?pretty&size=5" -H 'Content-Type: application/json' -d'
{
  "query": { 
	"term": {
	  "doc.p443.data.http.response.request.tls_handshake.server_certificates.validation.browser_trusted": "true"
	} 
  },
  "_source": [ "doc.ip"]
}
'

curl -X GET "localhost:9200/records-fresh-ie-20171130/_search?pretty&size=5" -H 'Content-Type: application/json' -d'
{
  "query": { 
	"term": {
	  "doc.p443.https.tls.validation.browser_trusted": "true"
	} 
  },
  "_source": [ "doc.ip"]
}
'

curl -X POST "localhost:9200/_xpack/sql/translate?format=txt&pretty" -H 'Content-Type: application/json' -d'
{
    "query": "SELECT doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name as CipherSuite, COUNT(*) as Count FROM \"records-fresh-ie-2019*\" GROUP BY doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name"
}
'

# Get all matching indices (records-fresh-ie*) in ascending order
curl -X GET "localhost:9200/_cat/indices/records-fresh-ie*?v&h=index&s=index:desc&format=json&pretty"


curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
    "action.destructive_requires_name": "true"
}
'

curl -X DELETE "localhost:9200/.monitoring*"

