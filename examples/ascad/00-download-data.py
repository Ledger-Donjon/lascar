"""
lascar on ASCAD Database

(https://github.com/ANSSI-FR/ASCAD)

Objective in this script:

Download the ASCAS data available online.
Unzip them...

"""
import sys
import os
import subprocess

if not len(sys.argv) == 2:
    print("Need to specify the location of ASCAD_DIR.")
    print("USAGE: python3 %s ASCAD_DIR" % sys.argv[0])
    exit()

path = os.path.abspath(sys.argv[1])
zip_path = os.path.join(path, "ASCAD_data.zip")

subprocess.call(
    [
        "wget",
        "https://www.data.gouv.fr/s/resources/ascad/20180530-163000/ASCAD_data.zip",
        "--directory-prefix",
        path,
    ]
)
subprocess.call(["unzip", zip_path, "-d", path])
subprocess.call(["rm", zip_path])
