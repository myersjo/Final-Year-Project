sudo apt update
sudo apt -y upgrade

# Elastic Stack common set up

# Install Oracle Java
# Add package repo
sudo add-apt-repository ppa:webupd8team/java -y
# Install JDK
sudo apt install oracle-java8-installer -y
# Check version
java -V


# Import PGP Key
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
sudo apt update

# Install Elasticsearch
sudo apt install elasticsearch
# Enable auto-start on boot
sudo /bin/systemctl daemon-reload
sudo /bin/systemctl enable elasticsearch.service
sudo /bin/systemctl start elasticsearch.service
# Test ES
curl -X GET "localhost:9200/"

# Install Kibana
sudo apt install kibana
# Enable auto-start on boot
sudo /bin/systemctl daemon-reload
sudo /bin/systemctl enable kibana.service


# Set up defaults
curl -X PUT "localhost:9200/_template/default_template" -H 'Content-Type: application/json' -d @Elasticsearch/DefaultIndexTemplate.json
curl -X PUT "localhost:9200/_template/default_template" -H 'Content-Type: application/json' -d @Elasticsearch/RecordsFreshTemplate.json
curl -X PUT "localhost:9200/_template/fingerprint_template" -H 'Content-Type: application/json' -d @Elasticsearch/FingerprintTemplate.json