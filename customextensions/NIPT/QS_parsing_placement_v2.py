import logging
import sys
import glsfileutil
import glsapiutil
from xml.dom import minidom
from xml.dom.minidom import parseString
from optparse import OptionParser
import collections
import urllib

# XML File Parsing Script 
api = None
options = None

# Updates the steps placement page
def POSTPlacementValues( stepdetails, PlateID, dest_containerLimsID ,  oArtifacts, Result_Artifacts ):

    configNode = stepdetails.getElementsByTagName( "configuration" )[0]
    config_uri = configNode.getAttribute( "uri" )
    config_PT = configNode.firstChild.data
    config_PT = urllib.quote( config_PT )
    
    placeXML = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><stp:placements xmlns:stp="http://genologics.com/ri/step" uri="' + options.stepURI + '/placements">']
    placeXML.append( '<step uri="' + options.stepURI + '" rel="steps"/>' )
    placeXML.append( '<configuration uri="' + config_uri + '">' + config_PT + '</configuration>' )
    placeXML.append( '<output-placements>' )
    for oArt in oArtifacts:
        #If unvalid - put sample back in original tube
        if Result_Artifacts[oArt][0] == "None" :
            cName = oArt + "_invalid"
            cURI = conURI = createContainer( "Tube", cName )
            cLimsID = cURI.split("/")[-1]

            placeXML.append( '<output-placement uri="' + oArtifacts[oArt][0] + '"><location><container uri="' + api.getBaseURI() + 'containers/' + cLimsID + '" limsid="' + cLimsID + '"/>' )
            placeXML.append( '<value>' + "1:1" + '</value></location></output-placement>' )

        else :
            placeXML.append( '<output-placement uri="' + oArtifacts[oArt][0] + '"><location><container uri="' + api.getBaseURI() + 'containers/' + dest_containerLimsID + '" limsid="' + dest_containerLimsID + '"/>' )
            placeXML.append( '<value>' + Result_Artifacts[oArt][0] + '</value></location></output-placement>' )
        
    placeXML.append( '</output-placements></stp:placements>' )
    
    #Perform POST
    r = api.POST( "".join( placeXML ), options.stepURI + '/placements')

    logging.info(r)

    if "One or more of the requested wells are already in use" in r :
        print "Creating new container with same name as existing container"
        conURI = createContainer( "96 well plate", PlateID )
        POSTPlacementValues( stepdetails, PlateID, conURI ,  oArtifacts, Result_Artifacts )
    return r

def createContainer( cType, cName ):

    response = ""
    qURI = api.getBaseURI() + "containertypes?name=" + urllib.quote( cType )
    qDOM = parseString( api.GET( qURI ) )
    nodes = qDOM.getElementsByTagName( "container-type" )
    if len(nodes) == 1:
        ctURI = nodes[0].getAttribute( "uri" )
        xml = '<?xml version="1.0" encoding="UTF-8"?>'
        xml += '<con:container xmlns:con="http://genologics.com/ri/container">'
        if len(cName) > 0:
            xml += ( '<name>' + cName + '</name>' )
        else:
            xml += '<name></name>'
        xml += '<type uri="' + ctURI + '"/>'
        xml += '</con:container>'
        rXML = api.POST( xml, api.getBaseURI() + "containers" )
        rDOM = parseString( rXML )
        nodes = rDOM.getElementsByTagName( "con:container" )
        if len(nodes) > 0:
            tmp = nodes[0].getAttribute( "uri" )
            response = tmp
    elif len(nodes) == 0:
        print "This is not a valid container type."
        sys.exit(255)
    return response

def containerURIfromID( PlateID ) :
    #Check if container exist or if a new must be created
    cQueryURI = api.getBaseURI() + "containers?name=" + PlateID 
    cQueryDOM = parseString( api.GET( cQueryURI ) )
    cNodes = cQueryDOM.getElementsByTagName( "container" )
    
    if len(cNodes) != 1 :
        logging.info("NEW CONTAINER")
        conURI = createContainer( "96 well plate", PlateID )
    else:
        logging.info("EXISTING CONTAINER")
        for c in cNodes:
            for nameNode in c.childNodes:
                try:
                    if len(nameNode.firstChild.data) > 0:
                        conURI = c.getAttribute( "uri" )
                except:
                    continue	
    return conURI
	
