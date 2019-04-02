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