import glsfileutil
import glsapiutil
from xml.dom.minidom import parseString
import getopt
import sys
import re

HOSTNAME = 'https://mtapp046.lund.skane.se'
api = None

def getInputPools():
    iPoolPlanIDs = []
    planIDs = []
    detailsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/details"
    detailsDOM = parseString(api.GET(detailsURI))

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        iPoolURI = IOMap.getElementsByTagName( "input" )[0].getAttribute( "uri" )
        iPoolDOM = parseString(api.GET(iPoolURI))
        iPoolPlanID = api.getUDF(iPoolDOM, "planID") 
        if iPoolPlanID not in iPoolPlanIDs:
            iPoolPlanIDs.append(iPoolPlanID)
            planIDs.append(iPoolPlanID.split("_")[-1])

    #Check that all input pools come from same planning step
    if len(planIDs) != 1 :
        print "Only pools coming from the same planning step can be used as inputs to this step"
        sys.exit(255)

    return planIDs[0], iPoolPlanIDs

def main():

    global api
    global args

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:")

    for o,p in opts:
        if o == '-l':
            args[ "stepLimsID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
    
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    #Get planID                                                                
    planID, iPoolPlanIDs = getInputPools()
    
    #Make sure that all pools from planning step are represented
    lines = [line.rstrip('\n') for line in open('/all/clarity_plan_run_files/' + planID.split("_")[-1] + ".csv")]
    AnalysisSpecificPools = []
    for line in lines :
        tokens = line.split("_")
        if tokens[0] not in AnalysisSpecificPools :
            AnalysisSpecificPools.append(tokens[0])

    if len(AnalysisSpecificPools) != len(iPoolPlanIDs):
        print "The number of analysis-specific input pools: " + str( len(iPoolPlanIDs) ) + " does not correspond to the number of pools from the planning step: " + str( len(AnalysisSpecificPools) )
        sys.exit(255)

if __name__ == "__main__":
    main()
