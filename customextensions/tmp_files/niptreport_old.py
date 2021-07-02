#!python
# -*- coding: latin-1 -*-
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
import csv
import time
import random
import pprint

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


# Get UDFs from a dom into a dict
def get_UDFs(dom):
    udf_data = {}
    elements = dom.getElementsByTagName( "udf:field" )
    for udf in elements:
        udf_data[ udf.getAttribute("name") ] = udf.firstChild.data

    return udf_data


# Return LU UDFs and correspnding sample UDFs in a dict
def get_data(luid):
    xml = api.GET( BASE_URI + "artifacts/" + luid )
    lu_udfs = {}
    sample_data = {}

    if xml:
        dom = parseString(xml)

        # Get UDF data for LU artifact
        lu_udfs = get_UDFs(dom)

        # Get sample ID and URI
        sample = dom.getElementsByTagName("sample")
        sample_lims_id  = sample[0].getAttribute("limsid")
        sample_lims_uri = sample[0].getAttribute("uri")

            
        # Fetch sample data
        sample_xml = api.GET( sample_lims_uri )
        if sample_xml:
            sample_dom = parseString(sample_xml)

            sample_data = get_UDFs( sample_dom )
            sample_data["genesis_id"] = sample_dom.getElementsByTagName("name")[0].firstChild.data


        # Get technician name from parent process
        parent_process_uri = dom.getElementsByTagName("parent-process")[0].getAttribute("uri")
        parent_process_xml = api.GET( parent_process_uri )
        if parent_process_xml:
            parent_process_dom = parseString(parent_process_xml)
            technician = parent_process_dom.getElementsByTagName("technician")
            sample_data["technician_name"] = technician[0].getElementsByTagName("first-name")[0].firstChild.data + " " + technician[0].getElementsByTagName("last-name")[0].firstChild.data




    sample_data["ID"] = sample_lims_id
    sample_data["Comment"] = lu_udfs.get("Comment", "")
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


def nl_list(elems):
    if len(elems) == 1:
        return elems[0]
    else:
        st = ""
        for idx, elem in enumerate(elems):
            st = st + str(elem)
            if( idx == len(elems) - 2 ):
                st = st + " eller "
            elif( idx < len(elems) - 2 ):
                st = st + ", "
        return st
                                                            


