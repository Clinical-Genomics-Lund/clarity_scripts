import sys
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import datetime
from GetSampleInfoForSampleSheet_WGSv3 import getWGSinfo

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

    if "TruSeq DNA PCR free - WGS" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getWGSinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument, args[ "kitVersion" ])

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description

def getInputLibraries(planID):
    sampleData = {}
    sampleData["TruseqWGS"] = []

    detailsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/details"
    detailsDOM= parseString( api.GET(detailsURI) )

    #Loop over contents
    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        aURI = Nodes[0].getAttribute( "uri" )
        if aURI not in sampleData["TruseqWGS"]:
            sampleData["TruseqWGS"].append(aURI)

    #Get instrument, readlength, readtype
    instrument = "NovaSeq"
    ReadLength_ReadType = "150_Paired" 
    readLength = ReadLength_ReadType.split("_")[0]
    readType = ReadLength_ReadType.split("_")[1]

    return sampleData, instrument, readLength, readType

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

    outputFilePlaceholders = extraparams[2:5]

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )
    
    planID = args[ "stepLimsID" ].split("/")[-1]

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
        f_out.write('[Settings]\n' + 'Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA' + '\n' + 'AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT' + '\n\n' + '[Data]' + '\n') 

        #Write data header
        f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')

        #Write data content
        for Library in sampleData[pool] :
            SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument, args[ "kitVersion" ] )
            f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + ",," + SampleProj_Description + "\n")
            
        f_out.close()

if __name__ == "__main__":
    main()
