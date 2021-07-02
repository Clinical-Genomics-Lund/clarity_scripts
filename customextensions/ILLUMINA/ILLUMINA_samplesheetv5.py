import sys
import getopt
import datetime
from GetSampleInfoForSampleSheetv4 import getMICROinfo, getMYELOIDinfo, getEXOMEinfo, getRNASEQinfo, getTWISTinfo, gethumanWGSinfo, getSARSinfo, getNIPTinfo
import re
from genologics.lims import *
from genologics.entities import *

def getI7_I5_Index(Index) : 
    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)

    return I7_Index , I5_Index

def getIndex(action, Index, instrument, kitVersion) : 
    if action == 'twist' : 
        #Index Example NEW: Duplex41 A06(GAAGTTGG-GTTGTTCG)
        I7_ID = Index.split(' ')[0]
        I5_ID = Index.split(' ')[0]
        
        I7_Index, I5_Index = getI7_I5_Index(Index)

    elif action == 'micro':
        #Index Example: A701-A503 (ATCACGAC-TGTTCTCT)
        I7_ID = Index.split('-')[0]
        I5_ID = re.search(r'\-(.*)\s', Index).group(1)

        I7_Index, I5_Index = getI7_I5_Index(Index)

    elif action == 'RNAseq' :
        #Index Example: A03 UD00001 (ATCACGAC-TGTTCTCT)
        I7_ID = Index.split(' ')[1]
        I5_ID = Index.split(' ')[1]

        I7_Index, I5_Index = getI7_I5_Index(Index)

    elif action == 'myeloid': 
        #Index Example: A701-A503 (ATCACGAC-TGTTCTCT)
        I7_ID = Index.split('-')[0]
        I5_ID = re.search(r'\-(.*)\s', Index).group(1)
        
        I7_Index, I5_Index = getI7_I5_Index(Index)

    elif action == 'humanWGS':
        #Index Example: "D09 UDI0068 (CCTTCACC-GACGCTCC)"
        I7_ID = Index.split(' ')[1]
        I5_ID = Index.split(' ')[1]
        
        I7_Index, I5_Index = getI7_I5_Index(Index)

    elif action == 'sureselect' :
        #Index Example: A01 (GTCTGTCA)
        I7_ID = Index.split(' ')[0]
        I5_ID = "MolBC"
        
        I7_Index = re.search(r'\s\((.*)\)$', Index).group(1)
        I5_Index = "NNNNNNNNNN"

    elif action == 'IDPT' :
        #Index Example: 1A UDP0001 (CCTTCACCCC-GACGCTCCTT)
        I7_ID = Index.split(' ')[1]
        I5_ID = I7_ID

        I7_Index, I5_Index = getI7_I5_Index(Index)

    elif action == "nipt" :
        #Index Example: A3 p707-p504 (ACTGCCAT-CGATATGA)
        I7_ID = Index.split(' ')[1].split('-')[0]
        I5_ID = Index.split(' ')[1].split('-')[1]

        I7_Index, I5_Index = getI7_I5_Index(Index)

    if "NextSeq" in instrument or "MiniSeq" in instrument or "v1.5" in kitVersion:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    return I7_ID, I7_Index, I5_ID, I5_Index

def getAdapter(sampleData) : 
    adapter1Dict = {
        "Microbiology" : "CTGTCTCTTATACACATCT" , 
        "Myeloid" : "CTGTCTCTTATACACATCT" , 
        "SureSelectXTHS" : "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA" , 
        "TruSeqStrandedmRNA" : "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA" ,
        "TWIST" : "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA" ,
        "TruSeqWGS" : "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
        "SarsIDPT" : "CTGTCTCTTATACACATCT",
        "MicrobiologyIDPT" : "CTGTCTCTTATACACATCT",
        "MicrobiologyIDPT-CTG" : "CTGTCTCTTATACACATCT",
        "NIPT" : ""
        }

    adapter2Dict = {
        "Microbiology" : "CTGTCTCTTATACACATCT" ,
        "Myeloid" : "CTGTCTCTTATACACATCT" ,
        "SureSelectXTHS" : "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT" ,
        "TruSeqStrandedmRNA" : "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT" ,
        "TWIST" : "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT", 
        "TruSeqWGS" : "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
        "SarsIDPT" : "",
        "MicrobiologyIDPT" : "",
        "MicrobiologyIDPT-CTG" : "",
        "NIPT" : ""
        }

    adapter1 = set()
    adapter2 = set()
    for pool in sampleData.keys() : 
        adapter1.add(adapter1Dict[pool])
        adapter2.add(adapter2Dict[pool])

    adapter1 = "+".join(adapter1)
    adapter2 = "+".join(adapter2)

    return adapter1 , adapter2 

