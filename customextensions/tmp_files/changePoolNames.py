import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
from collections import defaultdict

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

def getInnerXml( xml, tag ):
    tagname = '<' + tag + '.*?>'
    inXml = re.sub( tagname, '', xml )
    
    tagname = '</' + tag + '>'
    inXml = inXml.replace( tagname, '' )
    
    return inXml

def main():
    api = None
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( "apiuser", "LateDollarsState592" )
    searchURI = "https://mtapp046.lund.skane.se/api/v2/processes/?type=TruSight+Myeloid+Panel+and+QAML+-+Pool+patient+specific+samples"
    searchDOM = parseString(api.GET(searchURI))
    foundProcesses = searchDOM.getElementsByTagName( "process" )
    
    for process in foundProcesses :
        pURI = process.getAttribute( "uri" )
        if pURI == "https://mtapp046.lund.skane.se/api/v2/processes/122-9851" :
            pDOM = parseString(api.GET(pURI))
            IOMaps = pDOM.getElementsByTagName( "input-output-map" )
            
            pooledSamples = defaultdict(list)
            for IOMap in IOMaps:
                iNode = IOMap.getElementsByTagName( "input" )
                iURI = iNode[0].getAttribute("uri")
                oNode = IOMap.getElementsByTagName( "output" )
                if ( oNode[0].getAttribute( "output-type" ) == "Sample" ) :
                    iName = parseString(api.GET(iURI)).getElementsByTagName( "name" )[0].firstChild.data
                    pooledSamples[oNode[0].getAttribute("uri")].append(iName)
#            print pooledSamples
            for key in pooledSamples :
                if key == "https://mtapp046.lund.skane.se/api/v2/artifacts/2-42915?state=25259" :
#                print key
#                sys.exit(255)
                    pDOM = parseString(api.GET(key))

                ## step 4: update the sample
                    nNode = pDOM.getElementsByTagName( "name" )[0]
                    name = getInnerXml( nNode.toxml(), "name" )

                ## create a new name using your own specific logic
                    newName = '+'.join(pooledSamples[key])
                
                    pXML = pDOM.toxml()
                    print pXML
                    print "\n\n"
#                newXML = re.sub( '(.*<name>)(.*)(<\/name>.*)', "\1" + newName + "\3", pXML )
                    newXML = re.sub( '<name>(.*)<\/name>.*', '<name>' + newName + '</name>', pXML )
                    print newXML

                ## step 5: save the sample
                    response = api.PUT( newXML, key )
                    print response               

if __name__ == "__main__":
    main()
