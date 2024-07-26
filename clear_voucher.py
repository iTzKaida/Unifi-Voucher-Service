import os
import shutil

# Pfad zum Verzeichnis voucher_data
voucher_directory = 'voucher_data'

def clear_voucher_data(directory):
    if os.path.exists(directory):
        # Lösche den gesamten Inhalt des Verzeichnisses
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Entfernen der Datei
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Entfernen des Verzeichnisses
                print(f'{file_path} wurde gelöscht.')
            except Exception as e:
                print(f'Fehler beim Löschen von {file_path}. Grund: {e}')
    else:
        print(f'Das Verzeichnis {directory} existiert nicht.')

if __name__ == '__main__':
    clear_voucher_data(voucher_directory)
    print('Das Verzeichnis voucher_data wurde geleert.')
