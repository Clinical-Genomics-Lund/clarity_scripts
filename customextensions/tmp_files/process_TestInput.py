# Takes the output file from microbiologys pipetting robot and formats it so that it can be automatically read into clarity

import sys
import test_sendEmail
from datetime import datetime
import subprocess

sys.stdout.write("ProjectName;Submitted Sample Name;UDF/Analysis;UDF/Department;UDF/Date of arrival;UDF/Sample submission signing;UDF/Sequencing runs\n")

date = str(datetime.now().strftime("%Y-%m-%d"))

try:
	with open(sys.argv[1], 'r') as inputfile:
		inputfile.next()
		for line in inputfile:
			line = line.replace('"','').split('\t')
			sampleName = line[1]
			if sampleName != "No Sample":
				barcode = sys.argv[1].split("/")[-1].split('.')[0]
				well = ':'.join([line[0][0],line[0][1:]])
				runs = int(line[2])
				sys.stdout.write("The_TEST_Project;%s;Sars-CoV-2 IDPT;Klinisk Mikrobiologi;%s;Automation;%d\n" % (sampleName, date, runs) )

except:
	test_sendEmail.send_fail_email( '\tprocess_TestInput.py\n\nFile:\n\t%s\n' % sys.argv[1] )

