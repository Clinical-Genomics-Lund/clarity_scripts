#!python
# -*- coding: latin-1 -*-
from __future__ import division
import sys
import getopt
import glsapiutil
import xml.dom.minidom
import os
import re
import string
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
import urllib2
import time
import random
import pprint
import math 
import sys

reload(sys)
sys.setdefaultencoding('utf8')

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

DEBUG = False
api = None
args = None



html_escape_table = {
        u'&': "&amp;",
        u'"': "&quot;",
        u"'": "&apos;",
        u'>': "&gt;",
        u'<': "&lt;",
        u'å': "&aring;",
        u'ä': "&auml;",
        u'ö': "&ouml;",
        u'Å': "&Aring;",
        u'Ä': "&Auml;",
        u'Ö': "&Ouml;"
        }

def html_escape(text):
    return "".join(html_escape_table.get(c,c) for c in text)


# Return LU UDFs and correspnding sample UDFs in a dict
def get_data(dom):
    sample_data = {}
    #Constants:
    V_droplet_uL = 0.00085
    V_reaction_uL = 20.0

    artifact_id = dom.getAttribute("limsid")
    sample_data["Ch1+Ch2+"] = int( api.getUDF( dom, "Ch1+Ch2+" ) )
    sample_data["Ch1-Ch2+"] = int( api.getUDF( dom, "Ch1-Ch2+" ) )
    sample_data["Ch1+Ch2-"] = int( api.getUDF( dom, "Ch1+Ch2-" ) )
    sample_data["Ch1-Ch2-"] = int( api.getUDF( dom, "Ch1-Ch2-" ) )
    sample_data["Number of replicates"] = int( api.getUDF( dom, "Number of replicates" ) )
    

    # Get sample ID and URI
    sample = dom.getElementsByTagName("sample")
    sample_lims_id  = sample[0].getAttribute("limsid")
    sample_lims_uri = sample[0].getAttribute("uri")

            
    # Fetch sample data
    sample_xml = api.GET( sample_lims_uri )
    if sample_xml:
        sample_dom = parseString(sample_xml)

        sample_data["submitted_id"] = sample_dom.getElementsByTagName("name")[0].firstChild.data
        sample_data["personalIdentityNumber"] = api.getUDF( sample_dom, "Personal Identity Number" )
        sample_data["Patient Name"] = api.getUDF( sample_dom, "Patient Name" )
        sample_data["Analysis"] = api.getUDF( sample_dom, "Analysis" )
        sample_data["Date recieved"] = sample_dom.getElementsByTagName("date-received")[0].firstChild.data
        sample_data["Total_plasma_extracted_vol_mL"] = float(api.getUDF( sample_dom, "Plasma volume (ml)" ) )
        sample_data["cfDNA_Total_elution_vol_ul"] = float( api.getUDF( sample_dom, "Elution volume (ul)" ) )
        sample_data["Dilution_factor"] = api.getUDF( sample_dom, "Dilution factor" )
        sample_data["IBSAFE_Input_per_well_vol_ul"] = 9.0 / float(sample_data["Dilution_factor"] )


    #Perform calculations 
    sample_data["N_mut"] = sample_data["Ch1+Ch2+"] + sample_data["Ch1+Ch2-"]
    sample_data["N_wt"] = sample_data["Ch1+Ch2+"] + sample_data["Ch1-Ch2+"]
    sample_data["N_total"] = sample_data["Ch1+Ch2+"] + sample_data["Ch1+Ch2-"] + sample_data["Ch1-Ch2+"] + sample_data["Ch1-Ch2-"]
    sample_data["Lambda_mut"] = -math.log(1 - sample_data["N_mut"] / sample_data["N_total"])
    sample_data["Lambda_wt"] = -math.log(1 - sample_data["N_wt"] / sample_data["N_total"])
    

    sample_data["C_mut"] = (2.0 * sample_data["Lambda_mut"] * V_reaction_uL *  sample_data["cfDNA_Total_elution_vol_ul"] ) / ( V_droplet_uL * sample_data["IBSAFE_Input_per_well_vol_ul"] * sample_data["Total_plasma_extracted_vol_mL"] )

    sample_data["C_wt"] = (2.0 * sample_data["Lambda_wt"] * V_reaction_uL *  sample_data["cfDNA_Total_elution_vol_ul"] ) / ( V_droplet_uL * sample_data["IBSAFE_Input_per_well_vol_ul"] * sample_data["Total_pla\
sma_extracted_vol_mL"] )

    sample_data["%MAF"] = (sample_data["C_mut"] * 100.0 ) / (sample_data["C_mut"] + sample_data["C_wt"])

    sample_data["Plasma_volume_screened_mL"] = (sample_data["IBSAFE_Input_per_well_vol_ul"] * sample_data["Total_plasma_extracted_vol_mL"] * sample_data["Number of replicates"]) / sample_data["cfDNA_Total_elution_vol_ul"]

    sample_data["Total_DNA_screened"] = ( (sample_data["C_mut"] + sample_data["C_wt"] ) * sample_data["IBSAFE_Input_per_well_vol_ul"] * sample_data["Total_plasma_extracted_vol_mL"] * sample_data["Number of replicates"] ) / sample_data["cfDNA_Total_elution_vol_ul"] 


    #Additional calculation for minimal MAF
    Lambda_mut_min = -math.log(1.0 – 3.0/sample_data["N_total"])
    C_mut_min = (2 x Lambda_mut_min * V_reaction_uL * sample_data["cfDNA_Total_elution_vol_ul"] ) / (V_droplet_uL * sample_data["IBSAFE_Input_per_well_vol_ul"] * sample_data["Total_plasma_extracted_vol_mL"] )
    sample_data["MAF_min"] = (C_mut_min * 100) / (C_mut_min + sample_data["C_mut"])

    # Get technician name from parent process
    parent_process_uri = dom.getElementsByTagName("parent-process")[0].getAttribute("uri")
    parent_process_xml = api.GET( parent_process_uri )
    if parent_process_xml:
        parent_process_dom = parseString(parent_process_xml)
        technician = parent_process_dom.getElementsByTagName("technician")
        sample_data["technician_name"] = technician[0].getElementsByTagName("first-name")[0].firstChild.data + " " + technician[0].getElementsByTagName("last-name")[0].firstChild.data


    sample_data["ID"] = sample_lims_id
    sample_data["LUID"] = artifact_id
    return sample_data
                                                                                                                                            


