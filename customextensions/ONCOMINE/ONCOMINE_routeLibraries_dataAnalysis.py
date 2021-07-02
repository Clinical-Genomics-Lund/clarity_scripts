import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
import platform
from xml.dom.minidom import parseString

HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
DEBUG = "false"
CACHE = {}
api = None
f = open('/all/DemultiplexedOncomine_samples.txt', 'w+')

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.GET( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]

def getInputArtifacts( limsid, ppDOM ):

    arts = []

    IOMaps = ppDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        oLimsid = Nodes[0].getAttribute( "limsid" )
        if oLimsid == limsid:
            Nodes = IOMap.getElementsByTagName( "input" )
            iURI = Nodes[0].getAttribute( "uri" )
            arts.append( iURI )

    return arts

def getNonPooledArtifacts( paURI ):

    artifacts = []

    ## get the artifact
    paXML = getObject( paURI )
    paDOM = parseString( paXML )

    ## how many samples are associated with this artifact?
    Nodes = paDOM.getElementsByTagName( "sample" )
    if len( Nodes ) == 1 :
        artifacts.append( paURI )

    else:
        ##get the process that produced this artifact
        Nodes = paDOM.getElementsByTagName( "parent-process" )
        ppURI = Nodes[0].getAttribute( "uri" )
        ppXML = getObject( ppURI )
        ppDOM = parseString( ppXML )

        ##get the limsid of this artifact
        Nodes = paDOM.getElementsByTagName( "art:artifact" )
        aLimsid = Nodes[0].getAttribute( "limsid" )

        ##get the inputs that corresponds to this artifact
        inputs = getInputArtifacts( aLimsid, ppDOM )
        for input in inputs:
            arts = getNonPooledArtifacts( input )
            for art in arts:
                artifacts.append( art )

    return artifacts

def doPOST(paURI, arts):
        cancer_samples = []
        CF_samples = [] 
        LiqBio_samples = []
        CL_samples = []

        for art in arts:
            art = art.split("?")[0]
            artXML = getObject(art)
            artDOM = parseString( artXML )
            LibraryName = artDOM.getElementsByTagName("name")[0].firstChild.data
            LibraryType = LibraryName.split("_")[1]

            if ( (LibraryType == 'DNA') or (LibraryType == 'RNA' ) ) : 
                cancer_samples.append(art)
            elif (LibraryType == 'CF') : 
                CF_samples.append(art)
            elif (LibraryType == 'LiqBio') :
                LiqBio_samples.append(art)
            elif (LibraryType == 'CL') :
                CL_samples.append(art)

            else:
                print "The sample name must be tagged with CL, CHP , CF or LiqBio"
                sys.exit(255)

        if (len(cancer_samples) > 0 ) :
            cancerXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing"><assign stage-uri="' + HOSTNAME + '/api/v2/configuration/workflows/251/stages/401">'
            for sample in cancer_samples:
                cancerXML = cancerXML + '<artifact uri="' + sample + '"/>'
            cancerXML = cancerXML + '</assign>'
            cancerXML = cancerXML + '<unassign workflow-uri="' + HOSTNAME + '/api/v2/configuration/workflows/251"><artifact uri="' + paURI + '"/></unassign></rt:routing>'
            response_cancer = api.POST( cancerXML, BASE_URI + "route/artifacts/" )
            f.write('\nRouted cancer sample:\n' + cancerXML+ '\n')
                 
        if (len(CF_samples) > 0 ) :
            CFXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing"><assign stage-uri="' + HOSTNAME + '/api/v2/configuration/workflows/301/stages/415">'
            for sample in CF_samples:
                CFXML = CFXML + '<artifact uri="' + sample + '"/>'
            CFXML = CFXML + '</assign>'
            CFXML = CFXML + '<unassign workflow-uri="' + HOSTNAME + '/api/v2/configuration/workflows/301"><artifact uri="' + paURI + '"/></unassign></rt:routing>'
            response_CF = api.POST( CFXML, BASE_URI + "route/artifacts/" )
            f.write('\n\n' + 'Routed CF sample:\n' + CFXML + '\n')

        if (len(LiqBio_samples) > 0 ) :
            LiqBioXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing"><assign stage-uri="' + HOSTNAME + '/api/v2/configuration/workflows/501/stages/860">'
            for sample in LiqBio_samples:
                LiqBioXML = LiqBioXML + '<artifact uri="' + sample + '"/>'
            LiqBioXML = LiqBioXML + '</assign>'
            LiqBioXML = LiqBioXML + '<unassign workflow-uri="' + HOSTNAME + '/api/v2/configuration/workflows/501"><artifact uri="' + paURI + '"/></unassign></rt:routing>'
            response_LiqBio = api.POST( LiqBioXML, BASE_URI + "route/artifacts/" )
            f.write('\n\n' + 'Routed LiqBio sample:\n' + LiqBioXML + '\n')

        if (len(CL_samples) > 0 ) :
            CLXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing"><assign stage-uri="' + HOSTNAME + '/api/v2/configuration/workflows/554/stages/971">'
            for sample in CL_samples:
                CLXML = CLXML + '<artifact uri="' + sample + '"/>'
            CLXML = CLXML + '</assign>'
            CLXML = CLXML + '<unassign workflow-uri="' + HOSTNAME + '/api/v2/configuration/workflows/554"><artifact uri="' + paURI + '"/></unassign></rt:routing>'
            response_CL = api.POST( CLXML, BASE_URI + "route/artifacts/" )
            f.write('\n\n' + 'Routed CL sample:\n' + CLXML + '\n')

