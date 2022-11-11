#Author Filip Malmberg

import keyring
import lzma
import os
import pymysql
import subprocess
import sys
import tarfile

from datetime import datetime
from pick import pick
from time import sleep

dbpw = keyring.get_password("172.28.88.47", "simdbuploader")
printer='TTP-644MT'
packagingprinter='Zebra-ZT230'
user = os.getlogin()


try:
    os.listdir(f"/home/{user}/labelfiles")
except Exception:
    print("labelfiles folder was not found. Creating folder")
    os.mkdir(f"/home/{user}/labelfiles")

    
try:
    ps = subprocess.Popen('sudo lpinfo -m', stdout=subprocess.PIPE, shell=True)
    drivers_check = subprocess.check_output(('grep', 'TTP-644MT'), stdin=ps.stdout)
    ps.wait()
    drivers_check = drivers_check.decode().strip()
except Exception:
    print(f"Printer drivers not installed. Installing..")
    with lzma.open('drivers.tar.xz') as fd:
        with tarfile.open(fileobj=fd) as tar:
            content = tar.extractall('drivers')
    os.chdir('drivers')
    cmd = 'sudo ./install-driver'.split()
    subprocess.run(cmd)


try:
    ps = subprocess.Popen('lpstat -p -d', stdout=subprocess.PIPE, shell=True)
    printer_check = subprocess.check_output(('grep', 'TTP-644MT'), stdin=ps.stdout)
    ps.wait()
    printer_check = printer_check.decode().strip()
except Exception:
    print(f"Printer TTP-644MT not installed. Installing..")
    cmd = 'sudo lpadmin -p TTP-644MT -E -m tscbarcode/TTP-644MT.ppd -v lpd://172.28.88.43/queue -o PageSize=Custom.60x30mm'.split()
    subprocess.run(cmd)


try:
    ps = subprocess.Popen('lpstat -p -d', stdout=subprocess.PIPE, shell=True)
    printer_check = subprocess.check_output(('grep', 'ME340_lager'), stdin=ps.stdout)
    ps.wait()
    printer_check = printer_check.decode().strip()
except Exception:
    print(f"Printer ME340_lager not installed. Installing..")
    cmd = 'sudo lpadmin -p ME340_lager -E -m tscbarcode/ME340.ppd -v lpd://172.28.88.46/queue -o PageSize=Custom.60x30mm'.split()
    subprocess.run(cmd)


try:
    ps = subprocess.Popen('lpstat -p -d', stdout=subprocess.PIPE, shell=True)
    printer_check = subprocess.check_output(('grep', 'ME340_production'), stdin=ps.stdout)
    ps.wait()
    printer_check = printer_check.decode().strip()
except Exception:
    print(f"Printer ME340_production not installed. Installing..")
    cmd = 'sudo lpadmin -p ME340_production -E -m tscbarcode/ME340.ppd -v lpd://172.28.88.60/queue -o PageSize=Custom.60x30mm'.split()
    subprocess.run(cmd)


try:
    ps = subprocess.Popen('lpstat -p -d', stdout=subprocess.PIPE, shell=True)
    printer_check = subprocess.check_output(('grep', 'Zebra_ZT230_production'), stdin=ps.stdout)
    ps.wait()
    printer_check = printer_check.decode().strip()
except Exception:
    print(f"Printer Zebra_ZT230_production not installed. Installing..")
    cmd = 'sudo lpadmin -p Zebra_ZT230_production -E -m drv:///sample.drv/zebra.ppd -v socket://172.28.88.44:9100 -o PageSize=Custom.101x152mm'.split()
    subprocess.run(cmd)


try:
    ps = subprocess.Popen('lpstat -p -d', stdout=subprocess.PIPE, shell=True)
    printer_check = subprocess.check_output(('grep', 'Zebra_ZT230_lager'), stdin=ps.stdout)
    ps.wait()
    printer_check = printer_check.decode().strip()
except Exception:
    print(f"Printer Zebra_ZT230_lager not installed. Installing..")
    cmd = 'sudo lpadmin -p Zebra_ZT230_lager -E -m drv:///sample.drv/zebra.ppd -v socket://172.28.88.45:9100 -o PageSize=Custom.101x152mm'.split()
    subprocess.run(cmd)

    
title = 'Select printer: '
options = ['TTP-644MT', 'ME340_production', 'Zebra_ZT230_production', 'ME340_lager', 'Zebra_ZT230_lager']
printer, index = pick(options, title)


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
        title = 'Choose label size: '
        options = ['60x30mm', '100x20mm', '101x152mm']
        labelsize, index = pick(options, title)
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
            if labelsize == '101x152mm':
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
        cmd = f"lp -n {amount} {files_strings} -d {printer} -o media={labelsize}".split()
        subprocess.call(cmd)