def writeheader(f_out, planID, Date, readType, readLength, adapter1, adapter2, sampleData) : 
    #Header
    f_out.write('[Header]\nExperiment Name,' + planID + '\n') 
    #Date
    f_out.write('Date,' + Date + '\n\n') 
    #Reads
    if readType == "Paired" :
        if sampleData.keys()[0] == "SureSelectXTHS" : 
            f_out.write('[Reads]\n' + str(readLength) + '\n' + str(readLength) + '\n\n' )
        elif "IDPT" in sampleData.keys()[0]:
            f_out.write('[Reads]\n' + str(readLength - 1) + '\n' + str(readLength - 1) + '\n\n' )
        else: 
            f_out.write('[Reads]\n' + str(readLength + 1) + '\n' + str(readLength + 1) + '\n\n' )
    elif readType == "Single" :
        f_out.write('[Reads]\n' + str(readLength +1) + '\n\n')
    else:
        print "Read Type must be Paired or Single from the normalization step with ID " , planID
        sys.exit(255)
    #Adapter
    f_out.write('[Settings]\n' )
    f_out.write('Adapter,' + adapter1 + '\n') 
    if adapter2 != "":
        f_out.write('AdapterRead2,' + adapter2 + '\n\n' ) 
    else:
        f_out.write( '\n' )
    #Column headers
    f_out.write('[Data]' + '\n')
    f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')

def fixName(name) : 
    name = name.replace("_", "-")
    name = name.replace(" ", "-")
    name = name.replace(".", "-")
    name = name.replace("/", "-")
    name = name.replace("*", "-")
    return name 
    
def getTWISTLibraries( containerID , lims) :
    container = Container(lims, id = containerID) 
    poolArtInContainer = container.placements['1:1']
    parentProcessID = poolArtInContainer.parent_process.id
    parentProcessStep = Step(lims, id = parentProcessID ) 
    parentProcessStepPools = parentProcessStep.step_pools.get_pools()
    
    for pool in parentProcessStepPools:
        pName =  pool['name']
        if containerID in pName :        
            artifacts = pool['inputs']

    return artifacts

def getIDPTlibraries( containerID , lims) :
    container = Container(lims, id = containerID)
    poolArtInContainer = container.placements['1:1']
    parentProcessID = poolArtInContainer.parent_process.id
    parentProcessStep = Step(lims, id = parentProcessID )
    parentProcessStepPools = parentProcessStep.step_pools.get_pools()

    for pool in parentProcessStepPools:
        pName =  pool['name']
        if containerID in pName :
            artifacts = pool['inputs']

    return artifacts


def getSampleSheetInfo( planID, library , instrument, kitVersion):
    LibraryInfo = {}
    libraryName = library.name
    libraryName = fixName(libraryName) 
    
    #Get Sample info
    sampleLimsID = library.samples[0].id
    sampleUDFs = {}
    for item in library.samples[0].udf.items(): 
        sampleUDFs[item[0]] = item[1]

    #Fix paired sample
    if "Paired Sample Name" in sampleUDFs.keys() : 
        sampleUDFs["Paired Sample Name"] = fixName(sampleUDFs["Paired Sample Name"])
    
    #Get Index info
    Index = library.reagent_labels[0]

    #Find out what type of sample from Analysis field
    action_map = {
        'myeloid': getMYELOIDinfo,
        'micro': getMICROinfo,
        'sureselect' : getEXOMEinfo, 
        'RNAseq' : getRNASEQinfo, 
        'twist' : getTWISTinfo , 
        'humanWGS' : gethumanWGSinfo , 
        'sars' : getSARSinfo,
        'nipt' : getNIPTinfo
        }

    analysis = sampleUDFs["Analysis"]
    res = [probe for probe in ["GMSMyeloid",
                               "HereditarySolid",
                               "clinicalWES",
                               "GMSLymphoma",
                               "SciLifePanCancer",
                               "GMSSolidTumorv",
                               "MODY" ] if(probe in analysis)]
    if bool(res) == True:
        action = 'twist'
    elif "IDPT" in analysis:
        action = 'IDPT'
    elif "Myeloisk Panel" in analysis:
        action = 'myeloid'
    elif "Microbiology" in analysis:
        action = "micro"
    elif "SureSelectXTHS" in analysis:
        action = 'sureselect'
    elif "mRNA" in analysis:
        action = 'RNAseq'
    elif "TruSeq DNA PCR free" in analysis:
        action = 'humanWGS'
    elif "NIPT" in analysis:
        action = 'nipt'
    else: 
        print "No data to get for sample " , libraryName
        sys.exit(255)

    I7_ID, I7_Index, I5_ID, I5_Index = getIndex(action , Index, instrument , kitVersion) 

    if "Microbiology" in analysis:
        action = "micro"
    elif "Sars" in analysis:
        action = "sars"

    SampleID, SampleProj_Description = action_map[action](planID, library, libraryName, sampleLimsID, sampleUDFs)

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description