def setUDF( self, DOM, udfname, udfvalue ):
    newDOM = DOM

    ##if the node already exists, delete it
    elements = newDOM.getElementsByTagName( "udf:field" )
    for element in elements:
        if element.getAttribute( "name" ) == udfname:
            newDOM.childNodes[0].removeChild( element )

    #now add the new UDF node
    newNode = newDOM.createElement( "udf:field" )
    newNode.setAttribute( "name", udfname )
    txt = newDOM.createTextNode( udfvalue )
    newNode.appendChild( txt )
    newDOM.childNodes[0].appendChild( newNode )
    return newDOM
    
def updateSubmittedSampleField(arts):
    pass_fail = 0 

    for art in arts:
        artXML = getObject(art )
        artDOM = parseString( artXML )

        #Get Sample URI
        Nodes = artDOM.getElementsByTagName( "sample" )
        sampleURI = Nodes[0].getAttribute( "uri" )
        sampleXML = getObject( sampleURI )
        sampleDOM = parseString( sampleXML )

        SequencingRuns = 0
        SequencingUDF = api.getUDF(sampleDOM, "Sequencing runs")
        SequencingRuns = int(SequencingUDF) + 1

        if SequencingRuns == 0 :
            print "The submitted sample field 'Sequencing runs' is missing on sample. Please update the field with 0 if it is the first time the sample is being sequenced.\n"
            pass_fail += 1

        else :
            api.setUDF( sampleDOM, 'Sequencing runs', str(SequencingRuns) )
            f.write('\n\nUpdated submittedSample XML:\n' + sampleDOM.toxml().encode('utf-8') + '\n')
            rXML = api.PUT( sampleDOM.toxml().encode('utf-8'), sampleURI )
            print('Updated the submitted sample UDF "Sequencing runs"')

    return pass_fail

def getPoolLimsID():
    
        detailsURI = args[ "stepURI" ] + "/details"
        detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
        detailsXML = api.GET( detailsURI )
        detailsDOM = parseString( detailsXML )

        IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
        for IOMap in IOMaps:
            Nodes = IOMap.getElementsByTagName( "input" )
            iLimsid = Nodes[0].getAttribute( "limsid" )
            if iLimsid not in inputPoolsLimsID:
                inputPoolsLimsID.append( iLimsid)
        return inputPoolsLimsID

def main():

    global api
    global args
    global inputPoolsLimsID
    global pass_fail

    args = {}
    inputPoolsLimsID = []

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
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    inputPoolsLimsID = getPoolLimsID()
            
    for PoolLimsID in inputPoolsLimsID :
        paURI = BASE_URI + "artifacts/" + PoolLimsID
        arts = getNonPooledArtifacts( paURI )
        #Update Submitted Sample Progress
        pass_fail = updateSubmittedSampleField(arts)
        if pass_fail == 0:
            #Demultiplex the samples
            doPOST(paURI, arts)

if __name__ == "__main__":
    main()
