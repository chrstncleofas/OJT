import requests
from django.conf import settings
def send_sms_via_sinch(to_number, message):
    service_plan_id = settings.SINCH_SERVICE_PLAN_ID
    api_token = settings.SINCH_API_TOKEN
    sinch_number = settings.SINCH_PHONE_NUMBER

    url = "https://us.sms.api.sinch.com/xms/v1/" + service_plan_id + "/batches"

    payload = {
        "from": sinch_number,
        "to": [to_number],
        "body": message
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    return data
