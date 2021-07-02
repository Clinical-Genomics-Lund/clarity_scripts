import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from pprint import pprint
from xml.dom.minidom import parseString
from ION_runPlanTemplate import  updateTorrentRunPlanLiqBi , updateTorrentRunPlan, updateTorrentRunPlanCL

HOSTNAME = ""
VERSION = ""
BASE_URI = ""
CACHE = {}
DEBUG = "false"
count_steps = 0
api = None

def setupGlobalsFromURI( uri ):

    global HOSTNAME
    global VERSION
    global BASE_URI

    tokens = uri.split( "/" )
    HOSTNAME = "/".join(tokens[0:3])
    VERSION = tokens[4]
    BASE_URI = "/".join(tokens[0:5]) + "/"

def get_udf( DOM, udfname ):

    response = ""
    
    elements = DOM.getElementsByTagName( "udf:field" )
    for udf in elements:
        temp = udf.getAttribute( "name" )
        if temp == udfname:
            response = udf.firstChild.data
            break
    return response


def getObject( URI ):

    global CACHE
    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = parseString(xml)

    return CACHE[ URI ]

def getWorkflow(chip) :
    if ("316" in chip) or ("318" in chip) :
        workflow_DR = "Oncomine Focus w2.3 - DNA and Fusions - Single Sample"
        workflow_D = "Oncomine Focus w2.3 - DNA - Single Sample"
        workflow_R = "Oncomine Focus w2.3 - Fusions - Single Sample"
        workflow_LiqBi = "Oncomine Lung Liquid Biopsy - w1.3 - DNA - Single Sample"
        workflow_CL = "Ampliseq_CL"
    else:
        if ("520" in chip) or ("530" in chip) or ("510" in chip):
            workflow_DR = "Oncomine Focus - 520 - w2.3 - DNA and Fusions - Single Sample"
            workflow_D = "Oncomine Focus - 520 - w2.3 - DNA - Single Sample"
            workflow_R = "Oncomine Focus - 520 - w2.3 - Fusions - Single Sample"
            workflow_LiqBi = "Oncomine Lung Liquid Biopsy - w1.3 - DNA - Single Sample"
            workflow_CL = "Ampliseq_CL" 
        else:
            print "Chip type must be 316, 318, 510, 520 or 530"
            sys.exit(255)

    return workflow_DR, workflow_D, workflow_R, workflow_LiqBi, workflow_CL

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

def getNonPooledArtifacts( artURI ):
    global count_steps 
    count_steps += 1
    artifacts = []

    ## get the artifact
    aDOM = getObject(artURI )

    ## how many samples are associated with this artifact?
    Nodes = aDOM.getElementsByTagName( "sample" )
    if len( Nodes ) == 1 & (count_steps >2):
        artifacts.append( artURI )

    else:
        ##get the process that produced this artifact
        Nodes = aDOM.getElementsByTagName( "parent-process" )
        ppURI = Nodes[0].getAttribute( "uri" )
        ppDOM = getObject( ppURI )

        ## get the limsid of this artifact
        Nodes = aDOM.getElementsByTagName( "art:artifact" )
        pLimsid = Nodes[0].getAttribute( "limsid" )

        ## get the inputs that corresponds to this artifact
        inputs = getInputArtifacts( pLimsid, ppDOM )
        for input in inputs:
            arts = getNonPooledArtifacts( input )
            for art in arts:
                artifacts.append( art )
        
    return artifacts

def getInfo(PoolURI, arts):
    SampleDict = {}
    SampleTubeLabel = ""
    AnalysisList= []

    diagnosis_short = {
        'Koloncancer': 'CO',
        'Lungcancer': 'LU',
        'GIST':'GI',
        'Malignt melanom': 'MM',
        'Annan (DNA)': 'D',
        'Annan (DNA + RNA)': 'DR' ,
        'Cystisk fibros' : 'CF',
        'CNS' : 'CNS'}
    
    for art in arts:
        artDOM = getObject(art )

        #Get Reagent label
        ReagentLabel = artDOM.getElementsByTagName( "reagent-label" )[0].getAttribute("name")

        #Get Sample Name 
        SampleName = artDOM.getElementsByTagName("name")[0].firstChild.data
        tokens = SampleName.split("_")

        #Get Sample URI 
        Nodes = artDOM.getElementsByTagName( "sample" )
        sampleURI = Nodes[0].getAttribute( "uri" )
        sampleDOM = getObject( sampleURI )

        #Save Sample LIMSID
        tokens2 = sampleURI.split("/")

        #Save Sample Diagnosis
        try: 
            Diagnosis = diagnosis_short[get_udf(sampleDOM, "Diagnosis")]
        except:
            print "All samples must have values for Diagnosis."
            sys.exit(255)
        
        #Save Cellularity(%)
        if tokens[1] != "CF" :
            Cellularity = get_udf(sampleDOM, "Cellularity (%)")
        else:
            Cellularity = None

        #Save Analysis
        Analysis = get_udf(sampleDOM, "Analysis")
        if Analysis not in AnalysisList :
            AnalysisList.append(Analysis)

        #SampleName, SampleName without suffix, Analysis, LimsID, Diagnosis, Cellularity
        SampleDict[ReagentLabel] = [SampleName, tokens[0], tokens[1], tokens2[6], Diagnosis , Cellularity]
    
    return SampleDict, AnalysisList

