import sys
import getopt
import glsapiutil_good
import xml.dom.minidom
import os
import re
import requests
import string
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET

HOSTNAME = 'http://192.168.8.10:8080'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

DEBUG = False
api = None
args = None

def dl_pdf( artifactluid_ofpdf ):    ### finds the file LUID from artifact LUID of the PDF

    artif_URI = BASE_URI + "artifacts/" + artifactluid_ofpdf
    artGET = requests.get(artif_URI, auth=(args[ "username" ],args[ "password" ]))      #GET artifact XML
    artXML = artGET.text
    root = ET.fromstring(artXML)
    for id in root.findall("{http://genologics.com/ri/file}file"):
        fileLUID = id.get("limsid")

    file_URI = BASE_URI + "files/" + fileLUID + "/download"
    fileGET = requests.get(file_URI, auth=(args[ "username" ],args[ "password" ])) ##retrieves the pdf file
    with open("frag.pdf", 'wb') as fd:				
        for chunk in fileGET.iter_content():                  	#saving data stream to file in local
            fd.write(chunk)

def getartifact_batch( LUIDs ):

        lXML = []
        lXML.append( '<ri:links xmlns:ri="http://genologics.com/ri">' )
        for limsid in LUIDs:
                lXML.append( '<link uri="' + BASE_URI + 'artifacts/' + limsid + '" rel="artifacts"/>' )
        lXML.append( '</ri:links>' )
        lXML = ''.join( lXML )
        mXML = api.getBatchResourceByURI( BASE_URI + "artifacts/batch/retrieve", lXML )

        try:
                mDOM = parseString( mXML )
                nodes = mDOM.getElementsByTagName( "art:artifact" )
                if len(nodes) > 0:
                        response = mXML
                else:
                        response = ""
        except:
                response = ""
        return response


def make_wellmap( batchDom ):

    nodes = batchDOM.getElementsByTagName( "art:artifact" )
    well_map = {}
    for each in nodes:
        limsID = each.getAttribute( "limsid" )
        nod = each.getElementsByTagName( "value" )
        well = nod[0].firstChild.data
        place = well[0] + well[2:]
        well_map[str(place)] = str(limsID)
    return well_map

	
def main():

    global api
    global args
    global batchDOM
   # print 'Requesting information from the API'

    args = {}
    fileLUID = " "
    opts, extraparams = getopt.getopt(sys.argv[1:], "a:u:p:f:")

    for o,p in opts:
        if o == '-a':
            args[ "artifactLUID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-f':
            args[ "outputfileLUIDs" ] = p

    api = glsapiutil_good.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )
    dl_pdf( args[ "artifactLUID" ] )

    outputfileLUIDs = args[ "outputfileLUIDs" ].split(" ")
    
    batchXML = getartifact_batch( outputfileLUIDs ) 
    
    batchDOM = parseString( batchXML )

    well_map = make_wellmap( batchDOM )

    wells=[]
    for i in range(1,13):
        for a in list(string.ascii_uppercase[:8]):
            well = a+str(i)
            wells.append(well)
   
   # print 'Extracting and attaching images'
    page = 10
    for each in range(len(wells)):
	well_loci = wells[each]        
	if well_loci in well_map.keys():
	    limsid = well_map[well_loci]
	    filename = limsid + "_" + well_loci
            command = 'pdfimages ' + 'frag.pdf' +' -j -f ' + str(page) + ' -l ' + str(page) + ' ' + filename
	    os.system(command)
	    page += 1
            longname = filename + "-000"
            ppmname = longname + ".ppm"
            jpegname = longname + ".jpeg"
            command2 = "convert " + ppmname + " " + jpegname
            os.system(command2)             #conversion to .jpeg

            command3 = "rm *ppm"            #removing ppm image so it isn't inadvertently attached
            os.system(command3)
if __name__ == "__main__":
    main()
