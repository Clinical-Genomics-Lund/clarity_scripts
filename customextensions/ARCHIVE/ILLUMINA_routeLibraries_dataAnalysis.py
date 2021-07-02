import sys
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

##################################################################################### 
availableStages = { #"NIPT" : "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/601/stages/1071" ,
                    #"LNP" : "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/604/stages/1148",
                    #"CAN2" : "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/603/stages/1130",
                    #"Mikrobiologi": "https://clarity-test.lund.skane.se/api/v2/configuration/workflows/602/stages/1091",
                    "SureSelect": "https://mtapp046.lund.skane.se/api/v2/configuration/workflows/201/stages/345",
                    }
#####################################################################################

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None

def updateSequencingRuns(iSampleURI_DOM) :
    for key in iSampleURI_DOM.keys():
        SequencingRuns = api.getUDF(iSampleURI_DOM[key], "Sequencing runs")
        SequencingRuns = int(SequencingRuns) +1
        
        api.setUDF(iSampleURI_DOM[key], "Sequencing runs", SequencingRuns)
        response = api.PUT( iSampleURI_DOM[key].toxml().encode('utf-8'), key )
    return response

def pack_and_send( stageURI, a_ToGo ):
    ## Build and submit the routing message
    rXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">'
    rXML = rXML + '<assign stage-uri="' + stageURI + '">'
    for uri in a_ToGo:
        rXML = rXML + '<artifact uri="' + uri + '"/>'
    rXML = rXML + '</assign>'
    rXML = rXML + '</rt:routing>'
    
    response = api.POST( rXML, api.getBaseURI() + "route/artifacts/" )
    print response 
    return response

def routeAnalytes( stageURIlist, iLibraries ):

    artifacts_to_route = {}
    for stageURI in stageURIlist:
        artifacts_to_route[ stageURI ] = []

    for key in iLibraries.keys():
        for analysis in availableStages.keys() :
            if analysis in key:
                for item in iLibraries[key] :
                    artifacts_to_route[ availableStages[analysis] ].append( item )

    for stage, artifacts in artifacts_to_route.items():
        if len(artifacts) > 0:
            r = pack_and_send( stage, artifacts )
            print r
        else:
            print "No artifacts to route. Please ask system admin."
            sys.exit(255)

def getInputLibraries(planID):
    iURIlist = []
    iLibraries = {}
    iSampleURI_DOM = {}
    PlanDetailsURI = BASE_URI + "steps/" + planID + "/details"
    PlanDetailsDOM = parseString( api.GET(PlanDetailsURI) )

    IOMaps = PlanDetailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        if iURI not in iURIlist:
            iURIlist.append(iURI)

    for iURI in iURIlist:
        iDOM = parseString( api.GET(iURI) )
        iSampleURI = iDOM.getElementsByTagName("sample")[0].getAttribute("uri")
        iSampleDOM = parseString( api.GET(iSampleURI) )
        iSampleURI_DOM[iSampleURI] = iSampleDOM
        Analysis = api.getUDF(iSampleDOM, "Analysis" )
        
        if "Myeloisk" in Analysis :
            Name = iDOM.getElementsByTagName( "name" )[0].firstChild.data
            if "LNP" in Name:
                Analysis = "LNP"
            elif "CAN2" in Name :
                Analysis = "CAN2"
            else:
                print "The library names of samples from the Myeloid analysis must contain LNP or CAN2 as panel identifiers" 
                sys.exit(255)

        if Analysis in iLibraries :
            iLibraries[Analysis].append(iURI)
        else:
            iLibraries[Analysis] = [iURI]

    return iLibraries, iSampleURI_DOM

def getPlanID():
    stepURI = BASE_URI + "steps/" + args[ "processLimsID" ] + "/details"
    stepDOM = parseString( api.GET(stepURI) )
    planID = api.getUDF(stepDOM, "planID")

    return planID

def main():

    global api
    global args
    global planID

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:")

    for o,p in opts:
        if o == '-l':
            args[ "processLimsID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )
    
    planID = getPlanID()
    iLibraries, iSampleURI_DOM = getInputLibraries(planID)

    stageURIlist = list( availableStages.values() )
    routeAnalytes( stageURIlist , iLibraries)
#    response = updateSequencingRuns(iSampleURI_DOM)
#    print response

if __name__ == "__main__":
    main()
