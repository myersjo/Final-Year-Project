esman installdeps --help

esman installdeps

esman extractsubset --help

esman extractsubset -c ../../Data/AviationCompanies_DNS.csv -j /home/stephen/data/smtp/runs/IE-20180316-181141/records.fresh -o test.json

nano test.json

es viewallindices --help

es viewallindices

es insert --help

es insert -i test.json -rd 2018-03-16 -cc IE

es viewallindices

es deleteindex --help

es deleteindex




GET av-records-fresh-geo-ie*/_search
{
  "query": {
    "match_phrase": {
      "doc.ip": "37.18.144.35"
    }
  },
  "_source": ["doc.company", "doc.ip", "doc.domain", "doc.run_date"],
  "sort": [
    {
      "doc.run_date": {
        "order": "desc"
      }
    }
  ]
}


GET av-records-fresh-geo-ie*,av-fingerprints-ie*/_search
{
  "query": {
    "match_phrase": {
      "doc.ip": "89.191.34.134"
    }
  },
  "_source": ["doc.ip", "doc.run_date", "doc.company", "doc.domain", "doc.fprint"],
  "sort": [
    {
      "doc.run_date": {
        "order": "desc"
      }
    }
  ]
}


GET records-fresh-ie-*/_search
{
  "query": { "match_all": {}},
  "aggs": {
    "groupby": {
      "terms": {
        "field": "doc.p443.data.http.redirect_response_chain.request.tls_handshake.server_certificates.certificate.parsed.subject_key_info.fingerprint_sha256.keyword",
        "size": 10
      }
    }
  },
  "_source": "false",
  "size": 5
}


GET records-fresh-ie-*/_search
{
  "query": { "match_all": {}},
  "aggs": {
    "groupby-fp": {
      "terms": {
        "field": "doc.p443.data.http.response.request.tls_handshake.server_certificates.certificate.parsed.subject_key_info.fingerprint_sha256.keyword",
        "size": 10
      },
      "aggs": {
        "groupby-date": {
          "date_histogram": {
            "field": "doc.run_date",
            "interval": "30d",
            "min_doc_count": 1
          }
        }
      }
    }
  },
  "_source": "false",
  "size": 5
}
