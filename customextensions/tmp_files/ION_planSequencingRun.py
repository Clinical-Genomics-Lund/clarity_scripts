import glsfileutil
import glsapiutil
from xml.dom.minidom import parseString
import getopt
import sys
import re
from collections import defaultdict
HOSTNAME = 'https://mtapp046.lund.skane.se'
api = None

def format(value):
    return str(round(value, 2))

def Normalization(InputAnalytes, TotalVolumePool, AnalysisDict, LoadingConc) :

    for sampleDict in InputAnalytes :
        LibraryVolume = (LoadingConc / AnalysisDict[sampleDict[sampleDict.keys()[0]]["Analysis"]] ) * (TotalVolumePool / (sampleDict[sampleDict.keys()[0]]["Concentration"] + sampleDict[sampleDict.keys()[0]]["Concentration1_20"]))
        
        if LibraryVolume < 2 :
            TotalVolumePool += 1
            return Normalization(InputAnalytes, TotalVolumePool, AnalysisDict, LoadingConc)
        else :
            sampleDict[sampleDict.keys()[0]]["PoolVolume"] = TotalVolumePool
            if sampleDict[sampleDict.keys()[0]]["Concentration"] > 0 :
                sampleDict[sampleDict.keys()[0]]["LibraryVolume"] = LibraryVolume
                sampleDict[sampleDict.keys()[0]]["DilutedLibraryVolume"] = 0
            else :
                sampleDict[sampleDict.keys()[0]]["LibraryVolume"] = 0
                sampleDict[sampleDict.keys()[0]]["DilutedLibraryVolume"] = LibraryVolume
    
    return InputAnalytes

def getPassedFailed(readDict, InputAnalytes_DNA, InputAnalytes_RNA, InputAnalytes_CF) :
    status = "PASSED"
    #Find out how many of each sample
    AnalysisDict = {}
    
    AnalysisDict["DNA"] = float(len(InputAnalytes_DNA))
    AnalysisDict["RNA"] = float(len(InputAnalytes_RNA))
    AnalysisDict["CF"] = float(len(InputAnalytes_CF))

    #Get factors
    AnalysisDict["DNAfactor"] = readDict["MinReadsDNAsample"] / readDict["MinReadsRNAsample"]
    AnalysisDict["RNAfactor"] = readDict["MinReadsRNAsample"] / readDict["MinReadsRNAsample"]
    AnalysisDict["CFfactor"] = readDict["MinReadsCFsample"] / readDict["MinReadsRNAsample"] 
    AnalysisDict["FactorSum"] = (AnalysisDict["DNA"] * AnalysisDict["DNAfactor"]) + (AnalysisDict["RNA"] * AnalysisDict["RNAfactor"]) + (AnalysisDict["CF"] * AnalysisDict["CFfactor"])

    #Check if warning is needed
    AnalysisDict["ReadsPerFactor"] = readDict["UsableReads"] / AnalysisDict["FactorSum"]

    #DNA
    if AnalysisDict["DNA"] > 0 :
        if ( AnalysisDict["ReadsPerFactor"] * AnalysisDict["DNAfactor"]) < readDict["MinReadsDNAsample"] :
            status = "FAILED"
    #RNA
    if AnalysisDict["RNA"] > 0 :
        if ( AnalysisDict["ReadsPerFactor"] * AnalysisDict["RNAfactor"]) < readDict["MinReadsRNAsample"] :
            status = "FAILED"
    #CF
    if AnalysisDict["CF"] > 0 :
        if ( AnalysisDict["ReadsPerFactor"] * AnalysisDict["CFfactor"]) < readDict["MinReadsCFsample"] :
            status = "FAILED"
    AnalysisDict["UsableReads" ] = readDict["UsableReads"]

    return status , AnalysisDict
    
def getReadInfo(chipType) :
    if chipType == "520" :
        readDict = {"UsableReads": float(7500000),
                    "MinReadsDNAsample" : float(466715),
                    "MinReadsRNAsample" : float(116565),
                    "MinReadsCFsample" : float(40000)}
    if chipType == "530" :
        readDict = {"UsableReads": float(20000000),
                    "MinReadsDNAsample" : float(466715),
                    "MinReadsRNAsample" : float(116565),
                    "MinReadsCFsample" : float(40000)}
    if chipType == "316" :
        readDict = {"UsableReads": float(3500000),
                    "MinReadsDNAsample" : float(466715),
                    "MinReadsRNAsample" : float(116565),
                    "MinReadsCFsample" : float(40000)}
    if chipType == "318" :
        readDict = {"UsableReads": float(4000000),
                    "MinReadsDNAsample" : float(466715),
                    "MinReadsRNAsample" : float(116565),
                    "MinReadsCFsample" : float(40000)}
    if chipType == "510" :
        readDict = {"UsableReads": float(3750000),
                    "MinReadsDNAsample" : float(466715),
                    "MinReadsRNAsample" : float(116565),
                    "MinReadsCFsample" : float(40000)}
    return readDict

