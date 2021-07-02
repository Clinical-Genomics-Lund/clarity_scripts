# Based on example script from genologics
# This script parses lane.html file and copies QC values to preconfigured process UDFs
# Script is NextSeq specific (4 lanes)

import sys
import re
import os.path
from optparse import OptionParser
from xml.dom.minidom import parseString
import glsapiutil   # needed for api calls
import glsfileutil  # needed to download file

udfs_in_clarity = {"Yield (Gb)": u'Yield (MBases)',
        "% PF Clusters": u'% PFClusters',
        "% Bases >=Q30": u'% &gt;= Q30bases',
        "Mean Quality Score": u'Mean QualityScore',
        "Clusters (Raw)" : u'Clusters (Raw)',
        "Clusters (PF)": u'Clusters(PF)'}

def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')
    Parser.add_option('-r', "--reagentCartridge", action='store', dest='rCartridge')
    Parser.add_option('-o', "--outputLUID", action='store', dest='outputLUID') # Log file
    return Parser.parse_args()[0]

def get_clusterDensity(Dir) :
    RunCompletionStatus_path = "/mnt/lennart/" + Dir + "/RunCompletionStatus.xml"
    
    RunCom_CSV = downloadfile(RunCompletionStatus_path)
    searchObj = re.search(r"<ClusterDensity>(.*)</ClusterDensity>", RunCom_CSV[13])

    if searchObj :
        clusterDens = float(searchObj.group(1))
    else :
        print "Could not find cluster density in " + RunCompletionStatus_path
        sys.exit(255)
    return clusterDens

def downloadfile( file_path ):
    if os.path.isfile(file_path) :
        raw = open( file_path, "r")
        lines = raw.readlines()
        raw.close()
    else:
        print "No file with path " + file_path + " - run not finished yet?"

    return lines

def parse_lane_html(LB_HTML):

    LB_HTML = LB_HTML.replace("<br>","")
    LB_DOM = parseString( LB_HTML )
    tables = LB_DOM.getElementsByTagName( 'tr' )

#First Table
    columnnames1 = {}
    row_data1 = {}
    for each in range(len(tables[1].childNodes)):           #searching the row with the column names
        try:
            columnnames1[tables[1].childNodes[each].toxml()[4:-5]] = each
        except AttributeError:
            print 'Attribute error'                 # columnnames stores the row index and column name

#Second Table
    columnnames2 = {}
    for each in range(len(tables[3].childNodes)):           #serching the row with the column names
        try:
            columnnames2[tables[3].childNodes[each].toxml()[4:-5]] = each
        except AttributeError:
            print 'Attribute error'                 # columnnames stores the row index and column name  

    Q30_colIndex = columnnames2[u'% &gt;= Q30bases']
    Mean_Qual_Score_colIndex = columnnames2[u'Mean QualityScore']

    table1 = {"Mean QualityScore" : 0, "% &gt;= Q30bases" : 0} #table1 plus two columns from table2, columnnames =keys, values=dict values

    for row in range(len(tables)):
        row_data = {}
        
        for each in range(len(tables[row].childNodes)):
            row_data[each] = tables[row].childNodes[each].toxml()[4:-5] #dictionary with col index and values
            #Get info from table1
            if len(row_data) == len(tables[1].childNodes):
                if row == 2 :
                    for key in columnnames1.keys():
                        table1[key] = row_data[columnnames1[key]]
            #Get info from table 2
            if len(row_data) == len(tables[3].childNodes):
                if row != 3 :
                    table1['% &gt;= Q30bases'] += float(row_data[Q30_colIndex])
                    table1['Mean QualityScore'] += float(row_data[Mean_Qual_Score_colIndex])

    return table1

