#Author Filip Malmberg

import keyring
import os
import pymysql
import subprocess
import sys

from datetime import datetime
from pick import pick
from time import sleep

dbpw = keyring.get_password("172.28.88.47", "simdbuploader")
printer='TTP-644MT'
packagingprinter='Zebra-ZT230'
user = os.getlogin()

#Check if printers are installed on the system
try:
    ps = subprocess.Popen('lpstat -p -d', stdout=subprocess.PIPE, shell=True)
    printer_check = subprocess.check_output(('grep', f'{printer}'), stdin=ps.stdout)
    ps.wait()
    printer_check = printer_check.decode().strip()
except Exception:
    print(f"Printer {printer} not installed. Aborting")
    sys.exit()
try:
    ps = subprocess.Popen('lpstat -p -d', stdout=subprocess.PIPE, shell=True)
    packagingprinter_check = subprocess.check_output(('grep', f'{packagingprinter}'), stdin=ps.stdout)
    ps.wait()
    packagingprinter_check = packagingprinter_check.decode().strip()
except Exception:
    print(f"Printer {packagingprinter} not installed. Aborting")
    sys.exit()


def sqlquery(column,itemnumber):
    db = pymysql.connect(host="172.28.88.47",user="simdbuploader",password=dbpw,database="simdb")
    cursor = db.cursor()
    cursor.execute(f"SELECT {column} FROM simdb.product_label WHERE pn='{itemnumber}'")
    try:
        result = cursor.fetchone()[0]
    except Exception:
        result = False
    return(result)
    db.close()


def getitemnumber():
    while True:
        itemnumber = input('Please enter your item number: ')
        if itemnumber[0]=='6' and len(itemnumber)==6 and itemnumber.isnumeric() or len(itemnumber)==9 and '-' in itemnumber and itemnumber[0]=='6':
            dbitemnumber = sqlquery('pn',itemnumber)
            if dbitemnumber is not False:
                return(itemnumber)
                break
            else:
                print('Label does not exist in database.')
        else:
            print('Please enter a valid item number.\n')


if __name__ == '__main__':
    while True:
        title = 'Choose labeltype: '
        options = ['Chassi 60x30mm', 'Packaging 101x152mm']
        option, index = pick(options, title)
        itemnumber = getitemnumber()
        typenumber = sqlquery('type',itemnumber)
        template = sqlquery('template',itemnumber)
        if typenumber == None: #This if-statement is just for the Systrans ICR-2 units
            typenumber = ""
        serial = int(input("Enter first serial: "))
        print(f"--- 2 increments means {serial} and {serial+1} will be printed ---")
        increments = int(input("How many increments?: "))
        amount = input("Enter amount of copies to print: ")
        commands = []
        for i in range(increments):
            if option == 'Packaging 101x152mm':
                cmd = "glabels-batch-qt  "\
                        f"/mnt/fs/Icomera/Line/Supply Chain/Production/Glabels/Templates/{template}p.glabels  "\
                        f"-D  serial={serial}  "\
                        f"-D  sap={itemnumber}  "\
                        f"-D  type={typenumber}  "\
                        f"-o  /home/{user}/labelfiles/{serial}.pdf".split("  ")
            else:
                cmd = "glabels-batch-qt  "\
                    f"/mnt/fs/Icomera/Line/Supply Chain/Production/Glabels/Templates/{template}.glabels  "\
                    f"-D  serial={serial}  "\
                    f"-D  sap={itemnumber}  "\
                    f"-D  type={typenumber}  "\
                    f"-o  /home/{user}/labelfiles/{serial}.pdf".split("  ")
            commands.append(f"-c /home/{user}/labelfiles/{serial}.pdf")
            subprocess.call(cmd)
            serial = serial+1
        files_strings = " ".join(commands)
        if option == 'Packaging 101x152mm':
            cmd = f"lp -n {amount} {files_strings} -d {packagingprinter}".split()
        else:
            cmd = f"lp -n {amount} {files_strings} -d {printer}".split()
        subprocess.call(cmd)
