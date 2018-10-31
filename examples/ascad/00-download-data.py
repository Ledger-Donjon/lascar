"""
lascar on ASCAD Database

(https://github.com/ANSSI-FR/ASCAD)

Objective in this script:

Download the ASCAS data available online.
Unzip them...

"""
import sys
import os

if not len(sys.argv) == 2:
    print("Need to specify the location of ASCAD_DIR.")
    print("USAGE: python3 %s ASCAD_DIR"%sys.argv[0])
    exit()


os.system("wget https://www.data.gouv.fr/s/resources/ascad/20180530-163000/ASCAD_data.zip --directory-prefix=%s"%sys.argv[1])
os.system("unzip %s/ASCAD_data.zip -d %s"%(sys.argv[1],sys.argv[1]))
os.system("rm %s/ASCAD_data.zip"%(sys.argv[1]))
