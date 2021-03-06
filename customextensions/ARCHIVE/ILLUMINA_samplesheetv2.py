import sys
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import datetime
from GetSampleInfoForSampleSheet import getMICROinfo, getNIPTinfo, getMYELOIDinfo, getEXOMEinfo

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

def getSampleSheetInfo( planID, Library , instrument):
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
    if "Clarigo NIPT Analys" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getNIPTinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, instrument)

    if "Myeloisk Panel" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getMYELOIDinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument)
    
    if "Mikrobiologi" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getMICROinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument)

    if "SureSelectXTHS" in sampleUDFs["Analysis"] :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getEXOMEinfo(planID, LibraryDOM, LibraryName, Index, sampleLimsID, sampleUDFs, instrument)


    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description

def getInputLibraries(planID):
    iLibraries = []
    PlanDetailsURI = "https://mtapp046.lund.skane.se/api/v2/steps/" + planID + "/details"
    PlanDetailsDOM = parseString( api.GET(PlanDetailsURI) )

    IOMaps = PlanDetailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        if iURI not in iLibraries:
            iLibraries.append( iURI)

    instrument_readLength_readType = api.getUDF(PlanDetailsDOM, "Instrument_ReadLength_ReadType")
    instrument = instrument_readLength_readType.split("_")[0]
    readLength = instrument_readLength_readType.split("_")[1]
    readType = instrument_readLength_readType.split("_")[2]

    return iLibraries, instrument, readLength, readType

def getplanID():
    
    DetailsURI = HOSTNAME + "/api/v2/steps/" + args[ "stepLimsID" ] + "/details"
    DetailsDOM = parseString( api.GET(DetailsURI) )
    planID = api.getUDF(DetailsDOM, "planID")
        
    return planID

def main():

    global api
    global args

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:f:")

    for o,p in opts:
        if o == '-l':
            args[ "stepLimsID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-f':
            args[ "outputfile" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )
    
    planID = getplanID()
    iLibraries, instrument, readLength, readType = getInputLibraries(planID)
    #readLength = int(readLength)
    Date = now.strftime("%Y-%m-%d")
    f_out = open(args[ "outputfile" ] + '.csv', 'w+')

    #########################
    # CHANGE BACK LATER
    #########################
    #if readType == "Paired" :
    #    f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength +1 ) + '\n' + str(readLength + 1 ) + '\n\n' + '[Data]\n')
    #elif readType == "Single" :
    #    f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + str(readLength +1) + '\n\n' + '[Data]\n')
    #else:
    #    print "Read Type must be Paired or Single from the planning step with ID " , planID
    #    sys.exit(255)

    f_out.write('[Header]\nExperiment Name,' + planID + '\nDate,' + Date + '\n\n[Reads]\n' + '150' + '\n' + '150' + '\n\n')
    f_out.write('[Settings]\n' + 'Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA' + '\n' + 'AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT' + '\n\n' + '[Data]' + '\n')
    f_out.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\n')

    for Library in iLibraries :
        SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description = getSampleSheetInfo( planID, Library, instrument )
        f_out.write(SampleID + ",,,," + I7_ID + "," + I7_Index + "," + I5_ID + "," + I5_Index + "," + SampleProj_Description + "\n")     
    
    f_out.close()

if __name__ == "__main__":
    main()
