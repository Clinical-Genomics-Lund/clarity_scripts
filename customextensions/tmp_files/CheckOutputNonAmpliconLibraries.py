import glsfileutil
import glsapiutil
from xml.dom.minidom import parseString
import getopt
import sys
import re
from collections import defaultdict
HOSTNAME = 'https://mtapp046.lund.skane.se'
api = None

def getPoolPlanID(pool_iURIs):
    pool_planID = {}
    for key in pool_iURIs.keys():
        planIDs = []
        for iURI in pool_iURIs[key] :
            iDOM = parseString(api.GET(iURI))
            planID = api.getUDF(iDOM, "planID")
            if planID not in planIDs:
                planIDs.append(planID)
        if len(planIDs) != 1:
            print "Seems like pooled amplicon libraries does not have the same planID. Please check that pooling and planning are correct"
            sys.exit(255)
        else:
            pool_planID[key] = planIDs[0]
            
    return pool_planID

def getOutputPool():
    poolsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/pools"
    poolsDOM = parseString(api.GET(poolsURI))

    IOMaps = poolsDOM.getElementsByTagName( "pool" )
    if len(IOMaps) != 1:
        print "Only one output pool allowed. Not allowed to exit step"
        sys.exit(255)
    else :
        poolURI = IOMaps[0].getAttribute( "output-uri" )

    return poolURI

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
                                      
    poolURI = getOutputPool()
    poolDOM = parseString(api.GET(poolURI))
    poolName = poolDOM.getElementsByTagName( "name" )[0].firstChild.data
    #Check that the user has not changed the pool Name
    stepDetailsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/details"
    stepDetailsDOM = parseString(api.GET(stepDetailsURI))
    planID = api.getUDF(stepDetailsDOM, "planID")

    if planID != poolName:
        print "User is not allowed to change pool name"
        sys.exit(255)
    else:
        poolDOM2 = api.setUDF( poolDOM, "planID", planID )
        r = api.PUT( poolDOM2.toxml(), poolURI)
        print r

if __name__ == "__main__":
    main()
