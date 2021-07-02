import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import xlsxwriter

HOSTNAME = ""
VERSION = ""
BASE_URI = ""
xrow = 0
xcol = 0
CACHE_IDS = []

#Convert kit selection to number of available reads
KitToReads = { 
               'NovaSeq S4 300' : 24000000000.0,} #changed from 20000000000.0 20201116


######Tapestation Option?
#Fragment size from Tapestation "Region 1 Average Size - bp" used when available. 

def visualization(f_out, k , data) :
    global xrow
    global cell_format_2dec
    
    lcol = 0
    f_out.write_string(xrow, lcol, data['labID'])
    lcol += 1
    f_out.write_string(xrow, lcol, k)
    lcol += 1
    f_out.write_string(xrow, lcol, data['well'])
    lcol += 1
    f_out.write_number(xrow, lcol, data['volumePerSample'], cell_format_2dec)
    lcol += 1
    xrow += 1

def normalization(f_out, data, totalReadSum, loadingConc, loadingVolume) : 
    global xrow
    global xcol
    global cell_format_yellow
    global cell_format_blue
    lcol = 0
    for i in ['LabID', 'LimsID', 'WellLocation', 'VolumePerSample(ul) from 1:4 dilution'] :
        f_out.write(xrow, lcol, i)
        lcol += 1
    xrow += 1
    
    sumOfng = 0
    minPoolVolume = 0
    sumOfSampleVolumes = 0

    #Calculate pooling factor 
    for k in data.keys() :
        data[k]['poolingFactor'] = float(data[k]['readCount']) / float(totalReadSum)

        #Find out minimum pool volume in order to calculate volume per sample
        neededPoolVolume = (2.0 * float(data[k]['nM']) ) / (loadingConc/200.0 * data[k]['poolingFactor'])
        
        if minPoolVolume == 0 : 
            minPoolVolume = neededPoolVolume
        else : 
            if neededPoolVolume > minPoolVolume :
                minPoolVolume = neededPoolVolume

    if minPoolVolume < float(loadingVolume) :
        poolVolume = float(loadingVolume)
    else :
        poolVolume = minPoolVolume
        
    #Calculate volume per sample
    for k in sorted(data.keys()) :
        data[k]['volumePerSample'] = float(poolVolume * loadingConc/200.0 * data[k]['poolingFactor'] ) / data[k]['nM']
        
        sumOfSampleVolumes += data[k]['volumePerSample']
        # Visualization to user
        visualization(f_out, k, data[k])

    bufferVol = poolVolume - sumOfSampleVolumes
    pooledLibraryVolume = poolVolume - bufferVol

    xrow += 1
    f_out.write(xrow, 0, 'PoolVolume (ul): ' + str("{0:.2f}".format(pooledLibraryVolume)).replace('.',','), cell_format_yellow)
    xrow += 1
    f_out.write(xrow, 0, 'BufferVolume (ul): ' + str("{0:.2f}".format(bufferVol)).replace('.',','), cell_format_yellow)
    xrow += 2
    f_out.write(xrow, 0, 'TotalVolume (ul): ' + str("{0:.2f}".format(poolVolume)).replace('.',','))
    if poolVolume > 310.0 : 
        xrow += 1
        f_out.write(xrow, 0, '###Use only 310 ul in subsequent steps###' , cell_format_blue)

def cacheArtifact( limsid ):

    global CACHE_IDS

    if limsid not in CACHE_IDS:
        CACHE_IDS.append( limsid )

