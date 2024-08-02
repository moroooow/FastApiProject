import requests


def q(name: str):
    url = "http://127.0.0.1:8000/hello"
    response = requests.get(url, params={"name": name})
    return response.json()


print(q("John"))
