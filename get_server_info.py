from http import client
import requests 
import xmltodict, json

r = requests.get("http://localhost:8080/stats.xml")

data = xmltodict.parse('<e> <a>text</a> <a>text</a> </e>')

print(data)

print(client)