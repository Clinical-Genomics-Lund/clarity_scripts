# Takes the output file from microbiologys pipetting robot and formats it so that it can be automatically read into clarity

import sys
from datetime import datetime
import CMDfunc

sys.stdout.write("ProjectName;Submitted Sample Name;UDF/Analysis;UDF/Nucleotide Type;UDF/Department;ContainerName;Well;ContainerType;UDF/Sequencing runs;UDF/Date of arrival;UDF/Sample submission signing;UDF/Desired read count\n")

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
				sys.stdout.write("Sars NGS 2021;%s;Sars-CoV-2 IDPT;RNA;Klinisk Mikrobiologi;%s;%s;96 well plate;0;%s;Automation;400000\n" % (sampleName, barcode, well, date) )

except:
	CMDfunc.send_fail_email( '\tProcess_sarsNGS_input.py\n\nFile:\n\t%s\n' % sys.argv[1] )	

