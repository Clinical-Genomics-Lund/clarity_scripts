import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
import platform
from xml.dom.minidom import parseString

HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None

def getNextActionURI( containerType ):
    chip = containerType.split(" ")[1]
    S5Chip = ["510", "520", "520", "530"]
    PGMChip = ["316v2", "318"]

    if chip in S5Chip :
        nsURI = HOSTNAME + "/api/v2/configuration/protocols/351/steps/405"
    else :
        if chip in PGMChip :
            nsURI = HOSTNAME + "/api/v2/configuration/protocols/351/steps/404"

    return nsURI

def getInput() :
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
    detailsXML = api.GET( detailsURI )
    detailsDOM = parseString( detailsXML )
    
    Inputs = []
    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        if iURI not in Inputs:
            Inputs.append(iURI)
    if len(Inputs) != 1:
        print "Only one input allowed"
        sys.exit(255)
    else: 
        InputURI = Inputs[0]

    return InputURI

def main():

    global api
    global args
    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "u:p:s:")

    for o,p in opts:
        if o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-s':
            args[ "stepURI" ] = p
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    ##Step 0: Get the container type
    InputURI = getInput()

    iXML = api.GET( InputURI )
    iDOM = parseString( iXML )
    containerURI = iDOM.getElementsByTagName( "container" )[0].getAttribute( "uri")
    cXML = api.GET( containerURI )
    cDOM = parseString( cXML )
    containerType = cDOM.getElementsByTagName( "type" )[0].getAttribute( "name")

    ## Step 1: Get the XML relating to the actions resource for this step
    aURI = args[ "stepURI" ] + "/actions"
    aURI = re.sub("http://localhost:9080", HOSTNAME, aURI)
    aXML = api.GET( aURI )
    aDOM = parseString( aXML )
    
    ## Step 2: Get Next Step URI
    nsURI = getNextActionURI( containerType )
    
    nodes = aDOM.getElementsByTagName( "next-action" )
    action = "nextstep"
    for node in nodes:
        ## ignore any nodes that already have an action attribute
        if not node.hasAttribute( "action" ):
            node.setAttribute( "action", action )
            node.setAttribute( "step-uri", nsURI )

    rXML = api.PUT( aDOM.toxml(), aURI )
    print rXML

if __name__ == "__main__":
    main()