def generate_html( data, niptdata ):
    
    with open(niptdata) as csvfile:
        reader = csv.DictReader( csvfile, delimiter="\t" )
        for row in reader:

            # Get LIMS-ID, should be everything before the first "_" or "-".
            id_parts = re.split( "[-_]", row["Sample ID"] )
            lims_id = id_parts[0]

            if lims_id == data["ID"]:

                sentence = ""
                positive = []
                negative = []
                nac = []
                low_fetal = False
                for chrom in ["13", "18", "21"]:
                    if row['Chr'+str(chrom)+" call"] == "Positive":
                        positive.append(chrom)
                    if row['Chr'+str(chrom)+" call"] == "Negative":
                        negative.append(chrom)
                    if row['Chr'+str(chrom)+" call"] == "Not automatically called":
                        nac.append(chrom)
                    if row['Chr'+str(chrom)+" call"] == "Low fetal fraction":
                        low_fetal = True

                if (len(negative) + len(nac)) == 3:
                    sentence = u"Ingen f&ouml;rh&ouml;jd risk f&ouml;r trisomi "+nl_list(negative)+" har p&aring;visats i provet."

                if row['Chr13 call'] == "Positive":
                    sentence = u"F&ouml;rh&ouml;jd risk f&ouml;r trisomi 13 har p&aring;visats i provet."
                if row['Chr18 call'] == "Positive":
                    sentence = u"F&ouml;rh&ouml;jd risk f&ouml;r trisomi 18 har p&aring;visats i provet."
                if row['Chr21 call'] == "Positive":
                    sentence = u"F&ouml;rh&ouml;jd risk f&ouml;r trisomi 21 har p&aring;visats i provet."

                if row['Chr13 call'] == "Low fetal fraction" or row['Chr18 call'] == "Low fetal fraction" or row['Chr21 call'] == "Low fetal fraction":
                    sentence = u"Patients prov har analyserats och bed&ouml;mts som inkonklusivt pga f&ouml;r l&aring;g fetalfraktion."
                if row['Fetal fraction'] == "Insufficient sample coverage":
                    sentence = u"Patients prov har analyserats och bed&ouml;mts som inkonklusivt."

                if len(nac):
                    sentence = sentence + u" Trisomistatus f&ouml;r kromosom "+nl_list(nac)+" kunde ej best&auml;mmas."



                f1 = open( data["ID"]+".html", 'w+' )

                for chr_call in ["Chr13 call", "Chr18 call", "Chr21 call"]:
                    if row[chr_call] == "Negative":
                        row[chr_call] = "<span class='neg'>negativ</span>"
                    elif row[chr_call] == "Positive":
                        row[chr_call] = "<span class='pos'>positiv</span>"
                    elif row[chr_call] == "Low fetal fraction":
                        row[chr_call] = "L&aring;g fetalfraktion"

                f1.write(
u"""<!doctype html><html>
<head>
  <title>NIPT report</title>
  <link rel="stylesheet" type="text/css" href="/home/petter/niptreport/report.css">
  <meta charset="UTF-8">
</head>

<body>

<div class="page">

<img class="logo" src="/home/petter/niptreport/rslogo.png">
<span class="report_header">Analysrapport, NIPT - """+data.get('genesis_id',"")+u"""</span>

<div class="report_div">
  <table class="report_general">
    <tr>
      <td class="top_report_key">Patientnamn</td><td class="top_report_val">"""+ html_escape( data.get('Patient Name', "SAKNAS") ) +u"""</td>
    </tr>                                                                                                                                        
    <tr>
      <td class="top_report_key">Personnummer</td><td class="top_report_val">""" + data.get('Personal Identity Number', "SAKNAS") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Prov-ID</td><td class="top_report_val">""" +data.get('genesis_id',"SAKNAS") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Ankomstdatum</td><td class="top_report_val">""" + data.get("Date of arrival", "SAKNAS") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Provtyp</td><td class="top_report_val"> Cellfritt cirkulerande DNA fr&aring;n blod</td>
    </tr>
    <tr>
      <td class="top_report_key">Rapportdatum</td><td class="top_report_val">""" + time.strftime("%x") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Analysmetod</td><td class="top_report_val">Clarigo, non-invasive prenatal test (NIPT)</td>
    </tr>
    <tr>
      <td class="top_report_key">Analys genomf&ouml;rd av</td><td class="top_report_val">Centrum f&ouml;r Molekyl&auml;r diagnostik (CMD) och Klinisk genetik</td>
    </tr>
    <tr>
      <td class="top_report_key">Rapport genererad av</td><td class="top_report_val">""" + data.get("technician_name", "SAKNAS") +u""" </td>
    </tr>
    <tr>
      <td class="top_report_key">Rapport-ID</td><td class="top_report_val">""" + data['genesis_id'] +"."+str(random.randrange(1000000,9999999)) +u"""</td>
    </tr>
  </table>
</div>


<span class="report_header">Testresultat</span>

<div class="results_summary">""" + sentence + " " + html_escape( data.get("Comment", "") ) + u"""</div>

<span class="report_text">Fetalfraktion: """ + row["Fetal fraction"] + u"""</span><br>
<table class="report_general">
  <tr>
    <th class="top_report"></th>
    <th class="top_report">Resultat</th>
    <th class="top_report">Evidensv&auml;rde</th>
    <th class="top_report">Z-v&auml;rde</th>
  </tr>
  <tr>
    <td class="top_report_key">Kromosom 13</td><td class="top_report_val">"""+row["Chr13 call"] +u"""</td><td class="top_report_val">"""+row["Chr13 evidence"] +u"""</td><td class="top_report_val">"""+row["Chr13 Z-score"] +u"""</td> 
  </tr>
  <tr>
    <td class="top_report_key">Kromosom 18</td><td class="top_report_val">"""+row["Chr18 call"] +u"""</td><td class="top_report_val">"""+row["Chr18 evidence"] +u"""</td><td class="top_report_val">"""+row["Chr18 Z-score"] +u"""</td> 
  </tr>
  <tr>
    <td class="top_report_key">Kromosom 21</td><td class="top_report_val">"""+row["Chr21 call"] +u"""</td><td class="top_report_val">"""+row["Chr21 evidence"] +u"""</td><td class="top_report_val">"""+row["Chr21 Z-score"] +u"""</td> 
  </tr>
</table>   </tr>

<span class="report_header">Metodbeskrivning</span>
<span class="report_text">Analysen &auml;r en CE-IVD-m&auml;rkt screening av fetal aneuploidi-status f&ouml;r kromosom 13, 18 och 21 i cellfritt DNA (cfDNA) preparerat fr&aring;n maternellt blod. En riktad amplifiering av cfDNA f&ouml;ljt av massivt parallell sekvensering (MPS, &auml;ven kallat NGS) har utf&ouml;rts. Ett analyssvar kan inte ges f&ouml;re graviditetsvecka 8, vid maternella kromosomavvikelser, vid multipla graviditeter, graviditet genom &auml;ggdonation, placental mosaicism, fetal chimerism, partiell fetal aneuploidi, "vanishing twins" eller fetalfraktion under 4%. Analyssvar kan inte heller ges f&ouml;r kvinnor som genomg&aring;tt blodtransfusion, immunterapi, stamcellsterapi, transplantation eller str&aring;lbehandling inom de senaste 3 m&aring;naderna.</span>


</table>
</style>

</div>

</body>
</html>""")
                csvfile.close()
                f1.close()
                return data["ID"]+".html"


	
def main():

    global api
    global args
    global batchDOM

    args = {}
    fileLUID = " "
    opts, extraparams = getopt.getopt(sys.argv[1:], "a:b:u:p:f:")

    for o,p in opts:
        if o == '-a':
            args[ "artifactLUID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-f':
            args[ "outputfileLUIDs" ] = p
        elif o == '-b':
            args[ "clarigofile" ] = p

    outputfileLUIDs = args[ "outputfileLUIDs" ].split(" ")

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )


    # WHY?
    complete_file( args[ "clarigofile" ],"clarigodata.txt" )

    os.system("cp clarigodata.txt /all")


    for LUID in outputfileLUIDs:
        data = get_data( LUID )

        html_fn = generate_html( data, "clarigodata.txt" )

        if html_fn is not None:
            #print html_fn
            #os.system("cp "+html_fn+" /all")

            pdf_fn = LUID+"."+data["genesis_id"]+".pdf"
       
            os.system("scp "+html_fn+" petter@10.0.224.63:/home/petter/niptreport/")
            os.system("ssh petter@10.0.224.63 '/home/petter/anaconda/bin/weasyprint /home/petter/niptreport/"+html_fn+" /home/petter/niptreport/"+LUID+".pdf && scp /home/petter/niptreport/"+LUID+".pdf glsai@mtapp046.lund.skane.se:/all'")
            os.system("mv /all/"+LUID+".pdf "+pdf_fn)
            print ":P"


if __name__ == "__main__":
    main()
