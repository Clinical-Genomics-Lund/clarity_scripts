import sys
import csv
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""
api = None


WellPlate =  [ 'A01' , 'A02' , 'A03' , 'A04' , 'A05' , 'A06' , 'A07' , 'A08' , 'A09' , 'A10' , 'A11' , 'A12' ,
               'B01' , 'B02' , 'B03' , 'B04' , 'B05' , 'B06' , 'B07' , 'B08' , 'B09' , 'B10' , 'B11' , 'B12' ,
               'C01' , 'C02' , 'C03' , 'C04' , 'C05' , 'C06' , 'C07' , 'C08' , 'C09' , 'C10' , 'C11' , 'C12' ,
               'D01' , 'D02' , 'D03' , 'D04' , 'D05' , 'D06' , 'D07' , 'D08' , 'D09' , 'D10' , 'D11' , 'D12' , 
               'E01' , 'E02' , 'E03' , 'E04' , 'E05' , 'E06' , 'E07' , 'E08' , 'E09' , 'E10' , 'E11' , 'E12' ,
               'F01' , 'F02' , 'F03' , 'F04' , 'F05' , 'F06' , 'F07' , 'F08' , 'F09' , 'F10' , 'F11' , 'F12' , 
               'G01' , 'G02' , 'G03' , 'G04' , 'G05' , 'G06' , 'G07' , 'G08' , 'G09' , 'G10' , 'G11' , 'G12' , 
               'H01' , 'H02' , 'H03' , 'H04' , 'H05' , 'H06' , 'H07' , 'H08' , 'H09' , 'H10' , 'H11' , 'H12' ]

def setupGlobalsFromURI( uri ):

   global HOSTNAME
   global VERSION
   global BASE_URI

   tokens = uri.split( "/" )
   HOSTNAME = "/".join(tokens[0:3])
   VERSION = tokens[4]
   BASE_URI = "/".join(tokens[0:5]) + "/"               

def getOutputArtifacts():
    
    URI = re.sub("http://localhost:9080", HOSTNAME , args[ "stepURI" ])
    pURI = URI + "/placements"
    dURI = URI + "/details"
    
    dDOM = parseString( api.GET(dURI) )

    pDOM = parseString( api.GET(pURI) )
    pMaps = pDOM.getElementsByTagName( "output-placement" )

    for pMap in pMaps:
        outputURI = pMap.getAttribute( "uri" )
        outputDOM = parseString(api.GET( outputURI ))

        well = outputDOM.getElementsByTagName( "value" )[0].firstChild.data
        letter = well[0]
        num = int(well[2:])
        if num < 10 :
            num = '0' + str(num) 

        well = letter + str(num)

        limsID = outputDOM.getElementsByTagName( "sample")[0].getAttribute("limsid")
        SampleID = outputDOM.getElementsByTagName( "name" )[0].firstChild.data


        sampleURI = outputDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
        sampleDOM = parseString(api.GET( sampleURI ))
        s_analysis = api.getUDF( sampleDOM, 'Analysis' )
        if s_analysis : 
            analysis = s_analysis
        
        sampleName = limsID + "_" + SampleID
        
        outputArtifacts[well] = sampleName

    return outputArtifacts , analysis

def main():

    global api
    global args
    global outputArtifacts

    args = {}
    outputArtifacts = {}

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

    setupGlobalsFromURI( args[ "stepURI" ] )
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    outputArtifatcts , analysis= getOutputArtifacts() 
    
    #Adjust for assay

    if 'KIT' in analysis : 
        analysis = 'KIT'
        Ch1_Target = 'Variant (FAM)'
        Ch2_Target = 'WT (HEX)'
        Expt_BG_Color = '255_0_0_255'

    elif 'EGFR' in analysis :
        analysis = 'EGFR'
        Ch1_Target = 'EGFR mut'
        Ch2_Target = 'EGFR wt'
        Expt_BG_Color = '255_255_140_0'
        
    else: 
        'Assay must be KIT or EGFR' 
        sys.exit(255)

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out, delimiter=',', quotechar="\'")

    writer.writerow( ('Well', 'Sample', 'Ch1 Target', 'Ch1 Target Type', 'Ch2 Target', 'Ch2 Target Type' , 'Experiment', 'Expt Type', 'Expt FG Color' ,'Expt BG Color', 'ReferenceCopyNumber', 'TargetCopyNumber', 'ReferenceAssayNumber', 'TargetAssayNumber', 'ReactionVolume', 'DilutionFactor', 'Supermix', 'Cartridge', 'Expt Comments' ))
    
    for well in WellPlate :
        if well in outputArtifatcts.keys() : 
            writer.writerow((well, outputArtifacts[well], Ch1_Target ,'Unknown' ,Ch2_Target,'Unknown','ABS','Absolute Quantification','255_255_255_255', Expt_BG_Color, '2', '1', '1', '1', '20', '1', 'ddPCR Supermix for Probes (no dUTP)', '', '' ))
        
        else:
            writer.writerow((well, "", Ch1_Target ,'Unknown' ,Ch2_Target,'Unknown','ABS','Absolute Quantification','255_255_255_255', Expt_BG_Color, '2', '1', '1', '1', '20', '1' , 'ddPCR Supermix for Probes (no dUTP)', '', '' ))

    f_out.close()

if __name__ == "__main__":
    main()