def getSampleData(stepURI, instrument, availableReads, kit ) :
    poolURIs = {}
    sampleData = {}
    IOmatch = {}
    
    pDOM = parseString(api.GET(stepURI))

    IOMaps = pDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        input = IOMap.getElementsByTagName( "input" )
        limsid = input[0].getAttribute( "limsid" )
        output = IOMap.getElementsByTagName( "output" )
        if output[0].getAttribute( "output-generation-type") == "PerInput" :
            oURI = output[0].getAttribute( "uri" ) 
            IOmatch[limsid] = oURI

        cacheArtifact( limsid )

    totalReadSum = 0
    for limsid in CACHE_IDS :
        aURI = BASE_URI + "artifacts/" + limsid
        aDOM = parseString(api.GET(aURI))
        name = aDOM.getElementsByTagName( "name" )[0].firstChild.data
        
        sURI = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
        slimsID = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )

        well = aDOM.getElementsByTagName( "value" )[0].firstChild.data
        libraryConc = api.getUDF( aDOM, "qPCR concentration (pM)" )
    
        if libraryConc == "" :
            print "All artifacts must have a value for qPCR concentration (pM)" 
            sys.exit(255)
        else : 
            #1:4 diluted library
            libraryConcDiluted = float(libraryConc)/4

        fragmentLength = api.getUDF( aDOM, "Size (bp)" )
        if fragmentLength == "" :
            print "All artifacts must have a value for Size (bp)"
            sys.exit(255)


        #Go to submitted sample level for read count
        sDOM = parseString(api.GET(sURI))
        readCount = api.getUDF( sDOM, "Desired read count" )

        if readCount == "" :
            print "Desired read count per sample must be specified at SubmittedSample level" 
            sys.exit(255)

            
        totalReadSum += float(readCount)

        #Calculate nM from Tapestation and qPCR values
        #(input.::qPCR concentration (pM):: * (452.0 / input.::Size (bp)::) ) / 1000.0; 
        nM = (float(libraryConc) * (452.0 / float(fragmentLength) ) / 1000.0 )
        nMDiluted = (float(libraryConcDiluted) * (452.0 / float(fragmentLength) ) / 1000.0 )

        #Update output artifact with concentration in nM 
        oURI = IOmatch[limsid]
        oDOM = parseString(api.GET(oURI))
        api.setUDF( oDOM, "Size adjusted concentration (nM)", nM )
        oXML = api.PUT( oDOM.toxml().encode('utf-8'), oURI )


        sampleData[slimsID] = { 'labID' : name, 
                                'limsID' : slimsID,
                                'nM' : float(nMDiluted),
                                'well' : well ,
                                'readCount' : float(readCount)} 


    return sampleData, totalReadSum

def setupGlobalsFromURI( uri ):

    global HOSTNAME
    global VERSION
    global BASE_URI
    
    tokens = uri.split( "/" )
    HOSTNAME = "/".join(tokens[0:3])
    VERSION = tokens[4]
    BASE_URI = "/".join(tokens[0:5]) + "/"

def main():
    global api
    api = None    
    api = glsapiutil.glsapiutil2()

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:c:k:l:")
    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-c':
            args[ "loadingConc" ] = p
        elif o == '-k':
            args[ "kit" ] = p
        elif o == '-l':
            args[ "outFile" ] = p

    setupGlobalsFromURI( args[ "stepURI" ] )
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    
    availableReads = float( KitToReads[ args[ "kit" ] ] )
    kit = args[ "kit" ]
    instrument =  args[ "kit" ].split(" ")[0]
    loadingConc = float(args[ "loadingConc" ])
    if kit == "NovaSeq S4 300" : 
        loadingVolume = 310.0
    
    #Get necessary data per sample
    sampleData, totalReadSum = getSampleData(args[ "stepURI" ], instrument, availableReads, kit)

    #Give warning if reads are missing 
    if totalReadSum > availableReads :
        print "WARNING! Too many samples. Number of reads missing: ", (totalReadSum - availableReads)
        sys.exit(255)

    #Calculate pooling factor, dilution factor, volume for pooling etc.
    f_outfile = xlsxwriter.Workbook(args[ "outFile" ] + '.xlsx')
    global cell_format_2dec
    global cell_format_red
    global cell_format_yellow
    global cell_format_blue

    cell_format_2dec = f_outfile.add_format({'bg_color':   '#FFC7CE'})
    cell_format_2dec.set_num_format('0.00')
    cell_format_yellow = f_outfile.add_format({'bg_color':   '#FFEB9C',
                                               'font_color': '#9C6500'})
    cell_format_blue = f_outfile.add_format({'bg_color':   '#B0E0E6'})
    f_outsheet = f_outfile.add_worksheet()
    columns = (37, 18, 15, 36 )
    for i in range(len(columns)):
        f_outsheet.set_column(i, i, columns[i])

    normalization(f_outsheet, sampleData, totalReadSum, loadingConc, loadingVolume)

    f_outfile.close()

if __name__ == "__main__":
    main()
