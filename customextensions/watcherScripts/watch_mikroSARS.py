import glob
import os
from time import sleep
import subprocess
import sys
import re

def main():
	files = glob.glob('/mnt/mikro-cmd/SARS-CoV-2/magna_extraktion/*')

	for file in files:
		if ('/opt/gls/clarity/customextensions/SarsCoV2/tmp_importSamples/' + file.split('/')[-1]) not in glob.glob('/opt/gls/clarity/customextensions/SarsCoV2/tmp_importSamples/*') and re.search('#.+\.txt', file):
			command_processFile = '/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/SarsCoV2/Process_sarsNGS_input.py %s' % file
			command = "/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/COMMON/COMMON_importSamplesCSV.py -u apiuser -p LateDollarsState592 -b https://mtapp046.lund.skane.se/api/v2/ -f <(%s)" % command_processFile
			print(command)

			subprocess.run(["bash", "-c", command])
			subprocess.run(["bash", "-c", "touch /opt/gls/clarity/customextensions/SarsCoV2/tmp_importSamples/%s" % file.split('/')[-1]])

if __name__ == '__main__':
	main()

