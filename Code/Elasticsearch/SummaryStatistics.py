import httplib as httpclient
import json
import dateparser as dp
import plotly
import requests
import plotly.plotly as py
import plotly.graph_objs as go

from datetime import datetime

# Constants
GET="GET"
POST="POST"

# Default values
host="http://localhost:9200"
idxNameBase="records-fresh-"
countryCode="ie"

# Send specified HTTP request and return JSON result
def sendHttpRequest(httpVerb, request, body=None):
    url = host + request
    headers = {'Content-type': 'application/json'}
    json_body = json.dumps(body)
    response=None
    if httpVerb == GET:
        response = requests.get(url, headers=headers)
    elif httpVerb == POST:
        response = requests.post(url, data = json_body, headers=headers)

    return response.json()

# Returns a list of all indices (runs) which match the given base and country code
#  e.g. 'records-fresh-ie*', where 'records-fresh-' is the base and 'ie' is the country code
def getAllMatchingRuns(idxNameBase, countryCode):
    print("\nRuns matching {}{}{}: ".format(idxNameBase, countryCode, "*"))
    request = "/_cat/indices/" + idxNameBase + countryCode + "*?v&h=index&s=index:desc&format=json"

    response = sendHttpRequest(GET, request)
    # print(response)

    runs = []
    for run in response:
        print(run["index"])
        runs.append(run["index"])

    return runs

# Gets total count of records per run and returns object with arrays for graphing
def getTotalRecordsByRun(idxNameBase, countryCode):
    print("\nTotal Records By Run: ")
    body = {"query": "SELECT doc.run_date as RunDate, COUNT(*) as Count FROM \"" + idxNameBase + countryCode + "*\" GROUP BY doc.run_date"}
    request = "/_xpack/sql"

    response = sendHttpRequest(POST, request, body)
    # print(response)

    data = { "run_dates": [], "counts": []}
    for run in response["rows"]:
        date = dp.parse(run[0])
        print("Run Date: {} Count: {}".format(date.strftime('%Y-%m-%d'), run[1]))
        data["run_dates"].append(date.strftime('%Y-%m-%d'))
        data["counts"].append(run[1])
    
    return data

# Gets count of records per run that have browser trusted certificates for P443 and returns object with arrays for graphing
def getCountP443BrowserTrustedCerts(idxNameBase, countryCode):
    print("\nCount Browser Trusted Certs: ")
    body = {"query": "SELECT doc.run_date as RunDate, COUNT(*) as CountBrowserTrusted FROM \"" + idxNameBase + countryCode + "*\" WHERE doc.p443.data.http.response.request.tls_handshake.server_certificates.validation.browser_trusted=true GROUP BY doc.run_date"}
    request = "/_xpack/sql"

    response = sendHttpRequest(POST, request, body)
    # print(response)

    data = { "run_dates": [], "counts": []}
    for run in response["rows"]:
        date = dp.parse(run[0])
        print("Run Date: {} Count: {}".format(date.strftime('%Y-%m-%d'), run[1]))
        data["run_dates"].append(date.strftime('%Y-%m-%d'))
        data["counts"].append(run[1])
    
    return data

def drawCountLineChart(idxNameBase, countryCode):
    print("\nDraw Count Line Chart: ")
    data = {}
    data["totalRecords"] = getTotalRecordsByRun(idxNameBase, countryCode)
    data["p443BrowserTrustedCerts"] = getCountP443BrowserTrustedCerts(idxNameBase, countryCode)
    # print(data)
    
    totalRecords = go.Scatter(
        x = data["totalRecords"]["run_dates"],
        y = data["totalRecords"]["counts"],
        name = 'Total Records by Run',
        line = dict(
            color = ('rgb(205, 12, 24)'),
            width = 4)
    )
    p443BrowserTrustedCerts = go.Scatter(
        x = data["p443BrowserTrustedCerts"]["run_dates"],
        y = data["p443BrowserTrustedCerts"]["counts"],
        name = 'Total Records With P443 Browser Trusted Certs by Run',
        line = dict(
            color = ('rgb(0, 153, 255)'),
            width = 4)
    )

    lines = [totalRecords, p443BrowserTrustedCerts]
    layout = dict(title = 'Data',
              xaxis = dict(title = 'Run Date'),
              yaxis = dict(title = 'Count'),
              )

    fig = dict(data=lines, layout=layout)
    py.plot(fig, filename='count-line-chart', auto_open=False)

def getCountP443CipherSuiteUsedForRun(run):
    print("\nCount P443 Cipher Suite Used for run {}:".format(run))
    body = {"query": "SELECT doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name as CipherSuite, COUNT(*) as Count FROM \"" + run +"*\" GROUP BY doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name"}
    request = "/_xpack/sql"

    response = sendHttpRequest(POST, request, body)

    data = { "cipherSuites": [], "counts": []}
    if 'rows' in response:
        for cipherSuite in response["rows"]:
            # print("Suite: {} Count: {}".format(cipherSuite[0], cipherSuite[1]))
            data["cipherSuites"].append(cipherSuite[0])
            data["counts"].append(cipherSuite[1])

    return data

def drawCountP443CipherSuiteUsedBarChart(idxNameBase, countryCode):
    print("\nDraw Count P443 Cipher Suite Used by Run:")
    runs = getAllMatchingRuns(idxNameBase, countryCode)

    data = []
    for run in runs:
        res = getCountP443CipherSuiteUsedForRun(run)
        # print(res)
        trace = go.Bar(
            x=res["cipherSuites"],
            y=res["counts"],
            name=run
        )
        data.append(trace)

    layout = go.Layout(
        barmode='group'
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='p443-count-cipher-suites', auto_open=False)

getAllMatchingRuns(idxNameBase, countryCode)
drawCountLineChart(idxNameBase, countryCode)
drawCountP443CipherSuiteUsedBarChart(idxNameBase, countryCode)