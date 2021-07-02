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

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]    

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

def getInputSamples():

    iFILE = open(args[ "LIST" ], "r")
    for line in iFILE :
        uri = "https://mtapp046.lund.skane.se/api/v2/samples/" + line.rstrip('\n')
        sampleXML = getObject( uri )
        sampleDOM = parseString( sampleXML )
        api.setUDF( sampleDOM, 'Progress', 'Sequencing and Data Analysis Complete' )
        response = api.updateObject( sampleDOM.toxml().encode('utf-8'), uri )    

    return response 

def main():

    global api
    global args
    global InputSamples
    global fail

    args = {}
    InputSamples = []
    fail = 0

    opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:")

    for o,p in opts:
        if o == '-l':
            args[ "LIST" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    response = getInputSamples()
    print response

if __name__ == "__main__":
    main()
