from http import client
import requests 
import xmltodict, json

r = requests.get("http://localhost:8080/stats.xml")

data = xmltodict.parse(r.text)

client = int(data["rtmp"]["server"]["application"]["live"]["nclients"])
uptime = int(data["rtmp"]["uptime"])
bytes_out = int(data["rtmp"]["bytes_out"])
bytes_in = int(data["rtmp"]["bytes_in"])

print(f"{client}, {uptime}, {bytes_in}, {bytes_out}", end="\r")
