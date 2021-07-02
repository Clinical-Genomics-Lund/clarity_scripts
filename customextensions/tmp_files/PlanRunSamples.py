import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
import httplib2
import json
from pprint import pprint
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
CACHE = {}
DEBUG = "false"
count_steps = 0
api = None
f = open('/all/TB_RunPlan_Samples.txt', 'w+')


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

def getNonPooledArtifacts( PoolURI ):
    global count_steps 
    count_steps += 1
    artifacts = []

    ## get the artifact
    pXML = getObject(PoolURI )
    pDOM = parseString( pXML )

    ## how many samples are associated with this artifact?
    Nodes = pDOM.getElementsByTagName( "sample" )
    if len( Nodes ) == 1 & (count_steps >2):
        artifacts.append( PoolURI )

    else:
        ##get the process that produced this artifact
        Nodes = pDOM.getElementsByTagName( "parent-process" )
        ppURI = Nodes[0].getAttribute( "uri" )
        ppXML = getObject( ppURI )
        ppDOM = parseString( ppXML )

## get the limsid of this artifact
        Nodes = pDOM.getElementsByTagName( "art:artifact" )
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
    Samples = []
    SampleTubeLabel = ""
    
    for art in arts:
        artXML = getObject(art )
        artDOM = parseString( artXML )
        #Get Sample Name 
        SampleName = artDOM.getElementsByTagName("name")[0].firstChild.data
        tokens = SampleName.split("_")
        if tokens[1] == 'CF' :
            runName = SampleName.replace('/','-')
            runName_new = tokens[0].replace('/','-')
            
        else : 
            runName = tokens[0]
            runName_new = tokens[0]
        Samples.append(runName)
        SampleDict[runName] = []
        SampleDict[runName].append(runName_new)
        #Get Reagent label
        ReagentLabels = artDOM.getElementsByTagName( "reagent-label" )
        for reagent in ReagentLabels:
            ReagentLabel = reagent.getAttribute("name")
            SampleDict[runName].append(ReagentLabel)
        #Get Analysis
        SampleDict[runName].append(tokens[1])
        #Get Sample URI 
        Nodes = artDOM.getElementsByTagName( "sample" )
        sampleURI = Nodes[0].getAttribute( "uri" )
        sampleXML = getObject( sampleURI )
        sampleDOM = parseString( sampleXML )
        #Save Sample LIMSID
        tokens2 = sampleURI.split("/")
        SampleDict[runName].append(tokens2[6])
        #Save Sample Diagnosis
        elements = sampleDOM.getElementsByTagName( "udf:field" )
        for udf in elements:
            temp = udf.getAttribute( "name" )
            if temp == 'Diagnosis':
                Diagnosis = udf.firstChild.data
                SampleDict[runName].append(Diagnosis )
        
        #Get Sample Tube Label
        PoolXML = getObject(PoolURI )
        PoolDOM = parseString( PoolXML )
        SampleTubeLabel = PoolDOM.getElementsByTagName("name")[0].firstChild.data


    return Samples, SampleDict, SampleTubeLabel

def getPoolURI():
    inputPoolURI = []

    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )

    shortID = get_udf( detailsDOM, "Torrent Suite Planned Run - Run Code" )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        inputPoolURI.append( iURI)
        
    inputPoolURI = list(set(inputPoolURI))
    
    PoolURI = inputPoolURI[0]
    
    return PoolURI, shortID


def updateTorrentRunPlan( shortID, tubeLabel, sampleData ):

    torrent_host = 'http://10.0.224.53/'


    bed = {
        'CL':  '/results/uploads/BED/1/hg19/unmerged/detail/ColonLungV2.20140523.designed.bed',
        'CHP': '/results/uploads/BED/8/hg19/unmerged/detail/CHP2.20131001.designed.bed',
        'CF': '/results/uploads/BED/8/hg19/unmerged/detail/CFTRexon.20131001.designed.bed'}

    diagnosis_short = {
        'Koloncancer': 'CO',
        'Lungcancer': 'LU',
        'GIST':'GI',
        'Malignt melanom': 'MM',
        'Annan (CHP)': 'GIMM',
        'Annan (CL)': 'COLU' ,
        'Cystisk fibros' : 'CF'}

    
    
    h = httplib2.Http()
    h.add_credentials('ionadmin', 'ionadmin')
    headers = {"Content-type": "application/json","Accept": "application/json"}


    # Get all planned experiments
    resp, content = h.request(torrent_host + '/rundb/api/v1/plannedexperiment/', "GET" )
    cont = json.loads( content )

    # Find the URI for the one with the specified planShortID
    plan_uri = "NOT_SET"
    for plan in cont["objects"]:
        if plan["planShortID"] == shortID:
            plan_uri = plan["resource_uri"]
            break
        
    # Get the data for that plan
    resp, content = h.request( torrent_host + plan_uri, "GET" )
    plan_dict = json.loads( content )
        
    # Change values
    plan_dict["bedfile"] = bed["CL"]
    plan_dict["sampleTubeLabel"] = tubeLabel
    for sample in plan_dict["barcodedSamples"].keys():
            
        for bc in  plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"].keys():
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["reference"] = "hg19"
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["targetRegionBedFile"] = bed[ sampleData[sample][2] ]
            
            new_name = sampleData[sample][3] + '_' + sampleData[sample][0] + "_" + diagnosis_short[ sampleData[sample][4] ]
            plan_dict["barcodedSamples"][new_name] = plan_dict["barcodedSamples"][sample].copy()
            del plan_dict["barcodedSamples"][sample]
                

    # Update the plan with the new data
    resp, content = h.request( torrent_host + plan_uri + "?format=json", "PUT", json.dumps( plan_dict ) )

#Order in list: NewRunName, Barcode, Analysis, Sample LimsID, Diagnosis

def main():

    global api
    global args
    global PoolURI

    args = {}
    PoolURI = ""

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    ## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
    ## so let's get this show on the road!

    PoolURI, shortID = getPoolURI()
    arts = getNonPooledArtifacts(PoolURI)
    Samples, SampleDict, SampleTubeLabel = getInfo(PoolURI, arts)
    f.write('SampleTubeLabel: ' + SampleTubeLabel + 'shortID:' + shortID + '\n')
    for sample in Samples :
        f.write('Sample: ' + sample + 'newRunName' + SampleDict[sample][0] + ' Sample LimsID: ' + SampleDict[sample][3] + ' Barcode: ' + SampleDict[sample][1] + ' Analysis: ' + SampleDict[sample][2] + ' Diagnosis: ' + SampleDict[sample][4] + '\n')

    updateTorrentRunPlan( shortID, SampleTubeLabel, SampleDict )

if __name__ == "__main__":
    main()

f.close()
