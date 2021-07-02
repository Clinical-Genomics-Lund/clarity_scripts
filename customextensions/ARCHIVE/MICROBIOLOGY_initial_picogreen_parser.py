import logging
import sys
__author__ = 'dcrawford'
# Oct 13th 2016
# File Parsing Script
# This script is useful if a field in the file to be parsed matches exactly the input, or output artifact name, the well location, or an artifact UDF.

####### Configuration Section #######

# Which row in the file is the column headers?
#HeaderRow = 44

# How is file delimited? examples: ',' '\t'
delim = '\t'

# MAPPING MODE #
# What will we use to map the data to the artifacts in Clarity? ( set ONE of these to True )
MapTo_ArtifactName = False  # matches to name of output artifact
MapTo_WellLocation = True
MapTo_UDFValue = False

if MapTo_UDFValue:      # only if MapTo_UDFValue is True
    UDFName = "Well"      # UDF name in Clarity

MappingColumn = 1       # In which column of the csv file will I find the above information? (Name / Well / UDF /ect.)

# What UDFs are we bringing into Clarity?
artifactUDFMap = {
    # "Column name in file" : "UDF name in Clarity",
    "Single conc. (ng/ul)" : "Concentration (ng/ul)"
}
####### End Config #######

import glsfileutil
import glsapiutil
from xml.dom.minidom import parseString
from optparse import OptionParser
api = None
options = None

artifactUDFResults = {}
DEBUG = False #True

wellConverter = { "1:A" : "A1" , "2:A" : "B1" ,  "3:A" : "C1" , "4:A" : "D1" , "5:A" : "E1" , "6:A" : "F1" , "7:A" : "G1" , "8:A" : "H1" ,
                  "9:A" : "A2" , "10:A" : "B2" ,  "11:A" : "C2" , "12:A" : "D2" , "13:A" : "E2" , "14:A" : "F2" , "15:A" : "G2" , "16:A" : "H2" ,
                  "17:A" : "A3" , "18:A" : "B3" ,  "19:A" : "C3" , "20:A" : "D3" , "21:A" : "E3" , "22:A" : "F3" , "23:A" : "G3" , "24:A" : "H3" ,

                  "1:B" : "A4" , "2:B" : "B4" ,  "3:B" : "C4" , "4:B" : "D4" , "5:B" : "E4" , "6:B" : "F4" , "7:B" : "G4" , "8:B" : "H4" ,
                  "9:B" : "A5" , "10:B" : "B5" ,  "11:B" : "C5" , "12:B" : "D5" , "13:B" : "E5" , "14:B" : "F5" , "15:B" : "G5" , "16:B" : "H5" ,
                  "17:B" : "A6" , "18:B" : "B6" ,  "19:B" : "C6" , "20:B" : "D6" , "21:B" : "E6" , "22:B" : "F6" , "23:B" : "G6" , "24:B" : "H6" ,

                  "1:C" : "A7" , "2:C" : "B7" ,  "3:C" : "C7" , "4:C" : "D7" , "5:C" : "E7" , "6:C" : "F7" , "7:C" : "G7" , "8:C" : "H7" ,
                  "9:C" : "A8" , "10:C" : "B8" ,  "11:C" : "C8" , "12:C" : "D8" , "13:C" : "E8" , "14:C" : "F8" , "15:C" : "G8" , "16:C" : "H8" ,
                  "17:C" : "A9" , "18:C" : "B9" ,  "19:C" : "C9" , "20:C" : "D9" , "21:C" : "E9" , "22:C" : "F9" , "23:C" : "G9" , "24:C" : "H9" ,

                  "1:D" : "A10" , "2:D" : "B10" ,  "3:D" : "C10" , "4:D" : "D10" , "5:D" : "E10" , "6:D" : "F10" , "7:D" : "G10" , "8:D" : "H10" ,
                  "9:D" : "A11" , "10:D" : "B11" ,  "11:D" : "C11" , "12:D" : "D11" , "13:D" : "E11" , "14:D" : "F11" , "15:D" : "G11" , "16:D" : "H11" ,
                  "17:D" : "A12" , "18:D" : "B12" ,  "19:D" : "C12" , "20:D" : "D12" , "21:D" : "E12" , "22:D" : "F12" , "23:D" : "G12" , "24:D" : "H12" }

def findHeaderIndex(data) :
    index = 0
    for row in data[0:] :
        index += 1
        if row.split(delim)[0] == "Well positions" :
            return index

