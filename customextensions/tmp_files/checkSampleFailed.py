import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None

# Get UDFs from a dom into a dict
def get_UDFs(dom):
    udf_data = {}
    elements = dom.getElementsByTagName( "udf:field" )
    for udf in elements:
        udf_data[ udf.getAttribute("name") ] = udf.firstChild.data

    return udf_data

def checkSampleFailed(oDOM) :
    udf_data = get_UDFs(oDOM) 
    #Making sure user writes comment when re-analyzing
    if (udf_data["Sample Classification"] == "Uppdatering/Ny data analys" ):
        if not ( udf_data.get("Comment")):
            api.reportScriptStatus( stepURI , "ERROR", "Please specify reason for re-analysis in the 'Comment' field")
    
    sLIMSID = oDOM.getElementsByTagName( "sample")[0].getAttribute("limsid")
    sDOM = parseString ( api.GET('https://mtapp046.lund.skane.se/api/v2/samples/' + sLIMSID) )
    sample_udf_data = get_UDFs(sDOM)

    #Check is sample has already been analyzed
    if ( "Progress" in sample_udf_data ) :
        if ( (sample_udf_data["Progress"] == "Sequencing and Data Analysis Complete" ) and (udf_data["Sample Classification"] != "Uppdatering/Ny data analys" )  ):
             api.reportScriptStatus(stepURI, "ERROR", "At least one sample has already been analyzed. Please choose 'Sample Classification - Uppdatering/Ny data analys'" ) 

    #Check the classification field
    if (sample_udf_data["Classification"] == "Rutinprov" ):
        if( ("Valideringsprov" in udf_data["Sample Classification"] ) or ("Kvalitetskontroll" in udf_data["Sample Classification"] ) ) : 
            api.reportScriptStatus(stepURI, "ERROR", "Please review the 'Sample Classification' field. Rutinprov does not match your choice" )

    if (sample_udf_data["Classification"] == "Extern Kvalitetskontroll" ):
        if( ("Rutinprov" in udf_data["Sample Classification"] ) or ("Intern Kvalitetskontroll" in udf_data["Sample Classification"] ) or ("Valideringsprov" in udf_data["Sample Classification"])  ) : 
            api.reportScriptStatus(stepURI, "ERROR", "Please review the 'Sample Classification' field. Extern Kvalitetskontroll does not match your choice" )

    if (sample_udf_data["Classification"] == "Valideringsprov" ):
        if( ("Rutinprov" in udf_data["Sample Classification"] ) or ("Kvalitetskontroll" in udf_data["Sample Classification"] ) ) :
            api.reportScriptStatus(stepURI, "ERROR", "Please review the 'Sample Classification' field. Valideringsprov does not match your choice" )

    if (sample_udf_data["Classification"] == "Intern Kvalitetskontroll" ):
        if( ("Rutinprov" in udf_data["Sample Classification"] ) or ("Extern Kvalitetskontroll" in udf_data["Sample Classification"] ) or ("Valideringsprov" in udf_data["Sample Classification"]) ) :
            api.reportScriptStatus(stepURI, "ERROR", "Please review the 'Sample Classification' field. Intern Kvalitetskontroll does not match your choice" )
                              
def getOutputArtifacts():

    detailsDOM = parseString( api.GET(detailsURI) )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if (Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" ) :
            OutputSamples.append(parseString(api.GET( Nodes[0].getAttribute( "uri" ) )))
    
    return OutputSamples

def main():

    global api
    global args
    global OutputSamples
    global detailsURI
    global stepURI

    args = {}
    OutputSamples = []

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

    stepURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", args[ "stepURI" ])
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    ## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
    ## so let's get this show on the road!

    outputArtifacts = getOutputArtifacts()
    #Check sample failed
    for oDOM in outputArtifacts :
        checkSampleFailed(oDOM)

if __name__ == "__main__":
    main()
