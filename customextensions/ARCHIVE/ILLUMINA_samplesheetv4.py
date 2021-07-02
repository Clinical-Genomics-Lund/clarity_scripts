import sys
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import datetime
from GetSampleInfoForSampleSheetv2 import getMICROinfo, getNIPTinfo, getMYELOIDinfo, getEXOMEinfo, getRNASEQinfo, getTWISTinfo

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None
now = datetime.datetime.now()

# Get UDFs from a dom into a dict
def get_UDFs(dom):
    udf_data = {}
    elements = dom.getElementsByTagName( "udf:field" )
    for udf in elements:
        udf_data[ udf.getAttribute("name") ] = udf.firstChild.data

    return udf_data

def getTWISTLibraries( containerID) :
    containerURI = "https://mtapp046.lund.skane.se/api/v2/containers/" + containerID
    containerDOM = parseString( api.GET(containerURI) )
    
    placementURI = containerDOM.getElementsByTagName( "placement" )[0].getAttribute( "uri" )
    placementDOM = parseString( api.GET(placementURI) )
    
    ppURI = placementDOM.getElementsByTagName( "parent-process" )[0].getAttribute( "uri" )
    ppPoolURI = "https://mtapp046.lund.skane.se/api/v2/steps/" + ppURI.split("/")[-1] + "/pools"
    ppPoolDOM = parseString( api.GET(ppPoolURI) )

    pools = ppPoolDOM.getElementsByTagName( "pool" )
    for pool in pools:
        pName =  pool.getAttribute( "name" )
        if containerID in pName :        
            artifacts = pool.getElementsByTagName( "input" )

    return artifacts


def getSampleSheetInfo( planID, Library , instrument, kitVersion):
    LibraryInfo = {}
    LibraryDOM = parseString( api.GET(Library) )
    LibraryName = LibraryDOM.getElementsByTagName("name")[0].firstChild.data
    

    #Get Sample info
    sampleURI = LibraryDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
    sampleLimsID = LibraryDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
    sampleDOM = parseString( api.GET(sampleURI) )
    sampleUDFs = get_UDFs(sampleDOM)
    
    #Get Index info
    Index = LibraryDOM.getElementsByTagName( "reagent-label" )[0].getAttribute("name") 
    #Find out what type of sample from Analysis field
    if "Clarigo NIPT" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getNIPTinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, instrument)

    if "Myeloisk Panel" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getMYELOIDinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument)
    
    if "Microbiology" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getMICROinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument, kitVersion)

    if "SureSelectXTHS" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getEXOMEinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument)

    if "TruSeq Stranded mRNA" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getRNASEQinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument, kitVersion)

    if "GMSMyeloid" in sampleUDFs["Analysis"] or "HereditarySolid" in sampleUDFs["Analysis"] or "clinicalWES" in sampleUDFs["Analysis"] or "GMSLymphoma" in sampleUDFs["Analysis"] or "SciLifePanCancer" in sampleUDFs["Analysis"] or "GMSSolidTumorv2.0" in sampleUDFs["Analysis"] or "GMSSolidTumorv1.0" in sampleUDFs["Analysis"]:
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getTWISTinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument, kitVersion)

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description

def getInputLibraries(planID):
    sampleData = {}
    poolURI = "https://mtapp046.lund.skane.se/api/v2/steps/" + planID + "/pools"
    poolDOM = parseString( api.GET(poolURI) )

    pools = poolDOM.getElementsByTagName( "pool" )
    for pool in pools:
        pName =  pool.getAttribute( "name" )
        pAnalysis = pName.split("_")[0]

        if pAnalysis == "NexteraQAML" or pAnalysis == "TruSightMyeloid" :
            pAnalysis = "Myeloid"

        if pAnalysis == "TWISTMyeloid" or pAnalysis == "TWISTHereditarySolid" or pAnalysis == "TWISTClinicalWES" or pAnalysis == "TWISTLymphoma" or pAnalysis == "TWISTPanCancer" or pAnalysis == "TWISTSolidTumor": 
            pInputURI = pool.getElementsByTagName( "input" )[0].getAttribute( "uri" )
            pInputDOM = parseString(api.GET(pInputURI))
            containerID =  pInputDOM.getElementsByTagName("name")[0].firstChild.data.split("_")[1]
            pAnalysis = "TWIST"

        if pAnalysis not in sampleData.keys() :
            sampleData[pAnalysis] = []
        
        #Loop over pool contents
        if pAnalysis == "TWIST":
            artifacts = getTWISTLibraries( containerID)
        else : 
            artifacts = pool.getElementsByTagName( "input" )

        for a in artifacts :
            aURI =  a.getAttribute( "uri" )
            sampleData[pAnalysis].append(aURI)

    detailsURI = "https://mtapp046.lund.skane.se/api/v2/steps/" + planID + "/details"
    detailsDOM= parseString( api.GET(detailsURI) )

    #Get instrument, readlength, readtype
    instrument = api.getUDF(detailsDOM , "Illumina kit").split(" ")[0]
    ReadLength_ReadType = api.getUDF(detailsDOM , "ReadLength_ReadType")
    readLength = ReadLength_ReadType.split("_")[0]
    readType = ReadLength_ReadType.split("_")[1]
    
    return sampleData, instrument, readLength, readType

