from genologics.lims import *
from genologics.entities import *
import sys
import getopt

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

        with open(args[ "outputFileLuid" ] + ".csv", "w") as f:

		sortedOutputs = {}

       		for input, output in process.input_output_maps :
			if output['output-generation-type'] == 'PerInput':
				print output
				revWell = output['uri'].location[1][2:] + output['uri'].location[1][0] # get well on the format 1A instead of A:1
				sortedOutputs[revWell] = output['limsid'] + '_' + output['uri'].samples[0].id

		for key in sorted(sortedOutputs):
			f.write( sortedOutputs[key] + '\n')

	file_out = Artifact(lims, id=args[ "outputFileLuid" ] ) 
	lims.upload_new_file(file_out , args[ "outputFileLuid" ] + ".csv")


if __name__== "__main__":
	main()

