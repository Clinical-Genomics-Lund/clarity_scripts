import sys
import getopt
import xml.dom.minidom
import glsapiutil
import re
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
api = None

# Get UDFs from a dom into a dict
def get_UDFs(dom):
    udf_data = {}
    elements = dom.getElementsByTagName( "udf:field" )
    for udf in elements:
        udf_data[ udf.getAttribute("name") ] = udf.firstChild.data

    return udf_data

def getAnalysis(URI, instrument):
    Analysis_LibraryLIMSID = ""
    LibraryDOM = parseString( api.GET(URI) )

    #Get Sample info
    sampleURI = LibraryDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
    sampleDOM = parseString( api.GET(sampleURI) )
    sampleUDFs = get_UDFs(sampleDOM)

    #Find out what type of sample from Analysis field
    if "Clarigo NIPT Analys" in sampleUDFs["Analysis"] :
        Analysis_LibraryLIMSID = ("NIPT_" + URI.rsplit('/', 1)[-1])

    elif "Myeloisk Panel" in sampleUDFs["Analysis"] :
        LibraryName = LibraryDOM.getElementsByTagName("name")[0].firstChild.data.split("_")
        
        if LibraryName[-1] == 'CAN2' :
            Analysis_LibraryLIMSID = ("CAN2_" + URI.rsplit('/', 1)[-1])
        elif LibraryName[-1] == 'LNP' :
            Analysis_LibraryLIMSID = ("LNP_" + URI.rsplit('/', 1)[-1])
        else :
            print "Myeloid samples must end with either CAN2 or LNP"
            sys.exit(255)

    elif "Mikrobiologi" in sampleUDFs["Analysis"] :
        Analysis_LibraryLIMSID = ("Micro_" + URI.rsplit('/', 1)[-1])

    elif "SureSelectXTHS" in sampleUDFs["Analysis"] :
        Analysis_LibraryLIMSID = ("Exome_" + URI.rsplit('/', 1)[-1])
    
    else:
        print "The samples must be either NIPT, Myeloid, Exome or Microbiology samples. Please check the submittedSample Analysis field."
        sys.exit(255)

    # Set planID_instrument on Library
    planID = args[ "stepURI"].rsplit('/', 1)[-1] + "_" + instrument
    LibraryDOM2 = api.setUDF( LibraryDOM, "planID", planID )
    # Update
    r = api.PUT( LibraryDOM2.toxml().encode('utf-8'), URI )
    print r

    return Analysis_LibraryLIMSID

def getInputLibraries_AndSetPlanID():
    temp = []
    iLibraries = []
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
    detailsDOM = parseString(api.GET(detailsURI))

    #Get instrument
    instrument = api.getUDF(detailsDOM, "Instrument_ReadLength_ReadType")
    #Check that instrument_ReadLength_ReadType is in correct format
    searchObj = re.search(r'^.*Seq_\d{1,}_Paired|Single$', instrument )
    if not searchObj :
        print "The field 'Instrument_ReadLength_ReadType' is not filled in correctly"
        sys.exit(255)
    
    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        if iURI not in temp:
            temp.append(iURI)
    
    for URI in temp:
        iLibraries.append(getAnalysis(URI, instrument))

    return iLibraries

def main():

    global api
    global args

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    #Get information about which analysis the input Libraries belong to and update the planID for each Library
    iLibraries = getInputLibraries_AndSetPlanID()

    #Write a file containing Analysis_LimsID for each input Library. The file will be used during later steps. 
    f_out = open('/all/clarity_plan_run_files/'+ args[ "stepURI"].rsplit('/', 1)[-1] + '.csv', 'w+')
    for Library in iLibraries:
        f_out.write(Library + '\n')
    f_out.close()

if __name__ == "__main__":
        main()