def complete_file( artifactluid_offile,outfile ):    ### finds the file LUID from artifact LUID of the file

    fileLUID = " "
    artif_URI = BASE_URI + "artifacts/" + artifactluid_offile
    print artif_URI

    artXML = api.GET(artif_URI)      #GET artifact XML
    artDOM = parseString( artXML )
    
    Nodes = artDOM.getElementsByTagName( "file:file" )
    fileLUID = Nodes[0].getAttribute( "limsid" )
    
    file_URI = BASE_URI + "files/" + fileLUID + "/download"
    fileGET = api.GET(file_URI) ##retrieves the file
    with open(outfile, 'wb') as fd:
        fd.write(fileGET)
                                                            


def generate_html( data, ddPCR_data ):
    
    sentence = ""
    result_summary = ""
    positive = []
    negative = []

    analysis = data["Analysis"].split("-")[1]
    if data["N_mut"] >= 3.0 :
        result = "<span class='pos'>positiv</span>"
        sentence = "Patientens plasma har testats " + result + "  f&ouml;r " + analysis
    else :
        result = "<span class='neg'>negativ</span>" 
        sentence = "Patientens plasma har testats " + result + "  f&ouml;r " + analysis

    f1 = open( data["ID"]+".html", 'w+' )

    f1.write(

u"""<!doctype html><html>
<head>
  <title>ddPCR report</title>
  <link rel="stylesheet" type="text/css" href="/home/maryem/ddPCR/report.css">
  <meta charset="UTF-8">
</head>

<body>

<div class="page">

<img class="logo" src="/home/maryem/ddPCR/rslogo.png">
<span class="report_header">Analysrapport, ddPCR - """+data.get('submitted_id',"")+u"""</span>

<div class="report_div">
  <table class="report_general">
    <tr>
      <td class="top_report_key">Patientnamn</td><td class="top_report_val">"""+ html_escape( data.get('Patient Name', "SAKNAS") ) +u"""</td>
    </tr>                                                                                                                                        
    <tr>
      <td class="top_report_key">Personnummer</td><td class="top_report_val">""" + data.get('Personal Identity Number', "SAKNAS") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Prov-ID</td><td class="top_report_val">""" + data["submitted_id"] +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Clarity LIMS-ID</td><td class="top_report_val">""" +data["ID"] +u"""</td>
    </tr> 
    <tr>
      <td class="top_report_key">Ankomstdatum</td><td class="top_report_val">""" + data["Date recieved"] +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Provtyp</td><td class="top_report_val"> Cellfritt cirkulerande DNA fr&aring;n blod</td>
    </tr>
    <tr>
      <td class="top_report_key">Rapportdatum</td><td class="top_report_val">""" + time.strftime("%Y-%m-%d") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Analysmetod</td><td class="top_report_val">IBSAFE ddPCR</td>
    </tr>
    <tr>
      <td class="top_report_key">Analys genomf&ouml;rd av</td><td class="top_report_val">Centrum f&ouml;r Molekyl&auml;r diagnostik (CMD)</td>
    </tr>
    <tr>
      <td class="top_report_key">Rapport genererad av</td><td class="top_report_val">""" + data.get("technician_name", "SAKNAS") +u""" </td>
    </tr>
    <tr>
      <td class="top_report_key">Rapport-ID</td><td class="top_report_val">""" + data['submitted_id'] +"."+str(random.randrange(1000000,9999999)) +u"""</td>
    </tr>
  </table>
</div>


<span class="report_header">Testresultat, """ + analysis + u"""</span>

<div class="results_summary">""" + sentence + u"""</div>

<table class="report_general">
  <tr>
    <th class="top_report"></th>
    <th class="top_report">Resultat</th>
    <th class="top_report">Enhet</th>
  </tr>
  <tr>
    <td class="top_report_key">Plasma analyserad</td><td class="top_report_val">""" + '{0:.2f}'.format(data["Plasma_volume_screened_mL"]) + u"""</td><td class="top_report_val">"""+ "mL" +u"""</td> 
  </tr>
  <tr>
    <td class="top_report_key">Totalm&auml;ngd DNA</td><td class="top_report_val">"""+ '{0:.2f}'.format(data["Total_DNA_screened"]) +u"""</td><td class="top_report_val">"""+ "enkelstr&auml;ngade kopior" +u"""</td> 
  </tr>
  <tr>
    <td class="top_report_key">WT konc</td><td class="top_report_val">"""+ '{0:.2f}'.format(data["C_wt"]) +u"""</td><td class="top_report_val">"""+ "enkelstr&auml;ngade kopior / mL plasma" +u"""</td> 
  </tr>
  <tr>
    <td class="top_report_key">MUT konc</td><td class="top_report_val">"""+ '{0:.2f}'.format(data["C_mut"]) +u"""</td><td class="top_report_val">"""+ "enkelstr&auml;ngade kopior / mL plasma" +u"""</td>
  </tr>  
  <tr>
    <td class="top_report_key">MAF</td><td class="top_report_val">"""+ '{0:.2f}'.format(data["%MAF"]) +u"""</td><td class="top_report_val">"""+ "%" +u"""</td>
  </tr>  
</table>   </tr>

<span class="report_header">Metodbeskrivning</span>
<span class="report_text">Bla Bla text</span>
</table>
</style>

</div>

</body>
</html>""")

    f1.close()
    return (data["ID"]+".html", result_summary)


	
