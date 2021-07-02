from optparse import OptionParser
import glsapiutil
from xml.dom.minidom import parseString
import sys

f = open('/all/route_to_seq_protocol.log', 'w')

DEBUG = False

#####################################################################################
### The output artifacts can be routed to one of the potential stages

availableStages = { #"NIPT_NextSeq" : "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/601/stages/1209" ,
                    #"NIPT_MiSeq" : "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/601/stages/1205",
                    #"LNP_NextSeq": "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/604/stages/1212",
                    #"CAN2_NextSeq": "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/603/stages/1211",
                    #"LNP_MiniSeq": "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/604/stages/1218",
                    #"CAN2_MiniSeq": "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/603/stages/1217",
                    #"Micro_NextSeq": "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/602/stages/1210",
                    #"Micro_MiniSeq": "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/602/stages/1216",
                    "Exome_MiniSeq": "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/201/stages/341",
                    "Exome_NextSeq": "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/201/stages/343",
                    }
#####################################################################################

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
    analytes = processDOM.getElementsByTagName( "output" )
    for analyte in analytes:
        if analyte.getAttribute( "type" ) == "Analyte":
            analyteURI = analyte.getAttribute( "uri" )
            if analyteURI in ANALYTES:
                pass
            else:
                ANALYTES.append( analyteURI )
                analyteXML = api.GET( analyteURI )
                analyteDOM = parseString( analyteXML )

                for key in availableStages.keys() : 
                    planID = api.getUDF(analyteDOM, "planID")
                    if key in planID :
                        artifacts_to_route[ availableStages[key] ].append( analyteURI )

    if DEBUG: print artifacts_to_route
    
    def pack_and_send( stageURI, a_ToGo ):
        ## Step 4: Build and submit the routing message
        rXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">'
        rXML = rXML + '<assign stage-uri="' + stageURI + '">'
        for uri in a_ToGo:
            rXML = rXML + '<artifact uri="' + uri + '"/>'
        rXML = rXML + '</assign>'
        rXML = rXML + '</rt:routing>'
        response = api.POST( rXML, api.getBaseURI() + "route/artifacts/" )
        f.write(rXML)
        return response

    # Sends seperate routing messages for each stage
    for stage, artifacts in artifacts_to_route.items():

        r = pack_and_send( stage, artifacts )

        if DEBUG: f.write( r)
        if len( parseString( r ).getElementsByTagName( "rt:routing" ) ) > 0:
            msg = str( len(artifacts) ) + " samples were added to the " + stage + " step. "
        else:
            msg = r
        print msg

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

    routeAnalytes( stageURIlist )

if __name__ == "__main__":
    main()
