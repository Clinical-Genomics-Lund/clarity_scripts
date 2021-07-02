import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
import platform
from xml.dom.minidom import parseString

HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME 
CACHE = {}
api = None

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]    

def setUDF( self, DOM, udfname, udfvalue ):
    newDOM = DOM

    ##if the node already exists, delete it
    elements = newDOM.getElementsByTagName( "udf:field" )
    for element in elements:
        if element.getAttribute( "name" ) == udfname:
            newDOM.childNodes[0].removeChild( element )

    #now add the new UDF node
    newNode = newDOM.createElement( "udf:field" )
    newNode.setAttribute( "name", udfname )
    txt = newDOM.createTextNode( udfvalue )
    newNode.appendChild( txt )
    newDOM.childNodes[0].appendChild( newNode )
    return newDOM

def checkFileAttachment(oDOM) :

    #Get the file node
    if not oDOM.getElementsByTagName( "file:file" ):
        comment = api.getUDF(oDOM, "Comment")
        if comment == "":
            print "Result file must be uploaded for samples analysed in Coyote"
            sys.exit(255)

#file_uri = oDOM.getElementsByTagName("file:file")[0].getAttribute( "uri" ) 
#fileDOM = parseString ( getObject(file_uri) ) 
#file_name = (fileDOM.getElementsByTagName( "original-location" )[0].firstChild.data).split(".")[-1]
#if file_name != "pdf" :
#api.reportScriptStatus( stepURI, "ERROR", "The Result file must be a PDF file" )            

def setProgressUDF(oURI) :

    oXML = getObject(oURI )
    oDOM = parseString( oXML )
    #Get Sample URI
    Nodes = oDOM.getElementsByTagName( "sample" )
    sampleURI = Nodes[0].getAttribute( "uri" )
    sampleXML = getObject( sampleURI )
    sampleDOM = parseString( sampleXML )

    api.setUDF( sampleDOM, 'Progress', 'Sequencing and Data Analysis Complete' )

    rXML = api.updateObject( sampleDOM.toxml().encode('utf-8'), sampleURI )                                

def getOutputSamples():

    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" :
            oURI = Nodes[0].getAttribute( "uri" )
            OutputSamples.append(oURI)
    
    return OutputSamples

def main():

    global api
    global args
    global OutputSamples

    args = {}
    OutputSamples = []

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p


    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME  )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    OutputSamples = getOutputSamples()

    #First check file attachment 
    for oURI in OutputSamples :
        oXML = api.getResourceByURI( oURI )
        oDOM = parseString( oXML )
        tool = api.getUDF( oDOM, "Variant analysis tool" )

        if (tool == "Annat. Se kommentar.") :
            #Make sure user has written comment.
            comment = api.getUDF(oDOM, "Comment")
            if comment == "" :
                print "Please specify used variant analysis tool in the 'Comment' field."
                sys.exit(255)
#        elif (tool == "Coyote") :   #Turned off 2020-02-27 to allow passing step without file upload
#            checkFileAttachment(oDOM)

    #Update the progress field if everything went well with the attachment check
    for oURI in OutputSamples :
        setProgressUDF(oURI)

if __name__ == "__main__":
    main()