def pull_udf_values_into_lims(html_file, runDirectory):

    global resultsCSV

    ## downloadfile function only works when the script is running on the clarity server.
    resultsCSV = downloadfile( html_file )

    resultsCSV.pop(0) # remove doctype node
    resultsCSV.pop(1) # remove 'links' node

    table1 = parse_lane_html( "".join(resultsCSV) )

    clusterDensity = get_clusterDensity(runDirectory)
    
    logFile.write("ClusterDensity:" + str(clusterDensity) + "\n")

    # Get step/details URI and update UDFs
    processURI = re.sub("steps", "processes" , args.stepURI)
    processDOM = parseString( api.GET(processURI) )
    
    cleanTable1 = {}

    for udf, tableColumn in udfs_in_clarity.items() :
        if udf == "% PF Clusters" :
            clustersPF = table1[u'Clusters(PF)'].replace(",","") 
            clustersRaw = table1[u'Clusters (Raw)'].replace(",","") 
            cleanTable1[udf] = (float(clustersPF) / float(clustersRaw) ) *100
        elif udf == "Yield (Gb)" :
            yieldmb = table1[tableColumn].replace(",","")
            yieldgb = float(yieldmb)*.001 
            cleanTable1[udf] = yieldgb
        elif udf == "% Bases >=Q30" :
            cleanTable1[udf] = float(table1[tableColumn]) /4
        elif udf == "Mean Quality Score" :
            cleanTable1[udf] = float(table1[tableColumn]) /4
        else :
            cleanTable1[udf] = int(table1[tableColumn].replace(",",""))
    
    for udf in cleanTable1.keys() :
        api.setUDF( processDOM, udf, cleanTable1[udf] )

    api.setUDF( processDOM, "Run directory", runDirectory)
    api.setUDF( processDOM, "Cluster density", clusterDensity)
    rXML = api.PUT( processDOM.toxml().encode('utf-8'), processURI)
    
    rDOM = parseString( rXML )
    nodes = rDOM.getElementsByTagName( "udf:field" )
    logFile.write(rDOM.toxml().encode('utf-8'))

    if len(nodes) > 0:
        print( "Success.")
    else:
        #Something is wrong
        print rXML
        sys.exit(255)

def getInstrument(detailsURI) :
    detailsDOM = parseString( api.GET(detailsURI) )
    try:
        instrument = detailsDOM.getElementsByTagName( "instrument" )[0].firstChild.data
    except :
        print "Please choose instrument"
        sys.exit(255)
        
    if "Gudrun" in instrument :
        instrumentID = instrument.split("(")[1]
        instrumentID = instrumentID.split(")")[0]
        instrument = "NextSeq2"
    elif "Margit" in instrument :
        instrumentID = instrument.split("(")[1]
        instrumentID = instrumentID.split(")")[0]
        instrument = "NextSeq1"
    else :
        print "Did not find NextSeq name Gudrun or Margit"
        sys.exit(255)
    return instrument, instrumentID

def main():

    global args
    args = setupArguments()

    global api
    api = glsapiutil.glsapiutil2()
    api.setURI( args.stepURI )
    api.setup( args.username, args.password )

    global FH # filehandler
    FH = glsfileutil.fileHelper()
    FH.setAPIHandler( api )
    FH.setAPIAuthTokens( args.username, args.password )
    
    #Log file
    global logFile
    logFile = open(args.outputLUID, "w+")
    
    #Get Instrument (NextSeq 1 or NextSeq2)
    detailsURI  = args.stepURI + "/details"
    instrument, instrumentID = getInstrument(detailsURI)

    #Find out run directory by searching for reagent cartridge ID in the RunParameters file
    search_path = "/mnt/lennart/" + instrument + "/"
    search_file_name = "/RunParameters.xml"
    search_str = "<SerialNumber>" + args.rCartridge + "</SerialNumber>"  

    found_directory = ""

    for fname in os.listdir(search_path) :
        if os.path.isfile(search_path + fname + search_file_name) :
            fo = open(search_path + fname + search_file_name)
            # Read the first line from the file
            line = fo.readline()
            line_no = 1
            
            # Rread line by line
            while line :
                # Search for string in line
                index = line.find(search_str)
                if ( index != -1) :
                    found_directory = search_path + fname 
                    break
                elif (line_no == 37) :
                    break
                # Read next line
                line = fo.readline()
                line_no += 1

            #Close file
            fo.close()
        #Break loop if directory found
        if found_directory != "" :
            break
    
    logFile.write(found_directory + "\n")

    if (found_directory == "" ) :
        print "Could not find a NextSeq run with the provided reagent cartridge ID. Can not import run data. Run not finished yet?"
        sys.exit(255)

    #Get the html file to parse
    flowcell = found_directory[-9:]
    html_file_path = found_directory + "/Data/Intensities/BaseCalls/Reports/html/" + flowcell + "/all/all/all/lane.html"
    if not os.path.isfile(html_file_path):
        print "html file with QC data not found. Can not continue." , html_file_path
        sys.exit(255)

    #Get run directory
    runDirectory = re.sub("/mnt/lennart/", "", found_directory)

    #Parse lane.html file
    pull_udf_values_into_lims(html_file_path, runDirectory)
    
    #Close log file handler
    logFile.close()

if __name__ == "__main__":
    main()
