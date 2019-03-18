##Highlights/Features
###Code
- Bulk Insert: code to insert existing JSON data into Elasticsearch (ES), taking into account below recommended spec machine
- Summary Statistics: code to summarise data using graphs (Plotly)
- Extract data subset: code to read domain names line-by-line from CSV file, search for domain name in each line in JSON file and if match, copy JSON line to output file. If CSV file contains an IP (e.g. from AddDNSDetail.py), the IP can be used for search if there is no match for the domain. This can lead to mismatched records if the time between getting the IP for the domain and the running the scan is relatively large as IPs change
- Elasticsearch management cmds

### Elastic Stack
- Elasticsearch and Kibana running on machine with minimum spec (below recommended)
-- Index template to set number of shards to 1; removes replication, redundancy, reduces index search performance, reduces overhead of multiple shards
- Nginx with self-signed cert
- Filebeat to read records.fresh output in realtime (e.g. as it’s being written during scan), parse JSON and send to Logstash
- Logstash to process JSON, adding additional fields such as country code, run date and geoip data and send to ES

### Analysis
- IE Scan dashboard: 
-- Change in P443 Cipher Suite usage over multiple scans
-- Change in number of P443 Browser Trusted Certs over multiple scans
- AV Data dashboard:
-- Change in number of records by company (change in number of mail servers?)
-- Companies per ip - if two companies are shown for the same IP with different run dates, the IP has been reused. If the run dates are the same, there was either an error with the search (e.g. link from one company site to the other) or both companies are being served from the same host (shared hosting)
-- Count of P443 Sha256 Fingerprint use by run - if the count is greater than one, multiple hosts are using the same sha256 crypto key for p443
-- Companies per P443 Sha256 Fingerprint - shows each fingerprint and the companies who use it
-- Change in P443 Cipher Suite usage by run
-- Count ASN name by run - would show the change in AS over time; only included in censys.io data (2017). 

### Technical Challenges/Difficulties Encountered:
- Elasticsearch crash on bulk insert
-- Problem: ES would crash when attempting to bulk insert data
-- Fixes attempted: 
--- Tried own code and Filebeat/Logstash
--- Own code: used timers (sleep) to reduce request rate, reduced chunk size, used generators to reduce memory usage of python script, added check to ensure ES was running and restart and wait if not
-- Final solution/fix: 
--- reduce the number of shards per ES index and keep indices to a minimum. 
--- Have max 20 shards per 1GB heap (1 shard per index = 20 indices, including system indices)
--- Set heap size to be 50% of total RAM available (1GB heap with 2GB RAM); remaining RAM used by lucene and other processes
-- Cause:
--- By default, ES creates 5 primary shards (each with 1 replica shard) per index, giving 10 shards per index
--- Each shard corresponds to a lucene index
--- Each document (record) is inserted into 1 primary shard and its replica
--- Data about every shard is stored in memory during runtime; more shards = more overhead
--- Swap significantly degrades performance
--- Machine only has 2GB of RAM, 6 GB swap
--- With 1GB heap, overhead resulted in little memory for handling incoming bulk insert request
--- ES initially attempted to queue requests and process them at reduced rate. Eventually it would refuse incoming HTTP requests, resulting in HTTP request timeouts on other end (followed by retry attempts if configured). Garbage collector would attempt to free up memory, but was active significantly more than ES code. Eventually, ES would crash
-- Contributing factors: 
--- Machine significantly smaller than average for ES (up to 64GB vs 2GB)
--- ES usually used with large amount of short, single-line logs; we have a relatively small number (25,000-30,000) of significantly larger logs (some up to 3,500 JSON fields)
-- Kibana ‘Request Entity Too Large’
--- Error when loading index pattern covering multiple runs and large number of fields
--- HTTP Request included JSON payload with names and metadata about each field in the index pattern (4,000 fields, 5 metadata fields)
--- Fixed by adding client_max_body_size to nginx config and setting it to 20M


## Notes
- Scans only include data from hosts in a specific country which listen on port 25 (mail servers). Data on other ports (e.g. P443) are included when the same host is used for multiple services (e.g. mail and web server), i.e. is not a dedicated mail server
