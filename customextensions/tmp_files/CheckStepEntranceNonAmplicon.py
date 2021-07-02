import glsfileutil
import glsapiutil
from xml.dom.minidom import parseString
import getopt
import sys
import re
from collections import defaultdict
HOSTNAME = 'https://mtapp046.lund.skane.se'
api = None

def Pool(planID, iLibrariesURIs) : 
    pXML = '<?xml version="1.0" encoding="UTF-8"?>'
    pXML = pXML + '<stp:pools xmlns:stp="http://genologics.com/ri/step" uri="' + HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + '/pools">'
    pXML = pXML + '<step uri="' + HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ]+ '"/>'
    pXML = pXML + getStepConfiguration()
    pXML = pXML + '<pooled-inputs>' + '<pool name="' + planID + '">'
    
    for aURI in iLibrariesURIs :
        pXML = pXML + '<input uri="' + aURI + '"/>'
    pXML = pXML + '</pool>'
    pXML = pXML + '</pooled-inputs>'
    pXML = pXML + '<available-inputs/>'
    pXML = pXML + '</stp:pools>'

    response = api.PUT( pXML, HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/pools" )
    return response

def getPlanID(Library_UDF):
    planIDs = []
    for key in Library_UDF :
        planID = Library_UDF[key]["planID"]
        if planID:
            if planID not in planIDs:
                planIDs.append(planID)
        else:
            print "Analyte missing planID. Can not proceed"
            sys.exit(255)
                
    if len(planIDs) != 1 :
        print "The input Libraries must all have the same planID"
        sys.exit(255)
    else :
        planID = planIDs[0]

    return planID

def getStepConfiguration( ):
    response = ""
    stepXML = api.GET( HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] )
    stepDOM = parseString( stepXML )
    nodes = stepDOM.getElementsByTagName( "configuration" )
    if nodes:
        response = nodes[0].toxml()
        
    return response
    
# Get UDFs from a dom into a dict
def get_UDFs(dom):
    udf_data = {}
    elements = dom.getElementsByTagName( "udf:field" )
    for udf in elements:
        udf_data[ udf.getAttribute("name") ] = udf.firstChild.data

    return udf_data

def getInputLibraries():
    iLibrariesDOM = []
    iLibrariesURIs = []
    iLibrariesLimsIDs = []
    
    detailsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/details"
    detailsDOM = parseString(api.GET(detailsURI))

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        if iURI not in iLibrariesURIs :
            iLibrariesURIs.append(iURI)
            iLibrariesLimsIDs.append(Nodes[0].getAttribute("limsid"))
            iLibrariesDOM.append(parseString( api.GET(iURI) ) )

    return iLibrariesDOM, iLibrariesURIs, iLibrariesLimsIDs

def main():

    global api
    global args

    args = {}
    Library_UDF = {}
    planID_Libraries = defaultdict(list)
    analysis = ""

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
                                                                    
    iLibrariesDOM, iLibrariesURIs, iLibrariesLimsIDs = getInputLibraries()

    #Get Analyte UDFs for each Library 
    for Library in iLibrariesDOM:
        Library_UDF[Library] = get_UDFs(Library)

    #Check if all inputs come from same planning step
    planID = getPlanID(Library_UDF)

    #Make sure input Libraries are from same analysis and that all Libraries from planning step are represented
    lines = [line.rstrip('\n') for line in open('/all/clarity_plan_run_files/' + planID.split("_")[0] + ".csv")] 
    for line in lines :
        tokens = line.split("_")
        planID_Libraries[tokens[0]].append(tokens[1])

    for key in planID_Libraries :
        #Only analytes from one analysis are allowed. 
        #From the represented analysis, all analytes that were represented during planning must also be represented for normalization. 
        if len( set(iLibrariesLimsIDs).intersection(set(planID_Libraries[key])) ) > 0 :
            if len(set(iLibrariesLimsIDs).symmetric_difference(set(planID_Libraries[key])) ) == 0 :
                analysis = key
            else :
                print("WARNING: Missing or extra analytes for the " + key + " analysis: " + " ".join(set(iLibrariesLimsIDs).symmetric_difference(set(planID_Libraries[key]))) + ". Please make sure that analytes from only one analysis are present and that the input analytes correspond to the analytes used during the planning step.\n")
                sys.exit(255)

    #Update the process with Analysis_instrument_planID. This will later be copied to the output pool
    planID = analysis + "_" + planID.split('_')[1] + "_" + planID.split('_')[0]
    processURI = HOSTNAME + "/api/v2/processes/" + args[ "stepLimsID" ]
    processDOM = parseString(api.GET(processURI))
    processDOM2 = api.setUDF( processDOM, "planID", planID )
    
    r = api.PUT( processDOM2.toxml(),  processURI)

    #Pool libraries now once its known that the input is correct
    response = Pool(planID, iLibrariesURIs)
    print response

if __name__ == "__main__":
    main()
