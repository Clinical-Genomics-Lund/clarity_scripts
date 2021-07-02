import sys
import getopt
import xml.dom.minidom
import glsapiutil
import re
from xml.dom.minidom import parseString

HOSTNAME = 'http://192.168.9.123:8080'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

DEBUG = True
CACHE = {}
ARGS = {}
itemFetched = 0
itemNotFetched = 0
api = None

def getObject( URI ):

	global CACHE
	global itemFetched
	global itemNotFetched

	if URI not in CACHE.keys():
		xml = api.getResourceByURI( URI )
		CACHE[ URI ] = xml
		itemFetched += 1
	else:
		itemNotFetched += 1

	return CACHE[ URI ]

def getInputArtifacts( limsid, ppDOM ):

	arts = []

	IOMaps = ppDOM.getElementsByTagName( "input-output-map" )
	for IOMap in IOMaps:
		Nodes = IOMap.getElementsByTagName( "output" )
		oLimsid = Nodes[0].getAttribute( "limsid" )
		if oLimsid == limsid:
			Nodes = IOMap.getElementsByTagName( "input" )
			iURI = Nodes[0].getAttribute( "uri" )
			arts.append( iURI )

	return arts

def getNonPooledArtifacts( aURI ):

	artifacts = []

	## get the artifact
	aXML = getObject( aURI )
	aDOM = parseString( aXML )

	## how many samples are associated with this artifact?
	Nodes = aDOM.getElementsByTagName( "sample" )
	if len( Nodes ) == 1:
		artifacts.append( aURI )

	else:
		##get the process that produced this artifact
		Nodes = aDOM.getElementsByTagName( "parent-process" )
		ppURI = Nodes[0].getAttribute( "uri" )
		ppXML = getObject( ppURI )
		ppDOM = parseString( ppXML )

		## get the limsid of this artifact
		Nodes = aDOM.getElementsByTagName( "art:artifact" )
		aLimsid = Nodes[0].getAttribute( "limsid" )

		## get the inputs that corresponds to this artifact
		inputs = getInputArtifacts( aLimsid, ppDOM )
		for input in inputs:
			arts = getNonPooledArtifacts( input )
			for art in arts:
				artifacts.append( art )

	return artifacts

def getProjectname( uri ):

	pXML = getObject( uri )
	pDOM = parseString( pXML )
	Nodes = pDOM.getElementsByTagName( "name" )
	pName = api.getInnerXml( Nodes[0].toxml(), "name" )

	return pName

def getFlowCellLane( fcDOM ):

	nodes = fcDOM.getElementsByTagName( "value" )
	if nodes:
		WP = api.getInnerXml( nodes[0].toxml(), "value" )
		tokens = WP.split( ":" )
		response = int(tokens[0])
	else:
		response = -1

	return response

def getSequenceFromIndexName( iName ):

	regex = '(.*\()(.*)(\).*)'
	cr = re.compile( regex )
	m = cr.match( iName )
	if len( m.groups() ) == 3:
		sequence = m.groups()[1]
	else:
		sequence = ""

	return sequence

