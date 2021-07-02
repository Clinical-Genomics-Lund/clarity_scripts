import glob
import os
from time import sleep
import subprocess
import sys
import re

def main():

	files = glob.glob('/mnt/limsrs-clarity/InstrSend/*')

	for file in files:
		if re.search('\.csv', file):
			command_processFile = '/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/PreAnalys/Process_rslims_csv.py %s' % file
			command = "/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/COMMON/COMMON_importSamplesCSV.py -u apiuser -p LateDollarsState592 -b https://mtapp046.lund.skane.se/api/v2/ -f <(%s)" % command_processFile
			print(command)

			subprocess.run(["bash", "-c", command])
			subprocess.run(["bash", "-c", "mv %s /mnt/limsrs-clarity/InstrSend/Archived/%s" % (file, file.split('/')[-1])])

if __name__ == '__main__':
	main()