def UpdateSetID(Dictionary):

    SampleName_SetID = {}
    counter = 1

    for key in Dictionary.keys() :
        if Dictionary[key][1] not in SampleName_SetID :
            SampleName_SetID[Dictionary[key][1]] = [counter, "Unpaired"]
            counter += 1
        else:
            SampleName_SetID[Dictionary[key][1]][1] = "Paired"

    for key in Dictionary.keys() :
        Dictionary[key].append(SampleName_SetID[Dictionary[key][1]][0])
        Dictionary[key].append(SampleName_SetID[Dictionary[key][1]][1])
    
    return Dictionary

def getPoolURI():
    inputPoolURI = []
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
    detailsDOM = getObject( detailsURI )

    shortID = get_udf( detailsDOM, "Torrent Suite Planned Run - Run Code" )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        if iURI not in inputPoolURI:
            inputPoolURI.append( iURI)
            if len(inputPoolURI) > 1 :
                print "Run Plans can only be created for one pool at the time"
                sys.exit(255)

    PoolURI = inputPoolURI[0]
    #Get Sample Tube Label
    PoolDOM = getObject(PoolURI )
    SampleTubeLabel = PoolDOM.getElementsByTagName("name")[0].firstChild.data
    #Get chipType
    cURI = PoolDOM.getElementsByTagName("container")[0].getAttribute( "uri" )
    cDOM = getObject(cURI)
    chipType = cDOM.getElementsByTagName("type")[0].getAttribute( "name" )
    #Get TorrentSever
    torrentServer = get_udf( detailsDOM, "Torrent Server" )
    #Get project
    project = get_udf( detailsDOM, "Torrent Suite Data Project Label" )

    return PoolURI, shortID, SampleTubeLabel, chipType, torrentServer, project

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

    setupGlobalsFromURI( args[ "stepURI" ] )
    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    #Get Pool URI, ShortID of the RunPlan , SampleTubeLabel and ChipType
    PoolURI, shortID , SampleTubeLabel , chipType , torrentServer, project = getPoolURI()
    
    #Get artifacts from pool
    arts = getNonPooledArtifacts(PoolURI)

    #Get information from the artifacts
    SampleDict, AnalysisList = getInfo(PoolURI, arts)

    if ("Oncomine Lung Liquid Biopsy" in AnalysisList and "Oncomine Focus Assay" in AnalysisList) or ("Oncomine Lung Liquid Biopsy" in AnalysisList and "AmpliSeq CF" in AnalysisList) :
        print "Not allowed to sequence Oncomine Focus or Cystic Fibrosis samples together with Lung Liquid Biopsy samples" 
        sys.exit(255)

    #Get the Paired information
    SampleDictUpdated = UpdateSetID(SampleDict)
    
    #Get workflow
    workflow_DR, workflow_D, workflow_R, workflow_LiqBi, workflow_CL = getWorkflow(chipType)
    
    #Update the Run Plan with sample information
    if ("Oncomine Lung Liquid Biopsy" in AnalysisList) :
        updateTorrentRunPlanLiqBi( shortID, SampleTubeLabel, torrentServer, SampleDictUpdated, workflow_LiqBi, project )
    elif ("AmpliSeq ColonLung" in AnalysisList) :
        updateTorrentRunPlanCL( shortID, SampleTubeLabel, torrentServer, SampleDictUpdated, workflow_CL, project )
    else : 
        updateTorrentRunPlan( shortID, SampleTubeLabel, torrentServer, SampleDictUpdated, workflow_DR, workflow_D, workflow_R, project )

if __name__ == "__main__":
    main()