def getFlowCellContents( id ):

	LINES = []
	LINES.append( "FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject" )

	cURI = BASE_URI + "containers/" + id
	cXML = api.getResourceByURI( cURI )
	cDOM = parseString( cXML )
	## get the flowcell ID
	Nodes = cDOM.getElementsByTagName( "name" )
	cName = api.getInnerXml( Nodes[0].toxml(), "name" )

	lanes = cDOM.getElementsByTagName( "placement" )
	## it would be nice to have the lanes ordered
	lanes.sort( key=getFlowCellLane )

	for lane in lanes:
		WP = getFlowCellLane( lane )
		if DEBUG: print( "Processing lane:" + str(WP) )
		aURI = lane.getAttribute( "uri" )
		aLimsID = lane.getAttribute( "limsid" )
		aXML = api.getResourceByURI( aURI )
		aDOM = parseString( aXML )
		## get the artifact name, this artifact may be a pooled library
		Nodes = aDOM.getElementsByTagName( "name" )
		aName = api.getInnerXml( Nodes[0].toxml(), "name" )

		arts = getNonPooledArtifacts( aURI )
		for art in arts:
			aXML = getObject( art )
			aDOM = parseString( aXML )
			Nodes = aDOM.getElementsByTagName( "art:artifact" )
			aLimsid = Nodes[0].getAttribute( "limsid" )

			## get the submitted sample's name:
			Nodes = aDOM.getElementsByTagName( "sample" )
			sURI = Nodes[0].getAttribute( "uri" )
			sXML = api.getResourceByURI( sURI )
			sDOM = parseString( sXML )
			Nodes = sDOM.getElementsByTagName( "name" )
			sName = api.getInnerXml( Nodes[0].toxml(), "name" )
			Nodes = sDOM.getElementsByTagName( "smp:sample" )
			sLimsID = Nodes[0].getAttribute( "limsid" )

			## get the project associated with the submitted sample
			Nodes = sDOM.getElementsByTagName( "project" )
			pURI = Nodes[0].getAttribute( "uri" )
			pName = getProjectname( pURI )

			## get the index(es), but only if we are dealing with pooled samples
			Nodes = aDOM.getElementsByTagName( "reagent-label" )

			index = "No index"
			if Nodes and len(arts) > 1:
				index = ""
				for node in Nodes:
					indexName = node.getAttribute( "name" )
					indexSequence = getSequenceFromIndexName( indexName )
					index += indexSequence + ","
					## remove trailing comma
					index = index[ :-1]

			## assemble the data we need for each row of the samplesheet
			line = cName + ',' + str(WP) + ',' + sLimsID + ',,' + index + ',' + aName + ',N,,Script,"' + pName + '"'
			LINES.append( line )

	## finally, create the file
	if len( LINES ) > 1:
		tokens = ARGS[ "filename" ].split( "." )
		## as a bonus, insert the flow cell ID into the filename
		filename = str(tokens[0]) + "-" + cName + "." + str(tokens[1])
		if DEBUG: print( "Writing:" + filename )
		file = open( filename, "w" )
		for line in LINES:
			file.write( line + "\n" )
		file.close()

def getFlowCellIDs():

	IDs = []

	## we should be able to dig these out of the placements resource:
	pURI = BASE_URI + "steps/" + ARGS[ "limsid" ] + "/placements"
	pXML = api.getResourceByURI( pURI )
	pDOM = parseString( pXML )

	## dig out the containers, and store the unique IDs
	Nodes = pDOM.getElementsByTagName( "container" )
	for container in Nodes:
		cLimsID = container.getAttribute( "limsid" )
		if cLimsID not in IDs:
			IDs.append( cLimsID )

	return IDs

def main():

	global api
	global ARGS

	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:o:")

	for o,p in opts:
		if o == '-l':						## limsid of the cluster gen process
			ARGS[ "limsid" ] = p
		elif o == '-u':						## username
			ARGS[ "username" ] = p
		elif o == '-p':						## password
			ARGS[ "password" ] = p
		elif o == '-o':						## output file name
			ARGS[ "filename" ] = p

	api = glsapiutil.glsapiutil()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( ARGS[ "username" ], ARGS[ "password" ] )

	## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
	## so let's get this show on the road!

	## functional summary:
	##			getFlowCellIDs
	##			getFlowCellContents
	##				getFlowCellLane
	##				getNonPooledArtifacts
	##					getObject
	##					getInputArtifacts
	##					getNonPooledArtifacts etc
	##				getProjectname
	##				getSequenceFromIndexName

	## get the flow cell(s) for this process
	IDs = getFlowCellIDs()

	for id in IDs:
		getFlowCellContents( id )

	if DEBUG:
		print( str(itemFetched) + " items fetched" )
		print( str(itemNotFetched) + " were not fetched as they were cached" )

if __name__ == "__main__":
	main()