def getInputOutput():
    InputAnalytes_DNA = []
    InputAnalytes_RNA = []
    InputAnalytes_CF = []

    AnalysisList = ["DNA", "RNA", "CF"]

    poolsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/pools"
    poolsDOM = parseString(api.GET(poolsURI))

    processURI = HOSTNAME + "/api/v2/processes/" + args[ "stepLimsID" ]
    processDOM = parseString(api.GET(processURI))

    pool = poolsDOM.getElementsByTagName( "pool" )
    if len(pool) != 1:
        print "Planning of sequencing run can only be performed for one chip at the time. You have chosen more than one ouput pool"
        processDOM = api.setUDF( processDOM, "Status", "FAILED" )
        r = api.PUT( processDOM.toxml().encode('utf-8'), processURI)
        sys.exit(255)
    else:
        poolURI = pool[0].getAttribute("output-uri")
        for inputLibrary in pool[0].getElementsByTagName("input"):
            iURI = inputLibrary.getAttribute( "uri" )
            iDOM = parseString(api.GET(iURI))
            temp = {}
            name = iDOM.getElementsByTagName( "name" )[0].firstChild.data
            temp[name] = {}
            temp[name]["Analysis"] = name.split('_')[1]

            if temp[name]["Analysis"] not in AnalysisList:
                print "SampleName must have DNA/RNA/CF as suffix"
                processDOM = api.setUDF( processDOM, "Status", "FAILED" )
                r = api.PUT( processDOM.toxml().encode('utf-8'), processURI)
                sys.exit(255)

            temp[name]["Concentration"] = float(api.getUDF( iDOM, "qPCR concentration (pM)" ))
            if not temp[name]["Concentration"]:
                print name , " does not have a qPCR concentration"
                processDOM = api.setUDF( processDOM, "Status", "FAILED" )
                r = api.PUT( processDOM.toxml().encode('utf-8'), processURI)
                sys.exit(255)
 
            if temp[name]["Concentration"] >= 2000 :
                temp[name]["Concentration1_20"] = (temp[name]["Concentration"]/ 20)
                temp[name]["Concentration"] = 0
            else:
                temp[name]["Concentration1_20"] = 0

            temp[name]["sampleLimsID"] = iDOM.getElementsByTagName("sample")[0].getAttribute("limsid")
            
            if temp[name]["Analysis"] == "DNA":
                InputAnalytes_DNA.append(temp)
            if temp[name]["Analysis"] == "RNA":
                InputAnalytes_RNA.append(temp)
            if temp[name]["Analysis"] == "CF":
                InputAnalytes_CF.append(temp)  
    
    return pool , InputAnalytes_DNA, InputAnalytes_RNA, InputAnalytes_CF , processDOM, processURI

