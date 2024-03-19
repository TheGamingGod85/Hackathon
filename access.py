import requests

def prayatna_api_hit():
    url = 'http://13.48.136.54:8000/api/api-code/'
    api = "6e115e80-aff0-4174-9222-e5a7a37ce35b"
    bearer = "Bearer " + api

    headers = {"Authorization": bearer,
            'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers)
    cont = response.content

    return cont

print(prayatna_api_hit())

b'{"api_code":"PRAYATNA_70c516ae133a4d5fa2bbc0165b4ac68d"}'