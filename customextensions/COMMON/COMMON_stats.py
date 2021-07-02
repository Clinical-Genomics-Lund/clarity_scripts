"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
#from genologics.entities import SampleHistory
import sys
import getopt

def main():
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:d:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-s':
			args[ "projectID" ] = p
		elif o == '-d':
			args[ "date" ] = p

	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()

	samples = lims.get_samples(projectlimsid = args[ "projectID" ])

	sampleInfo = {}
	for sample in samples:
		try:
			dateLimit = args[ "date" ].split('-')
			date = sample.date_received.split('-')

		except:
			print("failed: date must have the form yyyy-mm-dd")
			sys.exit(255)

		s = False
		if date[0] == dateLimit[0]:
			if date[1] == dateLimit[1]:
				if date[2] >= dateLimit[2]:
					s = True

				elif date[2] > dateLimit[2]:
					s = True

			elif date[1] > dateLimit[1]:
				s = True

		elif date[0] > dateLimit[0]:
				s = True

		if s:
			sampleInfo[sample.name] = []

			for key in sample.udf:
				try:
					sampleInfo[sample.name].append( '%s:%s' % (key, sample.udf[key].encode('utf-8') ))
				except:
					sampleInfo[sample.name].append( '%s:%s' % (key, str(sample.udf[key]) ))

			print 'Sample name: %s, LimsID: %s, %s' %(sample.name, sample.id, ', '.join(sampleInfo[sample.name]))
				
if __name__=='__main__':
	main()

