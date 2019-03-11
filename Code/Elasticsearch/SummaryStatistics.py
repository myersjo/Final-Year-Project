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

# connection = httpclient.HTTPConnection('localhost:9200')

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
    
    line1 = go.Scatter(
        x = data["run_dates"],
        y = data["counts"],
        name = 'Total Records by Run',
        line = dict(
            color = ('rgb(205, 12, 24)'),
            width = 4)
    )

    lines = [line1]
    layout = dict(title = 'Data',
              xaxis = dict(title = 'Run Date'),
              yaxis = dict(title = 'Count'),
              )

    fig = dict(data=lines, layout=layout)
    py.plot(fig, filename='total-records', auto_open=False)


def getAllMatchingRuns(idxNameBase, countryCode):
    print("\nRuns matching {}{}{}: ".format(idxNameBase, countryCode, "*"))
    request = "/_cat/indices/" + idxNameBase + countryCode + "*?v&h=index&s=index:desc&format=json"

    response = sendHttpRequest(GET, request)
    # print(response)

    for run in response:
        print(run["index"])

def getCountBrowserTrustedCerts(idxNameBase, countryCode):
    print("\nCount Browser Trusted Certs: ")
    body = {"query": "SELECT doc.run_date as RunDate, COUNT(*) as CountBrowserTrusted FROM \"" + idxNameBase + countryCode + "*\" WHERE doc.p443.data.http.response.request.tls_handshake.server_certificates.validation.browser_trusted=true GROUP BY doc.run_date"}
    request = "/_xpack/sql"

    response = sendHttpRequest(POST, request, body)
    print(response)

    data = { "run_dates": [], "counts": []}
    for run in response["rows"]:
        date = dp.parse(run[0])
        print("Run Date: {} Count: {}".format(date.strftime('%Y-%m-%d'), run[1]))
        data["run_dates"].append(date.strftime('%Y-%m-%d'))
        data["counts"].append(run[1])
    
    line1 = go.Scatter(
        x = data["run_dates"],
        y = data["counts"],
        name = 'Total Records With Browser Trusted Certs by Run',
        line = dict(
            color = ('rgb(205, 12, 24)'),
            width = 4)
    )

    lines = [line1]
    layout = dict(title = 'Data',
              xaxis = dict(title = 'Run Date'),
              yaxis = dict(title = 'Count'),
              )

    fig = dict(data=lines, layout=layout)
    py.plot(fig, filename='browser-trusted-certs', auto_open=False)

getTotalRecordsByRun(idxNameBase, countryCode)
getAllMatchingRuns(idxNameBase, countryCode)
getCountBrowserTrustedCerts(idxNameBase, countryCode)