def main():

    global api
    global args

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:c:l:f:")

    for o,p in opts:
        if o == '-s':
            args[ "stepLimsID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-c':
            args[ "chipType" ] = p
        elif o == '-l':
            args[ "loadingConcentration" ] = p
        elif o == '-f':
            args[ "outputFile" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )
    
    pool , InputAnalytes_DNA, InputAnalytes_RNA, InputAnalytes_CF , processDOM, processURI = getInputOutput()

    readDict = getReadInfo(args[ "chipType" ])
    
    status, AnalysisDict = getPassedFailed(readDict, InputAnalytes_DNA, InputAnalytes_RNA, InputAnalytes_CF)
    
    if status == "FAILED":
        processDOM = api.setUDF( processDOM, "Status", "FAILED" )
        api.PUT( processDOM.toxml().encode('utf-8'), processURI)
        print "Too many samples. Can not proceed"
        sys.exit(255)

    #Continue with library normalization
    InputAnalytes_DNA  = Normalization(InputAnalytes_DNA, float(20), AnalysisDict, float(args[ "loadingConcentration" ]))
    InputAnalytes_RNA  = Normalization(InputAnalytes_RNA, float(20), AnalysisDict, float(args[ "loadingConcentration" ]))
    InputAnalytes_CF  = Normalization(InputAnalytes_CF, float(20), AnalysisDict, float(args[ "loadingConcentration" ]))
    
    #Print dilutions to file
    f = open(args[ "outputFile" ], "w+")
    f.write("Normalization of Oncomine Focus Assay and CFTR Libraries.\n\n")

    #DNA
    if InputAnalytes_DNA :
        SumDNALibraries = 0
        f.write("#---------------------------------------- DNA POOL ----------------------------------------#\n")
        f.write("Combine the following DNA libraries at indicated volumes:\n\n")
        f.write("Sample Name\tSample LimsID\tUndiluted library (ul)\t1:20 Diluted library (ul)\n")
        for sample in InputAnalytes_DNA :
            f.write(sample.keys()[0] + "\t" + sample[sample.keys()[0]]["sampleLimsID"] + "\t" + format(sample[sample.keys()[0]]["LibraryVolume"]) + "\t" + format(sample[sample.keys()[0]]["DilutedLibraryVolume"]) + "\n")

            TotalPoolVolume = sample[sample.keys()[0]]["PoolVolume"]
            SumDNALibraries += (sample[sample.keys()[0]]["LibraryVolume"] + sample[sample.keys()[0]]["DilutedLibraryVolume"] )
        water = TotalPoolVolume - SumDNALibraries
        f.write("\nNuclease Free Water (ul): " + format(water) )
        f.write("\n\n")

    #RNA
    if InputAnalytes_RNA :
        SumRNALibraries = 0
        f.write("#---------------------------------------- RNA POOL ----------------------------------------#\n")
        f.write("Combine the following RNA libraries at indicated volumes:\n\n")
        f.write("Sample Name\tSample LimsID\tUndiluted library (ul)\t1:20 Diluted library (ul)\n")
        for sample in InputAnalytes_RNA :
            f.write(sample.keys()[0] + "\t" + sample[sample.keys()[0]]["sampleLimsID"] + "\t" + format(sample[sample.keys()[0]]["LibraryVolume"]) + "\t" + format(sample[sample.keys()[0]]["DilutedLibraryVolume"]) + "\n")

            TotalPoolVolume = sample[sample.keys()[0]]["PoolVolume"]
            SumRNALibraries += (sample[sample.keys()[0]]["LibraryVolume"] + sample[sample.keys()[0]]["DilutedLibraryVolume"] )
        water = TotalPoolVolume - SumRNALibraries
        f.write("\nNuclease Free Water (ul): " + format(water)  )
        f.write("\n\n") 

    #CF
    if InputAnalytes_CF :
        SumCFLibraries = 0
        f.write("#---------------------------------------- CF POOL ----------------------------------------#\n")
        f.write("Combine the following CF libraries at indicated volumes:\n\n")
        f.write("Sample Name\tSample LimsID\tUndiluted library (ul)\t1:20 Diluted library (ul)\n")
        for sample in InputAnalytes_CF :
            f.write(sample.keys()[0] + "\t" + sample[sample.keys()[0]]["sampleLimsID"] + "\t" + format(sample[sample.keys()[0]]["LibraryVolume"]) + "\t" + format(sample[sample.keys()[0]]["DilutedLibraryVolume"]) + "\n")

            TotalPoolVolume = sample[sample.keys()[0]]["PoolVolume"]
            SumCFLibraries += (sample[sample.keys()[0]]["LibraryVolume"] + sample[sample.keys()[0]]["DilutedLibraryVolume"] )
        water = TotalPoolVolume - SumCFLibraries
        f.write("\nNuclease Free Water (ul): " + format(water) )
        f.write("\n\n")

    #Combine DNA/RNA/CF pool
    f.write("#---------------------------------------- Combine pools ----------------------------------------#\n")
    f.write("Loading concentration (pM):\t" + str(float(args[ "loadingConcentration" ])) + "\n\n")

    f.write("Volume DNA pool (ul):\t" + format((25 * AnalysisDict["DNA"] * ( (AnalysisDict["DNAfactor"] * AnalysisDict["ReadsPerFactor"])/ AnalysisDict["UsableReads"] ) ) ) + "\n")
    f.write("Volume RNA pool (ul):\t" + format((25 * AnalysisDict["RNA"] * ( (AnalysisDict["RNAfactor"] * AnalysisDict["ReadsPerFactor"])/ AnalysisDict["UsableReads"] ) ) ) + "\n")
    f.write("Volume CF pool (ul):\t" + format((25 * AnalysisDict["CF"] * ( (AnalysisDict["CFfactor"] * AnalysisDict["ReadsPerFactor"])/ AnalysisDict["UsableReads"] ) ) ) + "\n")

    #Update status 
    processDOM = api.setUDF( processDOM, "Status", "PASSED" )
    response = api.PUT( processDOM.toxml().encode('utf-8'), processURI)
    
    print "Please open the XLS file and perform library normalization."
    
if __name__ == "__main__":
    main()
