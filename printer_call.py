from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import os
from config import DRUCKER_IP

# Drucker konfigurieren
printer_model = 'QL-820NWB'
backend = 'network'
printer_identifier = DRUCKER_IP  


# Erstellen der Druckdaten
qlr = BrotherQLRaster(printer_model)
qlr.exception_on_warning = True

label_width_mm = 62
label_height_mm = 29
label_width = 696  # 62 mm Label Breite in Druckerpunkten (bei 300 dpi)
label_height = 271  # 29 mm Label Höhe in Druckerpunkten (bei 300 dpi)

# Text konfigurieren
header_text = "WLAN-Zugang Campingplatz"
header_font_size = 45  # Größere Schriftgröße für den Header
header_font_path = "C:\\Windows\\Fonts\\Arialbd.ttf"  # Pfad zur fettgedruckten Schriftart auf Windows
header_font = ImageFont.truetype(header_font_path, header_font_size)

font_size = 40  # Kleinere Schriftgröße für den restlichen Text
font_path = "C:\\Windows\\Fonts\\Arial.ttf"  # Pfad zur normalen Schriftart auf Windows
font = ImageFont.truetype(font_path, font_size)

voucher_directory = 'voucher_data'
printed_voucher_file = os.path.join(voucher_directory, 'printed_vouchers.txt')

# Sicherstellen, dass das Verzeichnis existiert
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Funktion zum Speichern eines gedruckten Vouchers
def save_printed_voucher(guest_name):
    with open(printed_voucher_file, 'a') as file:
        file.write(f"{guest_name}\n")
    print(f"Saved voucher for: {guest_name}")

def format_voucher_code(voucher_code):
    return f"{voucher_code[:5]}-{voucher_code[5:]}"

def voucher_exists(guest_name):
    guest_name_safe = guest_name.replace(' ', '_')
    image_path = os.path.join(voucher_directory, f'{guest_name_safe}.png')
    return os.path.exists(image_path)


# Erstellen der Bilder und Druckfunktion
def print_voucher(voucher_code, guest_name, expire_minutes):
    expiry_datetime = datetime.now() + timedelta(minutes=expire_minutes)
    expiry_str = expiry_datetime.strftime("%d.%m.%Y %H:%M")

    formatted_voucher_code = format_voucher_code(voucher_code)
    
    image = Image.new('1', (label_width, label_height), 1)  # '1' für 1-Bit Modus (Monochrom)
    draw = ImageDraw.Draw(image)

    # Header hinzufügen
    header_bbox = draw.textbbox((0, 0), header_text, font=header_font)
    header_width = header_bbox[2] - header_bbox[0]
    header_height = header_bbox[3] - header_bbox[1]
    header_x = (label_width - header_width) // 2
    draw.text((header_x, 10), header_text, font=header_font, fill='black')

    # Text hinzufügen
    text_lines = [guest_name, f"WLAN-Code: {formatted_voucher_code}", f'Ablauf: {expiry_str} Uhr']
    text_y = header_height + 30  # Abstand zum Header
    for line in text_lines:
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (label_width - text_width) // 2
        draw.text((text_x, text_y), line, font=font, fill='black')
        text_y += text_height + 10  # Abstand zwischen den Zeilen

    # Speichern des Bildes
    guest_name_safe = guest_name.replace(' ', '_')  # Leerzeichen durch Unterstriche ersetzen
    image_path = os.path.join(voucher_directory, f'{guest_name_safe}.png')
    image.save(image_path)

    qlr = BrotherQLRaster(printer_model)
    qlr.exception_on_warning = True
    # Konvertierung in Druckdaten und Senden an den Drucker
    instructions = convert(
        qlr=qlr,
        images=[image_path],  # Liste der Bilddateien
        label='62x29',
        rotate='0',  # Drehen des Bildes
        threshold=70.0,
        dither=False,
        compress=False,
        red=False  # Setze auf False, um alles in Schwarz zu drucken
    )

    
    # Senden der Druckdaten an den Drucker
    send(instructions=instructions, printer_identifier=printer_identifier, backend_identifier=backend)
    print(f"Voucher für {guest_name} erfolgreich gedruckt.")
