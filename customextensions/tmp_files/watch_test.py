import glob
import os
from time import sleep
import subprocess
import sys
import re
import test_sendEmail

def main():
	files = glob.glob('/mnt/automation/SampleList/*')

	for file in files:
		if ('/mnt/automation/Archived/' + file.split('/')[-1]) not in glob.glob('/mnt/automation/Archived/*') and re.search('#.+\.txt', file):
			command_processFile = '/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/tmp_files/process_TestInput.py %s' % file
			command = "/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/COMMON/COMMON_importSamplesCSV.py -u apiuser -p LateDollarsState592 -b https://mtapp046.lund.skane.se/api/v2/ -f <(%s)" % command_processFile

			print(command)

			try:
				subprocess.run(["bash", "-c", command])
				subprocess.run(["bash", "-c", "touch /mnt/automation/Archived/%s" % file.split('/')[-1]])

			except:
				test_sendEmail.send_fail_email( '\twatch_test.py\n\nCommand:\n\t%s\n' % command )

if __name__ == '__main__':
	main()

