import requests
import json
from datetime import datetime, timedelta
from requests.exceptions import HTTPError
import urllib3
import config
from printer_call import print_voucher, save_printed_voucher, voucher_exists, ensure_directory_exists

# SSL-Warnungen deaktivieren
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def login():
    login_url = f"{config.BASE_URL}/api/auth/login"
    payload = {
        "username": config.USERNAME,
        "password": config.PASSWORD
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(login_url, json=payload, verify=False)
    response.raise_for_status()
    cookies = response.cookies
    csrf_token = response.headers.get('X-CSRF-Token')
    return cookies, csrf_token

def create_voucher(cookies, csrf_token, guest_name, expire_minutes):
    url = f"{config.BASE_URL}/proxy/network/api/s/{config.SITE}/cmd/hotspot"
    headers = {
        'X-CSRF-Token': csrf_token
    }
    payload = {
        'cmd': 'create-voucher',
        'n': 1,
        'expire': expire_minutes,
        'quota': 0,  # Unbegrenzte Nutzung
        'note': guest_name
    }
    response = requests.post(url, json=payload, cookies=cookies, headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()
    if 'data' in data and len(data['data']) > 0:
        voucher_id = data['data'][0]['create_time']
        return voucher_id
    else:
        raise Exception("Fehler beim Erstellen des Vouchers, keine ID zurückgegeben")

def get_voucher_code(cookies, csrf_token, voucher_id):
    url = f"{config.BASE_URL}/proxy/network/api/s/{config.SITE}/stat/voucher"
    headers = {
        'X-CSRF-Token': csrf_token
    }
    response = requests.get(url, cookies=cookies, headers=headers, verify=False)  # SSL-Verifizierung deaktiviert
    response.raise_for_status()
    data = response.json()
    if 'data' in data:
        for voucher in data['data']:
            if voucher['create_time'] == voucher_id:
                return voucher['code']
    raise Exception("Fehler beim Abrufen des Voucher-Codes")

def main():
    ensure_directory_exists('voucher_data')

    print("Anmelden...")
    try:
        cookies, csrf_token = login()
        print(f"Anmeldung erfolgreich, CSRF Token: {csrf_token}")

        guest_name = input("Geben Sie den Namen für den Voucher ein: ")

        print("Wählen Sie die Gültigkeitsdauer für den Voucher:")
        print("1. 1 Monat")
        print("2. Bis zum Ende des Jahres")
        print("3. Benutzerdefinierte Anzahl von Tagen")

        choice = input("Geben Sie Ihre Wahl ein (1, 2 oder 3): ")

        if choice == '1':
            expire_minutes = 30 * 24 * 60  # 1 Monat
        elif choice == '2':
            now = datetime.now()
            end_of_year = datetime(now.year, 12, 31, 23, 59)
            expire_minutes = int((end_of_year - now).total_seconds() / 60)
        elif choice == '3':
            custom_days = int(input("Geben Sie die Anzahl der Tage ein: "))
            expire_minutes = custom_days * 24 * 60
        else:
            print("Ungültige Wahl. Beenden.")
            return

        if not voucher_exists(guest_name):
            print(f"Erstelle Voucher für {guest_name} mit Ablauf in {expire_minutes} Minuten...")
            voucher_id = create_voucher(cookies, csrf_token, guest_name, expire_minutes)
            voucher_code = get_voucher_code(cookies, csrf_token, voucher_id)
            print(f"Voucher erfolgreich erstellt: {voucher_code}")

            print(f"Drucke Voucher für {guest_name}...")
            print_voucher(voucher_code, guest_name, expire_minutes)
            save_printed_voucher(guest_name)
        else:
            print(f"Voucher für {guest_name} wurde bereits gedruckt.")

    except HTTPError as http_err:
        print(f"HTTP-Fehler aufgetreten: {http_err}")
    except Exception as err:
        print(f"Ein Fehler ist aufgetreten: {err}")

if __name__ == "__main__":
    main()
