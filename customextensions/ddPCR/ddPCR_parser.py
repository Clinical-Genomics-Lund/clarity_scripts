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
delim = ','

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
    "Ch1+Ch2+" : "Ch1+Ch2+",
    "Ch1+Ch2-" : "Ch1+Ch2-",
    "Ch1-Ch2+" : "Ch1-Ch2+" ,
    "Ch1-Ch2-" : "Ch1-Ch2-",
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

def findHeaderIndex(data) :
    index = 0
    for row in data[0:] :
        index += 1
        if row.split(delim)[0] == "Well" :
            return index

def parseinputFile():

    data = downloadfile( options.resultLUID )
    Header = findHeaderIndex(data)
    columnHeaders = data[Header -1].split( delim )
    #columnHeaders = data[HeaderRow -1].split( delim )

    if columnHeaders[0] != "Well" :
        print "Could not find header. Please check input file and/or parser script"
        sys.exit(255)
    #Get artifact UDFs
    results = {}
    for row in data[Header:]:
        values = row.split( delim )
        UDFresults = {}
        for column, UDF in artifactUDFMap.items():
            try : 
                UDFresults[ UDF ] = values[ columnHeaders.index( column ) ]
            except:
                pass

        well =  values[ MappingColumn - 1 ].replace('"', '')
        results[ well ] = UDFresults

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
        wellLetter = well[0]
        wellNumber = well[2:]

        if int(wellNumber) < 10 :
            well = wellLetter + "0" + wellNumber
        else :
            well = wellLetter + wellNumber

        try:
            if MapTo_ArtifactName:
                ArtifactUDFs = artifactUDFResults[ output_name ]    # Would need to change this line to input_name if the input artifact name is being matched to instead of output

            elif MapTo_WellLocation:
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
    newName = str( file_art_luid ) + ".csv"
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
