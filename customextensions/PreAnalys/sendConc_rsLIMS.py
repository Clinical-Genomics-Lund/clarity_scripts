from genologics.lims import *
from genologics.entities import *
import sys
import getopt
from datetime import datetime

def main():
	
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:s:u:p:o:")

	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-s':
			args[ "processLuid" ] = p
		elif o == '-o':
			args[ "outputFileLuid" ] = p

	BASEURI = args["BASEURI"].split('api')[0]
	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"]) 
	lims.check_version()

	process_id = args["processLuid"]
	process = Process(lims, id=process_id)
        
	inputs = process.all_inputs( unique=True)
	date = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
	fileOut = "ConcClarity-" + date + ".csv"

	concStr = ''

	with open(fileOut, "w") as f:
		f.write("LID;TEST;RESULT\n")
		concStr = concStr + "LID;TEST;RESULT\n"

		for input in inputs :
			try:
				f.write('%s;Clarity LimsID;%s\n' % (input.name, input.samples[0].id))
				f.write('%s;Concentration;%s\n' % (input.name, input.samples[0].udf['%s concentration (ng/ul)' % input.udf['Concentration type']]))

				concStr = concStr + ('%s;Clarity LimsID;%s\n' % (input.name, input.samples[0].id))
				concStr = concStr + ('%s;Concentration;%s\n' % (input.name, input.samples[0].udf['%s concentration (ng/ul)' % input.udf['Concentration type']]))
			except:
				print( 'All samples must have a concentration to send.' )
				sys.exit(255)

	with open("/opt/gls/clarity/customextensions/PreAnalys/tmp_sendConc/" + fileOut, 'w') as rslims:
		rslims.write(concStr)

	file_out = Artifact(lims, id = args[ "outputFileLuid" ] ) 
	lims.upload_new_file(file_out , fileOut)

if __name__== "__main__":
	main()

