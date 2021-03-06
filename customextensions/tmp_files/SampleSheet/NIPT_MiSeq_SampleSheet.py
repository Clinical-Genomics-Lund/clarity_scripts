import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import datetime

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
#count_steps is used to make sure that the correct analyte is used when a input pool contains only one sample
count_steps = 0
CACHE = {}
api = None
now = datetime.datetime.now()

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]

def DOMfromURI(URI) : 
    XML = api.getResourceByURI( URI )
    DOM = parseString( XML )
    return DOM    

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
    global count_steps
    count_steps += 1

    artifacts = []

    ## get the artifact
    paDOM = DOMfromURI(paURI)

    ## how many samples are associated with this artifact?
    Nodes = paDOM.getElementsByTagName( "sample" )
    if len( Nodes ) == 1 & (count_steps >2):
        artifacts.append( paURI )

    else:
        ##get the process that produced this artifact
        Nodes = paDOM.getElementsByTagName( "parent-process" )
        ppURI = Nodes[0].getAttribute( "uri" )
        ppDOM = DOMfromURI(ppURI)

        ## get the limsid of this artifact
        Nodes = paDOM.getElementsByTagName( "art:artifact" )
        aLimsid = Nodes[0].getAttribute( "limsid" )

        ## get the inputs that corresponds to this artifact
        inputs = getInputArtifacts( aLimsid, ppDOM )
        for input in inputs:
            arts = getNonPooledArtifacts( input )
            for art in arts:
                artifacts.append( art )

    return artifacts

def getSampleSheetInfo( arts ):
    SampleDict = {}
    Samples = []
    panel = ""

    for art in arts:
        tokens = art.split("?")
        art = tokens[0]
        artDOM = DOMfromURI(art)

        #Get Sample URI
        Nodes = artDOM.getElementsByTagName( "sample" )
        sampleURI = Nodes[0].getAttribute( "uri" )
        sampleDOM = DOMfromURI(sampleURI)

        #Save Sample LIMSID
        sampleLimsID = Nodes[0].getAttribute( "limsid" )
        Samples.append(sampleLimsID)
        SampleDict[sampleLimsID] = {}
        SampleDict[sampleLimsID].update({'SampleLimsID' : sampleLimsID })        

        #Save Sample Name  
        LibraryName = artDOM.getElementsByTagName("name")[0].firstChild.data
        SampleDict[sampleLimsID].update({'LibraryName' : LibraryName })

        #Get Reagent label
        ReagentLabels = artDOM.getElementsByTagName( "reagent-label" )
        for reagent in ReagentLabels:
            ReagentLabel = reagent.getAttribute("name")
            #A1 p704-p504 (CACCGGGA-CGATATGA)
            p7p5 = ReagentLabel.split(' ')[1]
            index7 = p7p5[0:2] + "-" + p7p5[2:4]
            index5 = p7p5[5:7] + "-" + p7p5[7:9]
            SampleDict[sampleLimsID].update({'index7' : index7})
            SampleDict[sampleLimsID].update({'index5' : index5 })
            i7_seq = re.search(r'\((.*)\-', ReagentLabel).group(1)
            SampleDict[sampleLimsID].update({'i7_seq' : i7_seq })
            i5_seq = re.search(r'[A|T|G|C]{8}\-(.*)\)', ReagentLabel).group(1)

            #Get reverse complement of Index 
            SampleDict[sampleLimsID].update({'i5_seq' : i5_seq })                           
        
    return Samples, SampleDict

def getPoolContents(inputPool):

    paURI = BASE_URI + "artifacts/" + inputPool
    arts = getNonPooledArtifacts( paURI )
    return  arts

def getInputOutputPools():
    
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    detailsDOM = DOMfromURI(detailsURI)

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iLimsid = Nodes[0].getAttribute( "limsid" )
        inputPools.append( iLimsid)
        Nodes = IOMap.getElementsByTagName( "output" )
        if (Nodes[0].getAttribute( "type" ) == "Analyte" ) :
            outputPools.append(Nodes[0].getAttribute( "limsid" ))
        
    return inputPools, outputPools

def main():

    global api
    global args
    global inputPools
    global outputPools
    global outputPool
    global count_steps

    args = {}
    inputPools = []
    outputPools = []
    outputPool = ""

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:f:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-f':
            args[ "outputfile" ] = p

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )
    
    ## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
    ## so let's get this show on the road!

    inputPools, outputPools = getInputOutputPools()
    # Make the content of the lists unique
    inputPools = list(set(inputPools))
    outputPools = list(set(outputPools) )
    # Make sure that the user has only one output pool
    if len(outputPools) > 1 :
        api.reportScriptStatus( args[ "stepURI" ], "ERROR", "Only one output pool is allowed")
    else : 
        outputPool = outputPools[0]
    Date = now.strftime("%Y-%m-%d")
    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    f_out.write('[Header]\nExperiment Name,' + Date + '_ClarigoNIPT\nDate,' + Date + '\nWorkflow,GenerateFASTQ\nApplication,FASTQ Only\nAssay,Multiplicom MASTR (MID 1-192)\nChemistry,Amplicon\n\n[Reads]\n76\n\n[Settings]\nCustomRead1PrimerMix,C1\nCustomIndexPrimerMix,C2\nReverseComplement,0\nAdapter,TGGAGAACAGTGACGATCGC\nAdapterRead2,TGGAGATGCTGCCGAGTCTT\n\n[Data]\n')

    f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')

    for inputPool in inputPools :
        count_steps = 0
        arts = getPoolContents(inputPool)
        Samples, SampleDict = getSampleSheetInfo( arts )
        for sample in Samples :
            f_out.write(SampleDict[sample]['SampleLimsID'] + "_" + SampleDict[sample]['LibraryName'] + ",,,," + SampleDict[sample]['index7'] + "," + SampleDict[sample]['i7_seq'] + "," + SampleDict[sample]['index5'] + "," + SampleDict[sample]['i5_seq'] + ",NIPT,nipt_" + SampleDict[sample]['LibraryName'] + "\n")     

    
    f_out.close()

if __name__ == "__main__":
    main()
