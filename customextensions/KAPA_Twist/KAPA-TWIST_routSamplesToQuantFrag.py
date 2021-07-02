from optparse import OptionParser
import glsapiutil
from xml.dom.minidom import parseString
import sys

f = open('/all/route_to_QuantFrag_protocol.log', 'w')

DEBUG = False

#####################################################################################
### The output artifacts can be routed to one of the potential stages

availableStages = { 
                    "Quantification": "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/801/stages/1916",
                    "Dilution": "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/801/stages/1917",
                    "CovarisFragmentation": "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/801/stages/1920",
                    "EnzymaticFragmentation": "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/801/stages/1918"
                    }
#####################################################################################

def pack_and_send( stageURI, a_ToGo ):
    ## Step 4: Build and submit the routing message
    rXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">'
    rXML = rXML + '<assign stage-uri="' + stageURI + '">'
    for uri in a_ToGo:
        rXML = rXML + '<artifact uri="' + uri + '"/>'
    rXML = rXML + '</assign>'
    rXML = rXML + '</rt:routing>'

    response = api.POST( rXML, api.getBaseURI() + "route/artifacts/" )

    return response


def routeAnalytes( stageURIlist ):

    ANALYTES = []		### Cache, prevents unnessesary GET calls

    artifacts_to_route = {}
    for stageURI in stageURIlist:
        artifacts_to_route[ stageURI ] = []

    ## Step 1: Get the step XML
    processURI = args.stepURI + "/details"
    processXML = api.GET( processURI )
    processDOM = parseString( processXML )

    ## Step 2: Cache Output Analytes
    analytes = processDOM.getElementsByTagName( "input-output-map" )

    for analyte in analytes:
        if analyte.getElementsByTagName( "output" )[0].getAttribute( "output-generation-type" ) == "PerInput" :
            oURI = analyte.getElementsByTagName( "output" )[0].getAttribute( "uri" )
            iURI = analyte.getElementsByTagName( "input" )[0].getAttribute( "uri" )

            if iURI in ANALYTES:
                pass
            else:
                ANALYTES.append( iURI )
                
            analyteXML = api.GET( oURI )
            analyteDOM = parseString( analyteXML )
                
            sampleURI = analyteDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
            sampleXML = api.GET( sampleURI )
            sampleDOM = parseString( sampleXML )
                
            fragmentation = api.getUDF(analyteDOM, "Fragmentation method")
                
            if ( api.getUDF(sampleDOM, "Sample concentration (ng/ul)") ) :
                concentration = True
            else:
                concentration = False
                    
                    
            if ( concentration == False ) :
                artifacts_to_route[ availableStages["Quantification"] ].append( iURI )

            elif ( concentration == True ) :
                artifacts_to_route[ availableStages["Dilution"] ].append( iURI )
                
#            elif ( (concentration == True) and (fragmentation == "Covaris fragmentation" ) ):
#                artifacts_to_route[ availableStages["CovarisFragmentation"] ].append( iURI )
                
#            elif ( (concentration == True) and (fragmentation == "Enzymatic fragmentation" ) ):
#                artifacts_to_route[ availableStages["EnzymaticFragmentation"] ].append( iURI ) 

            else:
                print "Can only route samples to Quantification, Enzymatic fragmentation or Covaris fragmentation"
                sys.exit(255)

            api.setUDF( sampleDOM, 'Fragmentation method', fragmentation )
            sXML = api.PUT( sampleDOM.toxml().encode('utf-8'), sampleURI )
            
    return artifacts_to_route

def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')

    return Parser.parse_args()[0]

def main():

    global args
    args = setupArguments()

    global api
    api = glsapiutil.glsapiutil2()
    api.setURI( args.stepURI )
    api.setup( args.username, args.password )

    stageURIlist = list( availableStages.values() )

    if DEBUG: print stageURIlist

    artifacts_to_route = routeAnalytes( stageURIlist )

    # Sends seperate routing messages for each stage
    for stage, artifacts in artifacts_to_route.items():
        if artifacts :
            r = pack_and_send( stage, artifacts )
            
            if DEBUG: f.write( r)
            if len( parseString( r ).getElementsByTagName( "rt:routing" ) ) > 0:
                msg = str( len(artifacts) ) + " samples were added to the " + stage + " step. "
            else:
                msg = r
            print msg

if __name__ == "__main__":
    main()
