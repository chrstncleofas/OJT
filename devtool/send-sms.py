import requests

servicePlanId = "0fd6ad91886e4696a54a41882e443d0a"
apiToken = "54aed4eaea094719832e6b583029905f"
sinchNumber = "+447441421995"
toNumber = "+639610090120"

url = "https://us.sms.api.sinch.com/xms/v1/" + servicePlanId + "/batches"

payload = {
  "from": sinchNumber,
  "to": [
    toNumber
  ],
  "body": "Hello how are you"
}

headers = {
  "Content-Type": "application/json",
  "Authorization": "Bearer " + apiToken
}

response = requests.post(url, json=payload, headers=headers)

data = response.json()
print(data)