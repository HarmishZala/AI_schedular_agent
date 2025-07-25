import requests

api_key = "<YOUR_GOOGLE_API_KEY>"
address = "Mumbai"
url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
response = requests.get(url)
print(response.status_code)
print(response.json())