def getInputLibraries(stepPools, lims, sampleData):

    for pool in stepPools:
        pName = pool['name'] 
        #example name: TWISTHereditarySolid_27-88415_122-122951
        pAnalysis = pName.split("_")[0]

        if pAnalysis == "NexteraQAML" or pAnalysis == "TruSightMyeloid" :
            pAnalysis = "Myeloid"

        if "TWIST" in pAnalysis:
            containerID = pool['inputs'][0].name.split("_")[1]
            pAnalysis = "TWIST"

        if "IDPT" in pAnalysis:
            containerID = pool['inputs'][0].name.split("_")[1]

        if pAnalysis not in sampleData.keys() :
            sampleData[pAnalysis] = []

        #Loop over pool contents
        if pAnalysis == "TWIST":
            artifacts = getTWISTLibraries( containerID, lims)
        elif "IDPT" in pAnalysis:
            artifacts = getIDPTlibraries( containerID, lims)
        else : 
            artifacts = pool[ "inputs" ]

        for a in artifacts :
            sampleData[pAnalysis].append(a)
    
    return sampleData

def main():
    global args
    args = {}
    opts , extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:v:")
    for o,p in opts:
        if o == '-b':
            args[ "BASEURI" ] = p
        elif o == '-u':
            args[ "USERNAME" ] = p
        elif o == '-p':
            args[ "PASSWORD" ] = p
        elif o == '-s':
            args[ "stepLimsID" ] = p
        elif o == '-v':
            args[ "kitVersion" ] = p

    BASEURI = args["BASEURI"].split('api')[0]
    lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
    lims.check_version()

    process = Process(lims,id= args[ "stepLimsID" ])
    sampleData = {}

    #Truseq WGS samples uses current step as planning step
    if process.type.id == "811" :
        sampleData["TruSeqWGS"] = []

        planID = args[ "stepLimsID" ]
        step = Step(lims,id= planID)
        inputs = process.all_inputs() 
        for input in inputs : 
            sampleData["TruSeqWGS"].append(input) 
    
    else: 
        planID = process.udf["planID"]
        step = Step(lims,id= planID)
        stepPools = step.step_pools.get_pools()
        #Get artifacts
        sampleData = getInputLibraries(stepPools, lims, sampleData)
    
    #Get instrument, readlength, readtype
    instrument = step.details.udf["Illumina kit"].split(" ")[0]
    ReadLength_ReadType = step.details.udf["ReadLength_ReadType"]
    readLength = ReadLength_ReadType.split("_")[0]
    readType = ReadLength_ReadType.split("_")[1]
    readLength = int(readLength)
    
    #Get Date
    now = datetime.datetime.now()
    Date = now.strftime("%Y-%m-%d")

    #Get file luid
    ss_arts = {}
    for out in process.all_outputs():
        if out.name == "SampleSheet" :
            ss_arts[out.id] = out
    ss_arts_ids = sorted( ss_arts.keys() ) 

    #SureSelect samples need own samplesheet (150 read length instead of 151?)
    sureSelect_sampleData = ""
    if "SureSelectXTHS" in sampleData.keys() :
        sureSelect_sampleData = {}
        sureSelect_sampleData["SureSelectXTHS"] = sampleData["SureSelectXTHS"]
        del sampleData["SureSelectXTHS"]
        
    #Write samplesheet (all other than SureSelect)
    if sampleData : 
        oFileName =  Date + "_SampleSheet.csv" 
        with open(oFileName, "w") as outputFile :
            adapter1 , adapter2 = getAdapter(sampleData)
            writeheader(outputFile, planID, Date, readType, readLength, adapter1, adapter2, sampleData) 
        
            for pool in sampleData.keys() :
                for library in sampleData[pool] :          
                    SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, library, instrument, args[ "kitVersion" ] )
                    outputFile.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + ",," + SampleProj_Description + "\n")

        lims.upload_new_file(ss_arts[ss_arts_ids[0]], oFileName)

    #Write samplesheet for SureSelect
    if sureSelect_sampleData : 
        oFileName =  Date +  "_SureSelect_SampleSheet.csv"
        with open(oFileName, "w") as outputFile :
            adapter1 , adapter2 = getAdapter(sureSelect_sampleData)
            writeheader(outputFile, planID, Date, readType, readLength, adapter1, adapter2, sureSelect_sampleData)

            for pool in sureSelect_sampleData.keys() :
                for library in sureSelect_sampleData[pool] :
                    SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, library, instrument, args[ "kitVersion" ] )
                    outputFile.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + ",," + SampleProj_Description + "\n")
        
        lims.upload_new_file(ss_arts[ss_arts_ids[1]], oFileName)

if __name__ == "__main__":
    main()
