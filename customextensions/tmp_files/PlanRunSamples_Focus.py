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
    else:
        if ("520" in chip) or ("530" in chip):
            workflow_DR = "Oncomine Focus - 520 - w2.3 - DNA and Fusions - Single Sample"
            workflow_D = "Oncomine Focus - 520 - w2.3 - DNA - Single Sample"
            workflow_R = "Oncomine Focus - 520 - w2.3 - Fusions - Single Sample"
        else:
            print "Chip type must be 316, 318, 520 or 530"
            sys.exit(255)

    return workflow_DR, workflow_D, workflow_R

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
        Diagnosis = diagnosis_short[get_udf(sampleDOM, "Diagnosis")]
        
        #Save Cellularity(%)
        if tokens[1] != "CF" :
            Cellularity = get_udf(sampleDOM, "Cellularity (%)")
        else:
            Cellularity = None

        #SampleName, SampleName without suffix, Analysis, LimsID, Diagnosis, Cellularity
        SampleDict[ReagentLabel] = [SampleName, tokens[0], tokens[1], tokens2[6], Diagnosis , Cellularity]

    return SampleDict

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

    return PoolURI, shortID, SampleTubeLabel, chipType, torrentServer

def updateTorrentRunPlan( shortID, tubeLabel, torrentServer, sampleData, workflow_DR, workflow_D, workflow_R ):
    #Set host server
    if torrentServer == "pgm2" :
        torrent_host = 'http://10.0.224.53/'
        bed = {
            'DNA':  '/results/uploads/BED/37/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'RNA': '/results/uploads/BED/37/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'CF': '/results/uploads/BED/12/hg19/unmerged/detail/CFTRexon.20131001.designed.bed'}

        hotspot = {
            'DNA' : '/results/uploads/BED/41/hg19/unmerged/detail/Oncomine_Focus.20160219.hotspots.bed' }

    elif torrentServer == "S5" :
        torrent_host = 'http://10.0.224.62/'
        bed = {
            'DNA':  '/results/uploads/BED/12/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'RNA': '/results/uploads/BED/12/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'CF': '/results/uploads/BED/9/hg19/unmerged/detail/CFTRexon.20131001.designed.bed'}

        hotspot = {
            'DNA' : '/results/uploads/BED/16/hg19/unmerged/detail/Oncomine_Focus.20160219.hotspots.bed' }
    else :
        print "Torrent Server must be either pgm2 or S5"
        sys.exit(255)
    
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
    plan_dict["bedfile"] = bed["DNA"]
    plan_dict["sampleTubeLabel"] = tubeLabel
    plan_dict["planStatus"] = "pending"
    
    #Update the content in "barcodedSamples"
    for sample in plan_dict["barcodedSamples"].keys():
        
        for bc in  plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"].keys():
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["reference"] = "hg19"
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["targetRegionBedFile"] = bed[ sampleData[bc][2] ]
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["controlType"] = ""
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["sseBedFile"] = ""

            if (sampleData[bc][2] == "DNA" ) or (sampleData[bc][2] == "CF") :
#                plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["hotSpotRegionBedFile"] = hotspot[ sampleData[bc][2] ]
                plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["nucleotideType"] = "DNA"
                if (sampleData[bc][2] == "DNA" ) :
                    plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["hotSpotRegionBedFile"] = hotspot[ sampleData[bc][2] ]  
            else:
                if (sampleData[bc][2] == "RNA" ) :
                    plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["nucleotideType"] = "RNA"
                else:
                    print "The suffix after the sample name must be either DNA, RNA or CF"
                    sys.exit(255)
            if sampleData[bc][4] == "CF" :
                sampleName = sampleData[bc][3] + '_' + sampleData[bc][0]
            else:
                sampleName = sampleData[bc][3] + '_' + sampleData[bc][0] + '_' + sampleData[bc][4]
            sampleName = sampleName.decode('unicode-escape')
            plan_dict["barcodedSamples"][sampleName] = plan_dict["barcodedSamples"][sample].copy()
            del plan_dict["barcodedSamples"][sample]    

    del plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"] 
    plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"] = []

    for bc in sampleData.keys() :
        sampleName = sampleData[bc][3] + '_' + sampleData[bc][0] + '_' + sampleData[bc][4]
        sampleName = sampleName.decode('unicode-escape')
        default_dict = { u'Gender': u'',
                         u'NucleotideType': sampleData[bc][2].decode('unicode-escape'),
                         u'Relation': u'Self',
                         u'RelationRole': u'Self',
                         u'barcodeId': bc.decode('unicode-escape'),
                         u'biopsyDays': u'',
                         u'cancerType': u'',
                         u'cellularityPct': str(sampleData[bc][5]).decode('unicode-escape'),
                         u'cellNum': u'',
                         u'coupleID': u'',
                         u'embryoID': u'',
                         u'sample': sampleName,
                         u'sampleDescription': u'',
                         u'sampleExternalId': u'',
                         u'sampleName': sampleName,
                         u'setid': str(sampleData[bc][6]).decode('unicode-escape'),
                         }

        if sampleData[bc][2] == "CF" :
            default_dict[u'ApplicationType'] = u'UploadOnly' 
            default_dict[u'NucleotideType'] = u'DNA'
            default_dict[u'tag_isFactoryProvidedWorkflow'] = None
            default_dict[u'Workflow'] = u''

        else :
            if sampleData[bc][7] == "Paired" :
                default_dict[u'ApplicationType'] = u'Oncomine_DNA_RNA_Fusion'
                default_dict[u'Relation'] = u'DNA_RNA'
                default_dict[u'tag_isFactoryProvidedWorkflow'] = u'true'
                default_dict[u'Workflow'] = workflow_DR.decode('unicode-escape')
                
            else:
                if sampleData[bc][2] == "DNA" :
                    default_dict[u'ApplicationType'] = u'Amplicon Low Frequency Sequencing'
                    default_dict[u'tag_isFactoryProvidedWorkflow'] = u'true'
                    default_dict[u'Workflow'] = workflow_D.decode('unicode-escape')
                if sampleData[bc][2] == "RNA" :
                    default_dict[u'ApplicationType'] = u'Oncomine_RNA_Fusion'
                    default_dict[u'cellularityPct'] = str(sampleData[bc][5]).decode('unicode-escape')
                    default_dict[u'tag_isFactoryProvidedWorkflow'] = u'true'
                    default_dict[u'Workflow'] = workflow_R.decode('unicode-escape')

        plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"].append(default_dict)

    #Update the plan with the new data
    resp, content = h.request( torrent_host + plan_uri + "?format=json", "PUT", json.dumps( plan_dict ) )
    print resp

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

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    #Get Pool URI, ShortID of the RunPlan , SampleTubeLabel and ChipType
    PoolURI, shortID , SampleTubeLabel , chipType , torrentServer = getPoolURI()
    
    #Get artifacts from pool
    arts = getNonPooledArtifacts(PoolURI)

    #Get information from the artifacts
    SampleDict = getInfo(PoolURI, arts)

    #Get the Paired information
    SampleDictUpdated = UpdateSetID(SampleDict)

    #Get workflow
    workflow_DR, workflow_D, workflow_R = getWorkflow(chipType)

    #Update the Run Plan with sample information
    updateTorrentRunPlan( shortID, SampleTubeLabel, torrentServer, SampleDictUpdated, workflow_DR, workflow_D, workflow_R )

if __name__ == "__main__":
    main()