def main():

    global api
    global args
    global batchDOM

    args = {}
    fileLUID = " "
    opts, extraparams = getopt.getopt(sys.argv[1:], "a:u:p:f:")

    for o,p in opts:
        if o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-f':
            args[ "outputfileLUIDs" ] = p

    outputfileLUIDs = args[ "outputfileLUIDs" ].split(" ")

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    output_artifacts = parseString( api.getArtifacts(outputfileLUIDs) )

    f = open( "/all/ddpCR_luid.xml", 'w+' )
    dir_date =  time.strftime("%y-%m-%d_%H.%M.%S")
    
    os.system("ssh petter@mtlucmds1.lund.skane.se mkdir '/data/ddPCR/Reports/"+dir_date+"'" )

    for dom in output_artifacts.getElementsByTagName("art:artifact"):

        # Get sample data
        data = get_data( dom )
        LUID = data["LUID"]


        # Generate PDF
        f.write(pprint.pformat(data)+"\n\n")
        (html_fn, summary) = generate_html( data, "ddPCR_results.txt" )


        if html_fn != "NO_REPORT": 
        
            os.system("cp "+html_fn+" /all")
            pdf_fn = LUID + "." + data["submitted_id"] + ".pdf"
            gen_fn = data["submitted_id"] + ".pdf"
            os.system("scp " + html_fn + " petter@mtlucmds1.lund.skane.se:/home/maryem/ddPCR")

            os.system("ssh petter@mtlucmds1.lund.skane.se '/home/petter/anaconda/bin/weasyprint /home/maryem/ddPCR/"+html_fn+" /home/maryem/ddPCR/"+pdf_fn+" && cp /home/maryem/ddPCR/"+pdf_fn+" /data/ddPCR/Reports/"+dir_date+" && mv /data/ddPCR/Reports/"+dir_date+"/"+pdf_fn+" /data/ddPCR/Reports/"+dir_date+"/"+gen_fn+" && scp /home/maryem/ddPCR/"+pdf_fn+" glsai@mtapp046.lund.skane.se:/all'")
 
            os.system("cp /home/maryem/ddPCR/"+LUID+".pdf /data/ddPCR/Reports")
            os.system("mv /all/" +pdf_fn+ " " + pdf_fn)
            os.system("rm /all/"+os.path.basename(pdf_fn))
            os.system("rm /all/"+os.path.basename(html_fn))
        # Set result UDF
#        api.setUDF( dom, "NIPT test results", summary )

        print ":P"

    f.close()
    # Update step artifact
    r = api.POST( output_artifacts.toxml().encode('utf-8'), BASE_URI + "artifacts/batch/update/" )
    
if __name__ == "__main__":
    main()
