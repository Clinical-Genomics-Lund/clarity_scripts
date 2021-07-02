import sys
import getopt
import xml.dom.minidom
import pprint
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = False
api = None

ARTIFACTS = None
CACHE_IDS = []

def setupGlobalsFromURI( uri ):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split( "/" )
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"

	if DEBUG is True:
		print HOSTNAME
		print BASE_URI

def getStepConfiguration( ):

	response = ""

	if len( args[ "stepURI" ] ) > 0:
		stepXML = api.getResourceByURI( args[ "stepURI" ] )
		stepDOM = parseString( stepXML )
		nodes = stepDOM.getElementsByTagName( "configuration" )
		if nodes:
			response = nodes[0].toxml()

	return response

def cacheArtifact( limsid ):

	global CACHE_IDS

	if limsid not in CACHE_IDS:
		CACHE_IDS.append( limsid )

def prepareCache():

	global ARTIFACTS

	lXML = '<ri:links xmlns:ri="http://genologics.com/ri">'

	for limsid in CACHE_IDS:
		link = '<link uri="' + BASE_URI + 'artifacts/' + limsid + '" rel="artifacts"/>'
		lXML = lXML + link
	lXML = lXML + '</ri:links>'

	mXML = api.getBatchResourceByURI( BASE_URI + "artifacts/batch/retrieve", lXML )
	ARTIFACTS = parseString( mXML )

def getArtifact( limsid ):

	response = None

	elements = ARTIFACTS.getElementsByTagName( "art:artifact" )
	for artifact in elements:
		climsid = artifact.getAttribute( "limsid" )
		if climsid == limsid:
			response = artifact

	return response

def getPoolingGroup( sURI ):

	response = ""

	sXML = api.getResourceByURI( sURI )
	sDOM = parseString( sXML )

	pGroup = api.getUDF( sDOM, "Personal Identity Number" )

	if pGroup != "":
		response = pGroup

	return pGroup

def buildGroupPoolXML( poolName, alist ):

	pXML = '<pool name="' + poolName +'">'
	for aURI in alist:
		pXML = pXML + '<input uri="' + aURI + '"/>'
	pXML = pXML + '</pool>'

	return pXML

def checkPoolContent (poolName, alist):
	# This dictionary will count one up if the sample is Paired, a Tumour or run on the main myeloid panel.
	# For a pool with 4 samples (paired analysis) this should be true: Paired = 4, Tumour = 2, Panel = 2
	# For a pool with 2 samples (unpaired analysis) this should be true: Paired = 0, Tumour = 1, Panel = 1
	PoolConcentCount = {}
	dict = {'PairedAnalysis': 0, 'Tumour': 0, 'Panel': 0}

	for aURI in alist: 
		# Get artifact DOM
		artXML = api.getResourceByURI( aURI )
		artDOM = parseString( artXML )

		# Get sample ID and URI
		sample = artDOM.getElementsByTagName("sample")
		sampleLimsID  = sample[0].getAttribute("limsid")
		sampleLimsURI = sample[0].getAttribute("uri")
		
		# Get sample DOM
		sampleXML = api.getResourceByURI( sampleLimsURI )
		sampleDOM = parseString(sampleXML)

		# Loop over the sample level UDFs and get the information
		elements = sampleDOM.getElementsByTagName( "udf:field" )
		for udf in elements:
			temp = udf.getAttribute( "name" )
			if temp == 'Analysis':
				if ( udf.firstChild.data == 'Myeloisk Panel - Parad') : 
					dict['PairedAnalysis'] += 1
			if temp == 'Sample Type':
				if (udf.firstChild.data.split(' ')[1] == 'malignitet' ) :
					dict['Tumour'] += 1
		# Get panel
		if (artDOM.getElementsByTagName("name")[0].firstChild.data.split('_')[1] == 'LNP') :
			dict['Panel'] += 1

	f2 = open( "/all/autopool_content.log", "a" )
	#f2.write( '\n\n\n' + aURI + '_' + sampleLimsID + ' ' + str(PairedAnalysis) + ' ' + str(Tumour) + ' ' + str(Panel) + ' ' + str(len(alist)) + '\n')
	f2.write('\n\n\n' + poolName + pprint.pformat(dict, width=1))
	f2.close()
	
	# Print response to user
	if (len(alist) == 4) : 
		if not (dict['PairedAnalysis'] == 4 and dict['Tumour'] == 2 and dict['Panel'] == 2 ) : 
			api.reportScriptStatus( args[ "stepURI" ], "ERROR", 'Please review the samples that are being pooled for patient identity number: ' + poolName + '\nFor debug purpose - the pool contains the following:\n' + pprint.pformat(dict, width=1) )
        if (len(alist) == 2) :
		if not (dict['PairedAnalysis'] == 0 and dict['Tumour'] == 2 and dict['Panel'] == 1 ) :
			api.reportScriptStatus( args[ "stepURI" ], "ERROR", 'Please review the samples that are being pooled for patient identity number: ' + poolName + '\nFor debug purpose - the pool contains the following:\n' + pprint.pformat(dict, width=1) )