def parseinputFile():

    data = downloadfile( options.resultLUID )
    Header = findHeaderIndex(data)
    columnHeaders = data[Header -1].split( delim )
    
    if columnHeaders[0] != "Well positions" :
        print "Could not find header. Please check input file and/or parser script"
        sys.exit(255)

    #Get artifact UDFs
    results = {}
    for row in data[Header:]:
        values = row.split( delim) 

        UDFresults = {}
        for column, UDF in artifactUDFMap.items():
            try : 
                if values[ columnHeaders.index( column ) ][0:2] == "# " :
                    UDFresults[ UDF ] = values[ columnHeaders.index( column ) ][2:]
                else: 
                    UDFresults[ UDF ] = values[ columnHeaders.index( column ) ]
            except:
                pass
            results[ values[ MappingColumn - 1 ]] = UDFresults

    return results 

def limslogic():

    stepdetails = parseString( api.GET( options.stepURI + "/details" ) ) #GET the input output map

    artifactUDFResults = parseinputFile()
    if DEBUG: logging.info(artifactUDFResults)

    resultMap = {}

    for iomap in stepdetails.getElementsByTagName( "input-output-map" ):
        output = iomap.getElementsByTagName( "output" )[0]
        if output.getAttribute( "output-generation-type" ) == 'PerInput':
            resultMap[ output.getAttribute( "uri" ) ] = iomap.getElementsByTagName("input")[0].getAttribute( "uri" )
    # resultMap will map the artifact outputs to the artifact inputs

    output_artifacts = parseString( api.getArtifacts( resultMap.keys() ) )
    input_artifacts = parseString( api.getArtifacts( resultMap.values() ) )

    nameMap = {}
    for artDOM in input_artifacts.getElementsByTagName( "art:artifact" ):
        art_URI = artDOM.getAttribute( "uri" )
        nameMap[ art_URI.split("?")[0] ] = artDOM.getElementsByTagName( "name" )[0].firstChild.data

    for artDOM in output_artifacts.getElementsByTagName( "art:artifact" ):
        art_URI = artDOM.getAttribute( "uri" )
        input_name = nameMap[ resultMap[ art_URI.split("?")[0] ] ]
        output_name = artDOM.getElementsByTagName( "name" )[0].firstChild.data
        well = artDOM.getElementsByTagName( "value" )[0].firstChild.data

        try:
            if MapTo_ArtifactName:
                ArtifactUDFs = artifactUDFResults[ output_name ]    # Would need to change this line to input_name if the input artifact name is being matched to instead of output
            elif MapTo_WellLocation:
                #remove the : from the well ( if needed uncomment the following line )
                well = wellConverter[ well ]
                ArtifactUDFs = artifactUDFResults[ well ]

            elif MapTo_UDFValue:
                udfvalue = api.getUDF( artDOM, UDFName )
                #if DEBUG: logging.info( udfvalue)
                ArtifactUDFs = artifactUDFResults[ udfvalue ]

            #if DEBUG: logging.info(ArtifactUDFs)
            for UDF, value in ArtifactUDFs.items():
                api.setUDF( artDOM, UDF, value )
        except:
            pass

    if DEBUG: logging.info( output_artifacts.toxml())
    r = api.POST( output_artifacts.toxml(), api.getBaseURI() + "artifacts/batch/update" )
    
    #logging.info(r)
    print ('Done :) ')

def downloadfile( file_art_luid ):
    newName = str( file_art_luid ) + ".txt"
    FH.getFile( file_art_luid, newName )
    raw = open( newName, "r")
    lines = raw.readlines()
    raw.close
    return lines

def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')
    Parser.add_option('-r', "--resultLUID", action='store', dest='resultLUID')
    Parser.add_option('-l', "--logfileLUID", action='store', dest='logfileLUID')

    return Parser.parse_args()[0]

def main():

    global options
    options = setupArguments()
    global api
    api = glsapiutil.glsapiutil2()
    api.setURI( options.stepURI )
    api.setup( options.username, options.password )
    logging.basicConfig(filename= options.logfileLUID ,level=logging.DEBUG)
    global FH
    FH = glsfileutil.fileHelper()
    FH.setAPIHandler( api )
    FH.setAPIAuthTokens( options.username, options.password )

    limslogic()

if __name__ == "__main__":
    main()
