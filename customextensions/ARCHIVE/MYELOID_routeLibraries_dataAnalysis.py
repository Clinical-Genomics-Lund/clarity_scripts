import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

DEBUG = "false"
CACHE = {}
api = None 
count_steps = 0
f = open('/all/AML_DEM.txt', 'w+')

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

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

def getNonPooledArtifacts( paURI ):
    global count_steps
    count_steps += 1  

    artifacts = []

    ## get the artifact
    paXML = getObject( paURI )
    paDOM = parseString( paXML )

    ## how many samples are associated with this artifact?
    Nodes = paDOM.getElementsByTagName( "sample" )
    if len( Nodes ) == 1 & (count_steps >2):
        artifacts.append( paURI )

    else:
        ##get the process that produced this artifact
        Nodes = paDOM.getElementsByTagName( "parent-process" )
        ppURI = Nodes[0].getAttribute( "uri" )
        ppXML = getObject( ppURI )
        ppDOM = parseString( ppXML )

        ## get the limsid of this artifact
        Nodes = paDOM.getElementsByTagName( "art:artifact" )
        aLimsid = Nodes[0].getAttribute( "limsid" )

        ## get the inputs that corresponds to this artifact
        inputs = getInputArtifacts( aLimsid, ppDOM )
        for input in inputs:
            arts = getNonPooledArtifacts( input )
            for art in arts:
                artifacts.append( art )

    return artifacts

def doPOST(paURI, arts):
        rXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">'
        myeloid_panel = 0
        nextera_panel = 0

        for art in arts:
            tokens = art.split("?")
            art = tokens[0]
            artXML = getObject(art)
            artDOM = parseString( artXML )

            #Get Panel from appended workflow-specific container identifier
            LibraryName = artDOM.getElementsByTagName("name")[0].firstChild.data
            tokens = LibraryName.split("_")
            if tokens[1] == 'CAN2' :
                rXML = rXML + '<assign stage-uri="https://mtapp046.lund.skane.se/api/v2/configuration/workflows/52/stages/162">' + '<artifact uri="' + art + '"/>' + '</assign>'
                nextera_panel += 1
            elif tokens[1] == 'LNP' :
                rXML = rXML + '<assign stage-uri="https://mtapp046.lund.skane.se/api/v2/configuration/workflows/51/stages/172">' + '<artifact uri="' + art + '"/>' + '</assign>'
                myeloid_panel += 1
        if myeloid_panel >0 : 
            rXML = rXML + '<unassign workflow-uri="https://mtapp046.lund.skane.se/api/v2/configuration/workflows/51">'
            rXML = rXML + '<artifact uri="' + paURI + '"/>'
            rXML = rXML + '</unassign>'
        if nextera_panel >0:
            rXML = rXML + '<unassign workflow-uri="https://mtapp046.lund.skane.se/api/v2/configuration/workflows/52">'
            rXML = rXML + '<artifact uri="' + paURI + '"/>'
            rXML = rXML + '</unassign>'
        rXML = rXML + '</rt:routing>'
        f.write(rXML)
       
        response = api.createObject( rXML, BASE_URI + "route/artifacts/" )

def setUDF( self, DOM, udfname, udfvalue ):
    newDOM = DOM

    ##if the node already exists, delete it
    elements = newDOM.getElementsByTagName( "udf:field" )
    for element in elements:
        if element.getAttribute( "name" ) == udfname:
            newDOM.childNodes[0].removeChild( element )

    #now add the new UDF node
    newNode = newDOM.createElement( "udf:field" )
    newNode.setAttribute( "name", udfname )
    txt = newDOM.createTextNode( udfvalue )
    newNode.appendChild( txt )
    newDOM.childNodes[0].appendChild( newNode )
    return newDOM

def updateSubmittedSampleField(arts):
    global pass_fail
    pass_fail = 0
    for art in arts:
        artXML = getObject(art )
        artDOM = parseString( artXML )
        #Get Sample URI
        Nodes = artDOM.getElementsByTagName( "sample" )
        sampleURI = Nodes[0].getAttribute( "uri" )
        sampleXML = getObject( sampleURI )
        sampleDOM = parseString( sampleXML )
        #Update The submitted sample field Sequencing Runs with 1
        SequencingRuns = 0
        elements = sampleDOM.getElementsByTagName( "udf:field" )
        #Loop over the UDF:s and find the Sequencing Runs field
        for udf in elements:
            temp = udf.getAttribute( "name" )
            if temp == 'Sequencing runs':
                SequencingRuns = int(udf.firstChild.nodeValue) + 1
        #Check that the field has been updated
        if SequencingRuns == 0 :
            stepURI = args[ "stepURI" ]
            stepURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", stepURI)
            api.reportScriptStatus( stepURI, "ERROR", "The submitted sample field 'Sequencing runs' is missing on sample. Please update the field with 0 if it is the first time the sample is being sequenced.\n")
            pass_fail += 1
        #If the field is updated, make the update on the object
        else :
            f.write('\n\nsubmittedSample XML:\n' + sampleXML +'\n')
            api.setUDF( sampleDOM, 'Sequencing runs', str(SequencingRuns) )

            response = api.updateObject( sampleDOM.toxml().encode('utf-8'), sampleURI )

            f.write('\n\nUpdated submittedSample XML:\n'  + sampleDOM.toxml().encode('utf-8') +'\n')
            print('Updated the submitted sample UDF "Sequencing runs"')
    return pass_fail

def getPoolContents(PoolLimsID):
    paURI = BASE_URI + "artifacts/" + PoolLimsID
    arts = getNonPooledArtifacts( paURI )
    return paURI, arts

def getPoolLimsID():
    
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iLimsid = Nodes[0].getAttribute( "limsid" )
        inputPoolsLimsID.append( iLimsid)
        
    return inputPoolsLimsID

def main():

    global api
    global args
    global inputPoolsLimsID
    global count_steps
    global pass_fail

    args = {}
    inputPoolsLimsID = []

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    ## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
    ## so let's get this show on the road!

    inputPoolsLimsID = getPoolLimsID()
    inputPoolsLimsID = list(set(inputPoolsLimsID))        
    for PoolLimsID in inputPoolsLimsID :
        count_steps = 0 
        paURI, arts = getPoolContents(PoolLimsID)
        updateSubmittedSampleField(arts)
        if pass_fail == 0:
            doPOST(paURI, arts)

if __name__ == "__main__":
    main()

f.close()
