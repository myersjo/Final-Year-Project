# Count of records per run
curl -X POST "localhost:9200/_xpack/sql?format=txt&pretty" -H 'Content-Type: application/json' -d'
{
    "query": "SELECT doc.run_date as RunDate, COUNT(*) as Count FROM \"records-fresh-ie-*\" GROUP BY doc.run_date"
}
'

curl -X POST "localhost:9200/records-fresh-ie-*/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "size" : 0,
  "_source" : false,
  "stored_fields" : "_none_",
  "aggregations" : {
    "groupby" : {
      "composite" : {
        "size" : 1000,
        "sources" : [
          {
            "166669" : {
              "terms" : {
                "field" : "doc.run_date",
                "missing_bucket" : true,
                "order" : "asc"
              }
            }
          }
        ]
      }
    }
  }
}
'

# Count of records with browser trusted certificates
curl -X POST "localhost:9200/_xpack/sql?format=txt&pretty" -H 'Content-Type: application/json' -d'
{
    "query": "SELECT doc.run_date as RunDate, COUNT(*) as CountBrowserTrusted FROM \"records-fresh-ie-*\" WHERE doc.p443.data.http.response.request.tls_handshake.server_certificates.validation.browser_trusted=true GROUP BY doc.run_date"
}
'
# Count of P443 cipher suite for specific run
curl -X POST "localhost:9200/_xpack/sql?format=txt&pretty" -H 'Content-Type: application/json' -d'
{
    "query": "SELECT doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name as CipherSuite, COUNT(*) as Count FROM \"records-fresh-ie-2019*\" GROUP BY doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name"
}
'

curl -X POST "localhost:9200/_xpack/sql?format=txt&pretty" -H 'Content-Type: application/json' -d'
{
    "query": "SELECT doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name as CipherSuite, COUNT(*) as Count FROM \"records-fresh-ie-2018*\" GROUP BY doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name"
}
'

curl -X POST "localhost:9200/_xpack/sql?format=txt&pretty" -H 'Content-Type: application/json' -d'
{
    "query": "SELECT doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name as CipherSuite, COUNT(*) as Count FROM \"records-fresh-ie-2017*\" GROUP BY doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name"
}
'