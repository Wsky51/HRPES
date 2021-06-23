import requests
import json
data={"ids": ["00007190","00007191"]}

url="https://www.chinadaily.com.cn"
data_json = json.dumps(data)
headers = {'Content-type': 'application/json',"charset":"utf-8"}

response = requests.get(url, headers = headers)

print(response.text)