def autoPool():

	pGROUPS = {}

	## step one: get the process XML
	pURI = BASE_URI + "processes/" + args[ "limsid" ]
	print pURI
	pXML = api.getResourceByURI( pURI )
	pDOM = parseString( pXML )

	IOMaps = pDOM.getElementsByTagName( "input-output-map" )
	for IOMap in IOMaps:
		input = IOMap.getElementsByTagName( "input" )
		limsid = input[0].getAttribute( "limsid" )
		cacheArtifact( limsid )

	## build our cache of Analytes
	prepareCache()

	## let's dig containers out of the cache
	for limsid in CACHE_IDS:
		artifact = getArtifact( limsid )
		aURI = artifact.getAttribute( "uri" )
		aURI = api.removeState( aURI )
		Nodes = artifact.getElementsByTagName( "sample" )
		sURI = Nodes[0].getAttribute( "uri" )
		pGroup = getPoolingGroup( sURI )

		## let's put some artifact into the correct group for pooling
		if pGroup not in pGROUPS.keys():
			pGROUPS[ pGroup ] = []
		temp = pGROUPS[ pGroup ]
		temp.append( aURI )
		pGROUPS[ pGroup ] = temp

	## let's build the pooling XML based upon the groups
	pXML = '<?xml version="1.0" encoding="UTF-8"?>'
	pXML = pXML + '<stp:pools xmlns:stp="http://genologics.com/ri/step" uri="' + args[ "stepURI" ] +  '/pools">'
	pXML = pXML + '<step uri="' + args[ "stepURI" ] + '"/>'
	pXML = pXML + getStepConfiguration()
	pXML = pXML + '<pooled-inputs>'

	for key in pGROUPS.keys():
		groupContents = pGROUPS[ key ]
		pXML = pXML + buildGroupPoolXML( key, groupContents )
		if (len(groupContents) == 4 or len(groupContents) == 2 ) :
			checkPoolContent(key, groupContents )
		else :
			api.reportScriptStatus( args[ "stepURI" ], "ERROR", 'One pool must only contain 2 or 4 samples.\nPaired analysis = 4 pooled samples.\nUnpaired analysis = 2 samples.\nPlease review your inputs to this step.' )

	pXML = pXML + '</pooled-inputs>'
	pXML = pXML + '<available-inputs/>'
	pXML = pXML + '</stp:pools>'

	print pXML

	response = api.updateObject( pXML, args[ "stepURI" ] + "/pools" )
	print response

	f = open( "/all/autopool.log", "w" )
	f.write( response )
	f.write( pXML )
	f.close()

	#api.reportScriptStatus( args[ "stepURI" ], "OK", response )

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:s:")

	for o,p in opts:
		if o == '-l':
			args[ "limsid" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p
		elif o == '-s':
			args[ "stepURI" ] = p

	setupGlobalsFromURI( args[ "stepURI" ] )
	api = glsapiutil.glsapiutil()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	## so let's get this show on the road!

	autoPool()

if __name__ == "__main__":
	main()
