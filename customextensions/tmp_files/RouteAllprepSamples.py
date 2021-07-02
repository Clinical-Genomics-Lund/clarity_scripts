import sys
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None

def pack_and_send( stageURI, a_ToGo ):
    ## Build and submit the routing message
    rXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">'
    rXML = rXML + '<assign stage-uri="' + stageURI + '">'
    for uri in a_ToGo:
        rXML = rXML + '<artifact uri="' + uri + '"/>'
    rXML = rXML + '</assign>'
    rXML = rXML + '</rt:routing>'

    response = api.POST( rXML, api.getBaseURI() + "route/artifacts/" )
    
    return response

def prepareCache(limsIDs):
    
    mXML = api.getArtifacts(limsIDs )
    DOM = parseString( mXML )
    return DOM

def getSamples():
    samples = []
    detailsURI = BASE_URI + "steps/" + args[ "processLimsID" ] + "/details"
    detailsDOM = parseString( api.GET(detailsURI) )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        samples.append( Nodes[0].getAttribute( "limsid" ) )

    return samples

def main():

    global api
    global args

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:")
    artifactsToRoute = []

    for o,p in opts:
        if o == '-l':
            args[ "processLimsID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )
    
    samples = getSamples()
    samplesDOM = prepareCache(samples)
    artMaps = samplesDOM.getElementsByTagName( "art:artifact" )
    for artMap in artMaps:
        Name = artMap.getElementsByTagName( "name" )[0].firstChild.data 
        Type = Name.split("_")[1]
        if Type == "RNA" :
            artifactsToRoute.append(artMap.getAttribute("uri"))
    
    #Send Allprep RNA to Tapestation step
    r = pack_and_send( "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/251/stages/372", artifactsToRoute )
    print r

if __name__ == "__main__":
    main()
