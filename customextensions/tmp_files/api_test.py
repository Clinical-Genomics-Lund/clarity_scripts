#!/usr/bin/env python

import glsapiutil
import platform
from xml.dom.minidom import parseString
import pprint

api = None


def get_parent_process_uri( dom ):
    if len( dom.getElementsByTagName( "parent-process" ) ) > 0:
        return dom.getElementsByTagName( "parent-process" )[0].attributes["uri"].value
    else:
        return False


def GET_dom( uri ):
    xml = api.GET(uri)
    return parseString(xml)


def iomap_output_type( element ):
    return element.getElementsByTagName("output")[0].attributes["output-type"].value

def iomaps_only_sample_outputs( element ):
    new_iomaps = []
    for io_map in element:
        if iomap_output_type(io_map) == "Sample" or iomap_output_type(io_map) == "Analyte":
            new_iomaps.append( io_map )
    if len(new_iomaps) > 0:
        return new_iomaps

    return 0



def trace_iomaps( uri ):

    # Fetch and parse URI
    dom = GET_dom( uri )


    # Get all i/o maps
    io_maps = dom.getElementsByTagName("input-output-map")


    # Extract only i/o mapping with output to "Sample" or "Analyte"
    io_maps = iomaps_only_sample_outputs( io_maps )


    # If there are more than 1 I/O mapping to a sample/analyte, return these LIMS IDS
    if len(io_maps) > 1:
        lims_ids = []
        for io_map in io_maps:
            lims_ids.append( io_map.getElementsByTagName("input")[0].attributes["limsid"].value )
        return lims_ids
        
    # Otherwise, recurse to previous parent process
    else:

        # Get URI of parent process 
        next_uri = get_parent_process_uri( io_map[0].getElementsByTagName("input")[0] )

        # If there wasn't any, we've reached the end of the I/O chain and still only 1 analyte
        if next_uri == False:
            return "Pool was never split..."
            
        else:
            trace_iomaps( next_uri )



def main():

    global api

    #pool_uri = "https://mtapp046.lund.skane.se/api/v2/artifacts/2-18207"
    pool_uri = "https://mtapp046.lund.skane.se/api/v2/artifacts/2-13304"
    username = 'apiuser'
    password = 'LateDollarsState592'
    
    api = glsapiutil.glsapiutil2()
    api.setHostname( "https://mtapp046.lund.skane.se" )
    api.setVersion( "v2" )
    api.setup( username, password )


    xml = api.GET("https://mtapp046.lund.skane.se/api/v2/artifacts/2-18207")

    dom = parseString(xml)
    
    print dom.getElementsByTagName("type")[0].firstChild.data


#    print xml

    return


if __name__ == '__main__':

    main()
