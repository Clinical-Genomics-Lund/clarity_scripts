import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
CACHE = {}
api = None

f = open('/all/TEST_NIPT_PNR.txt', 'w+')

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

def SearchPNR(LimsID, PNR):
    searchXML = getObject( HOSTNAME + "/api/v2/samples?udf.Analysis=Clarigo+NIPT+Analys&udf.Personal+Identity+Number="+PNR )
    if searchXML:
        dom = parseString(searchXML)
        # Get all sample elements
        samples = dom.getElementsByTagName( "sample" )
        # Print sample names
        for sample in samples:
            limsid = sample.getAttribute("limsid")
            if limsid != LimsID:
                
                prevSampleDOM = parseString( getObject(HOSTNAME +'/api/v2/samples/' + limsid ) )
                prevSampleName = limsid + '_' + prevSampleDOM.getElementsByTagName("name")[0].firstChild.data
                #f.write('\nPrevious Sample:' + prevSampleName)
                prevSamples.append(prevSampleName)
    return prevSamples

def getLimsID_PNR(InputURIs, ControlCheck):

    for iURI in InputURIs:
        iXML = getObject( iURI )
        iDOM = parseString( iXML )
        #Get Sample LimsID
        Nodes = iDOM.getElementsByTagName( "sample" )
        sampleLimsID = Nodes[0].getAttribute( "limsid" )

        if sampleLimsID[0:4] == "53C-" :
            ControlCheck = "yes" 

        #Get PNR from submitted sample
        sXML = getObject( 'https://mtapp046.lund.skane.se/api/v2/samples/' + sampleLimsID)
        sDOM = parseString( sXML )
        elements = sDOM.getElementsByTagName( "udf:field" )
        for udf in elements:
            temp = udf.getAttribute( "name" )
            if temp == 'Personal Identity Number':
                PNR = udf.firstChild.data
                prevSamples = SearchPNR(sampleLimsID, PNR)
                api.setUDF( sDOM, 'Previous samples', ','.join(prevSamples) )
                XML = api.updateObject( sDOM.toxml().encode('utf-8'), HOSTNAME +'/api/v2/samples/' + sampleLimsID )
                prevSamples[:] = []
        #f.close()
    return ControlCheck


def getDetailsDOM(stepURI):
    detailsURI = stepURI + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )
    return detailsDOM

def getInputSampleURIs():
    detailsDOM = getDetailsDOM(args["stepURI"]) 

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        InputSampleURIs.append(iURI)

    return InputSampleURIs

def main():
    global api
    global InputSampleURIs
    global LimsID_PNR
    global args
    global prevSamples

    args = {}
    InputSampleURIs = []
    LimsID_PNR = {}
    prevSamples = []


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

    InputSampleURIs = getInputSampleURIs() #List with all input URIs

    ControlCheck = "no"
    ControlCheck = getLimsID_PNR(InputSampleURIs, ControlCheck) 
    
    if (ControlCheck == "no" ):
        print "Step must include negative control" 
        sys.exit(255)


if __name__ == "__main__":
    main()