def getplanID():
    
    DetailsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/details"
    DetailsDOM = parseString( api.GET(DetailsURI) )
    planID = api.getUDF(DetailsDOM, "planID")
        
    return planID

def main():

    global api
    global args

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:v:")

    for o,p in opts:
        if o == '-l':
            args[ "stepLimsID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-v' :
            args[ "kitVersion" ] = p

    outputFilePlaceholders = extraparams[1:5]

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )
    
    planID = getplanID()

    sampleData, instrument, readLength, readType = getInputLibraries(planID)
    readLength = int(readLength)
    Date = now.strftime("%Y-%m-%d")

    #Placeholder index
    pools = sampleData.keys()
    placeholderIndex = {}
    if len(pools) > len(outputFilePlaceholders) :
        print "Too few output file placeholders. Please ask your systemadmin to increase the number of placeholders"
        sys.exit(255)

    for i in range(0,len(pools)) :
        placeholderIndex[pools[i] ] = i

    if (len(pools) == 3 ) and ( "TWIST" in pools and "TruSeqStrandedmRNA" in pools and "Microbiology" in pools ) :
        f_out = open(extraparams[1] + '_combined_SampleSheet.csv', 'w+')
        f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength +1 ) + '\n' + str(readLength + 1 ) + '\n\n' )
        f_out.write('[Settings]\n' + 'Adapter,CTGTCTCTTATACACATCT+AGATCGGAAGAGCACACGTCTGAACTCCAGTCA' + '\n' + 'AdapterRead2,CTGTCTCTTATACACATCT+AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT' + '\n\n' + '[Data]' + '\n')
        f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')
                                        
        #Write data content
        for Library in sampleData["TWIST"] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")
            
        for Library in sampleData["TruSeqStrandedmRNA"] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")

        for Library in sampleData["Microbiology"] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")

        f_out.close()


    elif (len(pools) == 2 ) and ( "TWIST" in pools and "TruSeqStrandedmRNA" in pools ) :
        f_out = open(extraparams[1] + '_combined_SampleSheet.csv', 'w+')
        f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength +1 ) + '\n' + str(readLength + 1 ) + '\n\n' )
        f_out.write('[Settings]\n' + 'Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA' + '\n' + 'AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT' + '\n\n' + '[Data]' + '\n')
        f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')

        #Write data content
        for Library in sampleData["TWIST"] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")

        for Library in sampleData["TruSeqStrandedmRNA"] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")

        f_out.close()

    elif (len(pools) == 2 ) and ( "TWIST" in pools and "Microbiology" in pools ) :
        f_out = open(extraparams[1] + '_combined_SampleSheet.csv', 'w+')
        f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength +1 ) + '\n' + str(readLength + 1 ) + '\n\n' )
        f_out.write('[Settings]\n' + 'Adapter,CTGTCTCTTATACACATCT+AGATCGGAAGAGCACACGTCTGAACTCCAGTCA' + '\n' + 'AdapterRead2,CTGTCTCTTATACACATCT+AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT' + '\n\n' + '[Data]' + '\n')
        f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')
        
        #Write data content
        for Library in sampleData["TWIST"] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")
            
        for Library in sampleData["Microbiology"] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")

        f_out.close()

    else: 

        for pool in pools :
            #Get placeholder
            f_out = open(outputFilePlaceholders[ placeholderIndex[pool]] + '_' + pool + '_SampleSheet.csv', 'w+')

            #Write Header
            if readType == "Paired" :
                if pool == "SureSelectXTHS" :
                    f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength) + '\n' + str(readLength) + '\n\n' )
                else: 
                    f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength +1 ) + '\n' + str(readLength + 1 ) + '\n\n' )

            elif readType == "Single" :
                f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength +1) + '\n\n')

            else:
                print "Read Type must be Paired or Single from the normalization step with ID " , planID
                sys.exit(255)


            #Write adapter settings
            if pool == "Myeloid" or pool == "Microbiology" :
                f_out.write('[Settings]\n' + 'Adapter,CTGTCTCTTATACACATCT' '\n\n' + '[Data]' + '\n')

            elif pool == "SureSelectXTHS" or pool == "TruSeqStrandedmRNA" or pool == "TWIST":
                f_out.write('[Settings]\n' + 'Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA' + '\n' + 'AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT' + '\n\n' + '[Data]' + '\n') 

            #Write data header
            f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')

            #Write data content
            for Library in sampleData[pool] :
                SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
                f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")
        
            f_out.close()

if __name__ == "__main__":
    main()
