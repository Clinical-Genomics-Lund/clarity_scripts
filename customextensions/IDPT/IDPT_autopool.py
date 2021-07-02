import sys
import getopt
import xml.dom.minidom
import pprint
import glsapiutil
import re
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = False
api = None

ARTIFACTS = None
CACHE_IDS = []
reagentLableList = []

#Definition of pool groups (key = analysis at sample level, value = Pool group name) 
pGroupDef = { 'Sars-CoV-2 IDPT' : 'SarsIDPT',
	      'Microbiology WGS IDPT' : 'MicrobiologyIDPT', 
              'Microbiology WGS IDPT - CTG' : 'MicrobiologyIDPT-CTG'}

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

def checkReagentLable(reagentLable) :
	global reagentLableList 

	if reagentLable not in reagentLableList :
		reagentLableList.append(reagentLable)
	else:
		print "Index name " + reagentLable + " already detected for another sample" 
		sys.exit(255)
		

def getPoolingGroup( sURI , artifact):

	response = ""

	sXML = api.getResourceByURI( sURI )
	sDOM = parseString( sXML )
	analysis =  api.getUDF( sDOM, "Analysis" )

	sID = artifact.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )

	if analysis == "" :
		print "Detected samples with undefined analysis."
		sys.exit(255)

	pGroup = pGroupDef[analysis]

	if "IDPT" in pGroup:
		aName = artifact.getElementsByTagName( "container" )[0].getAttribute("limsid")
		pGroup = pGroup + "_" + aName
	else:
		print "Only IDPT samples accepted."
		sys.exit(255)

	return pGroup

def buildGroupPoolXML( poolName, alist ):

	pXML = '<pool name="' + poolName +'">'
	for aURI in alist:
		pXML = pXML + '<input uri="' + aURI + '"/>'
	pXML = pXML + '</pool>'

	return pXML

def autoPool():

	pGROUPS = {}

	## step one: get the process XML
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
		
		#Check indexes 
		if len(artifact.getElementsByTagName( "reagent-label" )) > 1 :
			reagents = artifact.getElementsByTagName( "reagent-label" )
			for i in reagents : 
				reagentLable = i.getAttribute("name")
				checkReagentLable(reagentLable)
		else: 
			reagentLable = artifact.getElementsByTagName( "reagent-label" )[0].getAttribute("name")
			checkReagentLable(reagentLable)

		aURI = artifact.getAttribute( "uri" )
		aURI = api.removeState( aURI )
		Nodes = artifact.getElementsByTagName( "sample" )
		sURI = Nodes[0].getAttribute( "uri" )
		pGroup = getPoolingGroup( sURI, artifact )

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
		poolName = key
		pXML = pXML + buildGroupPoolXML( poolName, groupContents )

	pXML = pXML + '</pooled-inputs>'
	pXML = pXML + '<available-inputs/>'
	pXML = pXML + '</stp:pools>'

	print pXML

	response = api.updateObject( pXML, args[ "stepURI" ] + "/pools" )
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

	autoPool()

if __name__ == "__main__":
	main()
