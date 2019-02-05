curl -X GET "localhost:9200/_cat/health?v"
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

curl -X PUT "localhost:9200/records-fresh/_settings" -H 'Content-Type: application/json' -d'
{
  "index.mapping.total_fields.limit": 3000
}
'

#less records.fresh | json_pp | less
#less records.fresh | grep "82.141.246.117" | json_pp > /home/jordan/data/sample-records-c1-1.json
