import sys
delim = ','
MapTo_ArtifactName = False
DEBUG = True

api = None
options = None
HeaderRow = 1

MapTo_WellLocation = True

if MapTo_WellLocation:      # only if MapTo_UDFValue is True
    UDFName = "Well"      # UDF name in Clarity

MappingColumn = 1      # In which column of the csv file will I find the above information? (Name / Well / UDF /ect.)

# What UDFs are we bringing into Clarity?
artifactUDFMap = {
    # "Column name in file" : "UDF name in Clarity",
    "Sample Name" : "Sample Name", 
    "Size(bp)" : "Size (bp)", 
    "Well" : "Well"
}
####### End Config #######

import csv 
import glsfileutil
import glsapiutil
from xml.dom.minidom import parseString
from optparse import OptionParser

file_lines = []

def limslogic():

    artifactUDFResults = parseinputFile()
    #if DEBUG: print artifactUDFResults

    stepdetails = parseString( api.GET( options.stepURI + "/details" ) ) #GET the input output map
    #print api.GET( options.stepURI + "/details" )
    resultMap = {}

    #outputArtifacts = {}
    for iomap in stepdetails.getElementsByTagName( "input-output-map"):
        output = iomap.getElementsByTagName( "output" )[0]
        if output.getAttribute( "output-generation-type" ) == 'PerInput':
            oURI = output.getAttribute( "uri" )
            oDOM = parseString( api.GET( oURI ) )
            oLimsID = oDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
            well = oDOM.getElementsByTagName( "value" )[0].firstChild.data
            #print(oLimsID, well)
            #outputArtifacts[oLimsID] = oDOM
            #print(oLimsID, well, '\n\n')
            #value = results[oLimsID]
            fragmentLength = artifactUDFResults[well][0]
            #print(fragmentLength)
            DOM = api.setUDF( oDOM, "Size (bp)", fragmentLength)  
            r = api.PUT( DOM.toxml().encode('utf-8'), oURI )


    
def findHeaderIndex(data) :
    index = 0
    for row in data[0:] :
        index += 1
        if row.split(delim)[0] == "Well" :
            return index

def parseinputFile():
    max_length = 6000 # the maximun length of fragment on the kit
    nullValues = [] #stor the wells with has no  fragment size reported.
    data = downloadfile( options.resultLUID )
    Header = findHeaderIndex(data)
    columnHeaders = data[Header -1].split( delim )
    #columnHeaders = data[HeaderRow -1].split( delim )

    if columnHeaders[0] != "Well" :
        print "Could not find header. Please check input file(alternate format) and/or parser script."
        sys.exit(255)
    
    results = {}
    for row in data[Header:]:
        
        values = row.split( delim )
        if values[3] == '' or int(values[3]) == max_length:
            continue

        SampleName = values[1]
        well = values[0][0] + ':' + values[0][1:]
        Size = int(values[3]) #It has to be the highest peak of fragment!

        if well not in results.keys() :
            results[well] = [Size, SampleName]
        elif  Size > results[well][0] :
            results[well] = [Size, SampleName]
    for well in results.keys():
        if  results[well][0] == 1:
            results[well][0] = ''
            nullValues.append(well) # for non reported samples
    #nullValues_str =  ', '.join(nullValues) 
    
    return results 
    


def downloadfile( file_art_luid ):

    newName = str( file_art_luid ) + '.csv'
    FH.getFile( file_art_luid, newName )
    raw = open( newName, "r")
    lines = raw.read().splitlines()
    raw.close
    return lines

     
def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')
    Parser.add_option('-r', "--resultLUID", action='store', dest='resultLUID')

    return Parser.parse_args()[0]

def main():

    global options
    options = setupArguments()
    global api
    api = glsapiutil.glsapiutil2()
    api.setURI( options.stepURI )
    api.setup( options.username, options.password )
    global FH
    FH = glsfileutil.fileHelper()
    FH.setAPIHandler( api )
    FH.setAPIAuthTokens( options.username, options.password )

    
    #sys.exit(255)   
    #parseinputFile()
    
    limslogic()

if __name__ == "__main__":
    main()
