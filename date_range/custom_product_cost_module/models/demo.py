import requests

response = requests.get("https://globalproteccion.odoo.com/bi-connector/logs/")
print(response.status_code)