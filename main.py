import requests
import json
import pyodbc
from datetime import datetime, timedelta
from requests.exceptions import HTTPError
import urllib3
import config
from printer_call import print_voucher, save_printed_voucher, voucher_exists, ensure_directory_exists
import time

# Disable SSL warnings
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
        'quota': 0,  # Unlimited use
        'note': guest_name
    }
    response = requests.post(url, json=payload, cookies=cookies, headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()
    if 'data' in data and len(data['data']) > 0:
        voucher_id = data['data'][0]['create_time']
        return voucher_id
    else:
        raise Exception("Failed to create voucher, no ID returned")

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
    raise Exception("Failed to retrieve voucher code")

def get_guest_data():
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config.DATABASE_HOST};"
        f"DATABASE={config.DATABASE_NAME};"
        f"UID={config.DATABASE_USER};"
        f"PWD={config.DATABASE_PASSWORD};"
    )
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            b.ID,
            a.Vorname,
            a.Name,
            b.Anreise,
            b.Abreise
        FROM TBL_Buchungen b
        INNER JOIN TBL_Adressen a ON a.ID = b.ID_Adressen
        WHERE b.ID_Buchungen_Status IN (2, 3)
        AND CONVERT(date, b.Anreise) = CONVERT(date, GETDATE())
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def main():
    print("Logging in...")
    try:
        cookies, csrf_token = login()
        print(f"Login successful, CSRF Token: {csrf_token}")

        vouchers_to_print = []
        
        guests = get_guest_data()
        print(f"Guests arriving today: {guests}")

        for guest in guests:
            first_name = guest.Vorname
            last_name = guest.Name
            guest_name = f"{first_name} {last_name}"
            departure_date = guest.Abreise

            if isinstance(departure_date, str):
                departure_date = datetime.strptime(departure_date, "%Y-%m-%d")

            now = datetime.now()
            departure_datetime = datetime.combine(departure_date, datetime.strptime("12:00", "%H:%M").time())
            expire_minutes = int((departure_datetime - now).total_seconds() / 60)

            if expire_minutes > 0:
                if not voucher_exists(guest_name):
                    print(f"Creating voucher for {guest_name} with expiry at {departure_datetime}...")
                    voucher_id = create_voucher(cookies, csrf_token, guest_name, expire_minutes)
                    voucher_code = get_voucher_code(cookies, csrf_token, voucher_id)
                    print(f"Voucher created successfully: {voucher_code}")

                    vouchers_to_print.append((voucher_code, guest_name, expire_minutes))
                    save_printed_voucher(guest_name)
                else:
                    print(f"Voucher for {guest_name} has already been printed.")
            else:
                print(f"Cannot create voucher for {guest_name}, departure time already passed.")

        print(f"Vouchers to print: {vouchers_to_print}")

        # Zähler initialisieren
        counter = 1
        total_vouchers = len(vouchers_to_print)

        for voucher_code, guest_name, expire_minutes in vouchers_to_print:
            if counter > total_vouchers:
                break  # Wenn der Zähler die Anzahl der Voucher in der Liste überschreitet, breche die Schleife ab
            print(f"Printing voucher {counter}/{total_vouchers} for {guest_name} with code {voucher_code}...")
            print_voucher(voucher_code, guest_name, expire_minutes)
            time.sleep(10)  # Zeitverzögerung zwischen den Drucken
            counter += 1  # Zähler erhöhen


    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

if __name__ == "__main__":
    ensure_directory_exists('voucher_data')
    main()
