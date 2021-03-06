"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
import xlsxwriter
import sys
import getopt
import datetime

def main():
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:f:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-s':
			args[ "stepID" ] = p
		elif o == '-f':
                        args[ "outFile" ] = p


	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()

	process = Process(lims,id= args[ "stepID" ])
	outputs = process.all_outputs(unique = True)

	EGFR = "OFF"
	KIT = "OFF" 
	n = 0

	for out in outputs: 
		if out.type == 'Analyte': 
			n +=1
			if 'Analysis' in out.samples[0].udf :

				if "KIT" in out.samples[0].udf['Analysis'] :
					KIT = "ON" 
				if "EGFR" in out.samples[0].udf['Analysis'] :
					EGFR = "ON" 
	assay = "ddPCR Mix: "
	mix_dic_manual = {}
	assayMix = 0 
	supermix = 0
	restrictionEnz = 0 
	water_M = 0
	water_A = 0 

	if EGFR == "ON" and KIT == "ON" : 
		print "Not allowed to mix assays in reaction setup" 
		sys.exit(255)
	
	elif EGFR == "ON" :
		assay += "EGFR"
		#20x IBSAFE Assay Mix (ul) = Total * 1.1
		assayMix = n * 1.1 
		# ddPCR Supermix for probes (ul) = Total * 11
		supermix =  n * 11
		#save in dict
		mix_dic = {"1. 20x IBSAFE Assay Mix (ul)" : assayMix, 
			   "2. ddPCR Supermix for probes (ul)" : supermix
			   }

	elif KIT == "ON" :
		n += 1
		assay += "KIT"
		#KIT-assay = Total * 1
		assayMix = n * 1
		# ddPCR Supermix for probes (ul) = Total * 10
		supermix =  n * 10
		# Restriction enzyme = Total * 1 ul
		restrictionEnz =  n * 1
		# Water  3 or 5 ul (manual/automatic droplet generator) 
		water_M = n * 3
		water_A = n * 5
		#save in dict
		mix_dic = {"1. KIT-assay (ul)" : assayMix,
			   "2. ddPCR Supermix for probes (ul)" : supermix, 
			   "3. Restriction enzyme (ul)" : restrictionEnz, 
			   "4. Water (ul) - manual DG" : water_M,
			   "4. Water (ul) - auto DG" : water_A,
			   }


	f_outfile = xlsxwriter.Workbook(args[ "outFile" ] + '.xlsx')
	f_outsheet = f_outfile.add_worksheet()

	cell_format_2dec = f_outfile.add_format()
	cell_format_2dec.set_num_format('0.00')
	cell_format_red = f_outfile.add_format({'bg_color':   '#FFC7CE',
						'font_color': '#9C0006'})
	cell_format_yellow = f_outfile.add_format({'bg_color':   '#FFEB9C',
						   'font_color': '#9C6500'})

	columns = (28, 15)
	for i in range(len(columns)):
		f_outsheet.set_column(i, i, columns[i])
		
	xrow = 0
	xcol = 0

	f_outsheet.write_string(xrow, xcol, assay , cell_format_red)
	xrow +=1

	for k in sorted( mix_dic.keys() ) : 
		if "Water (ul)" in k : 
			f_outsheet.write_string(xrow, xcol, k, cell_format_yellow )
		else: 
			f_outsheet.write_string(xrow, xcol, k )
		f_outsheet.write_number(xrow, xcol+1, mix_dic[k],  cell_format_2dec )
		xrow +=1


	f_outfile.close()


if __name__=='__main__':
	main()

