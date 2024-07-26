from setuptools import setup, find_packages

setup(
    name='UnifiVoucher',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'pyodbc',
        'Pillow',
        'brother_ql',
        'urllib3',
    ],
    entry_points={
        'console_scripts': [
            'Voucher_Service = main:main',  # Name des Befehls und die Funktion, die ausgeführt werden soll
        ],
    },
)