def parseFile():
    Result_Artifacts = {}

    try :
        newFileName = str( options.resultLUID ) + ".xml"
        FH.getFile( options.resultLUID, newFileName )
        raw = open( newFileName, "r")
    except:
        print "Result File must be uploaded"
        sys.exit(255)
    try :
        xmldoc = minidom.parse(raw)
    except :
        print "Could not parse file. Please check if file is in XML format."
        sys.exit(255)
        
    Lot = xmldoc.getElementsByTagName( "Lot" )[0].firstChild.data
    InstrumentID = xmldoc.getElementsByTagName( "Instrument" )[0].firstChild.data
    RunID =  xmldoc.getElementsByTagName( "Filename" )[0].firstChild.data.split("/")[-1]
    RunID = RunID.split(".xml")[0]
    PlateID = xmldoc.getElementsByTagName( "PlateID" )[0].firstChild.data
    BatchTracks = xmldoc.getElementsByTagName( "BatchTrack" )

    artifactLocationStatus = collections.namedtuple( 'artifactLocationStatus' ,'well status')

    for Batch in BatchTracks :
        SampleTracks = Batch.getElementsByTagName( "SampleTrack" )
        for Sample in SampleTracks :
            SampleName = Sample.getElementsByTagName( "SampleCode" )[0].firstChild.data

            if Sample.getElementsByTagName( "SampleOutputPos" )[0].firstChild == None :
                SampleState = Sample.getElementsByTagName( "SampleState" )[0].firstChild.data
                SampleOutputPosition = "None"
                Result_Artifacts[SampleName] = artifactLocationStatus( SampleOutputPosition, SampleState)
            
            else :
                SampleOutputPosition = Sample.getElementsByTagName( "SampleOutputPos" )[0].firstChild.data
                SampleState = Sample.getElementsByTagName( "SampleState" )[0].firstChild.data
                Result_Artifacts[ SampleName ] = artifactLocationStatus( SampleOutputPosition, SampleState)

    return Lot, InstrumentID, RunID, PlateID, Result_Artifacts

def getOutputArtifacts():

    stepdetails = parseString( api.GET( options.stepURI + "/details" ) ) #GET the input output map

    oArtifacts = {}
    
    #Get output artifact names and URIs 
    for iomap in stepdetails.getElementsByTagName( "input-output-map" ):
        output = iomap.getElementsByTagName( "output" )[0]
        if output.getAttribute( "output-generation-type" ) == 'PerInput':
            oURI = output.getAttribute( "uri" )
            oDOM = parseString( api.GET( oURI ))
            oName = oDOM.getElementsByTagName( "name" )[0].firstChild.data

            iURI = iomap.getElementsByTagName( "input" )[0].getAttribute( "uri" )
            
            oArtifacts[ oName ] = [oURI , iURI]
    
    return stepdetails, oArtifacts

def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')
    Parser.add_option('-r', "--resultLUID", action='store', dest='resultLUID')
    Parser.add_option('-l', "--logfileLUID", action='store', dest='logfileLUID')

    return Parser.parse_args()[0]
	
def main():

    global options
    options = setupArguments()
    global api
    api = glsapiutil.glsapiutil2()

    api.setURI( options.stepURI )
    api.setup( options.username, options.password )
    logging.basicConfig(filename= options.logfileLUID ,level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')

    global FH
    FH = glsfileutil.fileHelper()
    FH.setAPIHandler( api )
    FH.setAPIAuthTokens( options.username, options.password )

    #First; get output artifacts
    stepdetails, oArtifacts = getOutputArtifacts()

    #Parse File
    Lot, InstrumentID, RunID , PlateID, Result_Artifacts = parseFile()

    #Check intersection of found artifact names
    c =  set(oArtifacts.keys()).intersection(set(Result_Artifacts.keys() ))

    if len(c) == 0 :
        print "The uploaded XML file does not contain any sample name from this step. Can not continue to place samples and parse information"
        sys.exit(255)
    if len(c) != len(oArtifacts.keys()) :
        print "All samples from this step must be represented in the uploaded XML file in order to perform placement and parsing"
        sys.exit(255)
    logging.info(Lot, InstrumentID, RunID, PlateID)
    
    #Find the destination container URI
    dest_containerURI = containerURIfromID( PlateID )
    dest_containerLimsID = dest_containerURI.split("/")[-1]

    #Update step UDFs
    stepLimsID = options.stepURI.split("/")[-1]
    processDOM = parseString( api.GET( api.getBaseURI() + "processes/" + stepLimsID ) )
    
    api.setUDF( processDOM, "QiaSymphony instrument serial number", InstrumentID )
    api.setUDF( processDOM, "Reagent cartridge lot number", Lot )
    api.setUDF( processDOM, "Run ID", RunID )
    r = api.PUT( processDOM.toxml().encode('utf-8'), api.getBaseURI() + "processes/" + stepLimsID)
    
    logging.info(r)

    #Update output artifacts
    for oArt in oArtifacts.keys():
        oDOM = parseString( api.GET(oArtifacts[oArt][0]) )
        oDOM = api.setUDF(oDOM, "QS validity of result" , Result_Artifacts[oArt][1] )

        r = api.PUT( oDOM.toxml().encode('utf-8'), oArtifacts[oArt][0])
        logging.info(r)

    #Get rid of the on-the-fly selected container
#    placementDOM = parseString( api.GET( options.stepURI + "/placements") )
#    conURI = placementDOM.getElementsByTagName("selected-containers")[0].getElementsByTagName("container")[0].getAttribute("uri")

#   print api.deleteObject( "", conURI ) # this is pretty safe since clarity won't delete a container unless its empty
    
    #Perform placement
    POSTPlacementValues( stepdetails, PlateID , dest_containerLimsID ,  oArtifacts, Result_Artifacts)

if __name__ == "__main__":
    main()
