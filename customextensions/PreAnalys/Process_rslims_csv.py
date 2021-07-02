# Takes the output file from RS lims and formats it so that it can be automatically read into clarity

import csv
import re
import sys
from datetime import datetime
import CMDfunc

extractionDict = {"QIAAMP-FFPE-DNA" : "Qiagen QIAamp DNA FFPE Kit",
		  "QIAAMP-FAST-DNA" : "Qiagen QIAamp FAST DNA tissue kit",
                  "QIAAMP-BLOOD" : "Qiagen QIAamp Blood mini kit",
                  "MAXWELL-FFPE-DNA" : "Maxwell RSC DNA FFPE Kit",
                  "MAXWELL-FFPE-RNA" : "Maxwell RSC RNA FFPE Kit",
                  "MAXWELL-RNA" : "Maxwell RSC RNA FFPE Kit",
                  "MAXWELL-DNA" : "Maxwell RSC DNA FFPE Kit"}

def getROWS( CSVfile) :
	ROWS = []
	reader = csv.DictReader(open(CSVfile, 'rb'), delimiter=';')
	line_count = 0
	for line in reader:
		line_count +=1
		ROWS.append(line)

	return ROWS


def main():
	date = str(datetime.now().strftime("%Y-%m-%d"))
	year = str(datetime.now().strftime("%Y"))

	output = []

	lines = getROWS(sys.argv[1])
	header = lines[0].keys() + ["UDF/Date of arrival","UDF/Sample submission signing","ProjectName"]
	output.append(';'.join(header) + '\n')

	if "UDF/Personal Identity Number" in header:
		PIN = 1
	else:
		PIN = 0

	for line in lines:
		line["UDF/Date of arrival"] = date
		line["UDF/Sample submission signing"] = "Automation"

		# From the department find which project to assign to
		if "Patologi" in line["UDF/Department"]:
			line["ProjectName"] = "Pre-analys MolPat " + year
		elif "Genetik" in line["UDF/Department"]:
			line["ProjectName"] = "Pre-analys MolGen " + year
		else:
			sys.exit("Error: Department must be either MolPat or MolGen")
		line["ProjectName"] = "The_TEST_Project"

		line["UDF/Extraction"] = extractionDict[line["UDF/Extraction"]]
		# Check the format of the personal identity number if one is given
		if PIN == 1 and not line["UDF/Personal Identity Number"] == "" and not re.search("\d{8}-\w{4}", line["UDF/Personal Identity Number"]):
			sys.exit("Error: Personal identity number has the wrong format.")

		outline = []
		for key in header:
			outline.append(line[key])

		output.append(';'.join(outline) + '\n')

	for line in output:
		sys.stdout.write(line)

if __name__=='__main__':
	try:
	        main()
	except:
		CMDfunc.send_fail_email( '\tprocess_TestInput.py\n\nFile:\n\t%s\n' % sys.argv[1] )

