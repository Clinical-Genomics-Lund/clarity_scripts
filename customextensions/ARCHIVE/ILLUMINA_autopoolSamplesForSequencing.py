import sys
import getopt
import xml.dom.minidom
import pprint
import glsapiutil
import re
from xml.dom.minidom import parseString

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

def getPoolingGroup( aURI ):

	aXML = api.getResourceByURI( aURI )
	aDOM = parseString( aXML )
	aPlanID = api.getUDF(aDOM, "planID")
	pGroup = aPlanID.split("_")[-1]

	return pGroup

def buildGroupPoolXML( poolName, alist ):

	pXML = '<pool name="' + poolName +'">'
	for aURI in alist:
		pXML = pXML + '<input uri="' + aURI + '"/>'
	pXML = pXML + '</pool>'

	return pXML

def autoPool():

	pGROUPS = {}

	## get the process XML
	pURI = BASE_URI + "processes/" + args[ "limsid" ]
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
		aURI = api.removeState(aURI)
		pGroup = getPoolingGroup( aURI )

		## let's put some artifact into the correct group for pooling
		if pGroup not in pGROUPS.keys():
			pGROUPS[ pGroup ] = []
		temp = pGROUPS[ pGroup ]
		temp.append( aURI )
		pGROUPS[ pGroup ] = temp
	
	if len( pGROUPS.keys() ) != 1 :
		print "Only pools with the same planID can be sequenced together"
		sys.exit(255)

	planID = pGROUPS.keys()[0]

	#Make sure that all pools from planning step are represented
	lines = [line.rstrip('\n') for line in open('/all/clarity_plan_run_files/' + planID + ".csv")]
	AnalysisSpecificPools = []
	for line in lines :
		tokens = line.split("_")
		if tokens[0] not in AnalysisSpecificPools :
			AnalysisSpecificPools.append(tokens[0])
			
	if len(AnalysisSpecificPools) != len(pGROUPS[planID]):
		print "The number of analysis-specific input pools does not correspond to the number of pools from the planning step." 
		sys.exit(255)

	## let's build the pooling XML based upon the groups
	pXML = '<?xml version="1.0" encoding="UTF-8"?>'
	pXML = pXML + '<stp:pools xmlns:stp="http://genologics.com/ri/step" uri="' + args[ "stepURI" ] +  '/pools">'
	pXML = pXML + '<step uri="' + args[ "stepURI" ] + '"/>'
	pXML = pXML + getStepConfiguration()
	pXML = pXML + '<pooled-inputs>'

	for key in pGROUPS.keys():
		groupContents = pGROUPS[ key ]
		name = key
		pXML = pXML + buildGroupPoolXML( name, groupContents )

	pXML = pXML + '</pooled-inputs>'
	pXML = pXML + '<available-inputs/>'
	pXML = pXML + '</stp:pools>'

	print pXML

	response = api.updateObject( pXML, args[ "stepURI" ] + "/pools" )
	print response
	
	return planID

def updateOutputPool(planID):
	pURI = BASE_URI + "processes/" + args[ "limsid" ]
	pXML = api.getResourceByURI( pURI )
	pDOM = parseString( pXML )
	pDOM2 =  api.setUDF( pDOM, "planID", planID )

	response = api.updateObject( pDOM2.toxml(), pURI )
	print response
	
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

	planID = autoPool()
	updateOutputPool(planID)

if __name__ == "__main__":
	main()
