#Definition of pool groups (key = analysis at sample level, value = Pool group name)
pGroupDef = { 'Myeloisk Panel - Parad' : 'Myeloid'  ,
              'Myeloisk Panel - Oparad - KLL' : 'Myeloid'  ,
              'Myeloisk Panel - Oparad - Annat' : 'Myeloid'  ,
              'Myeloisk Panel - Oparad - MPN' : 'Myeloid'  ,
              'Myeloisk Panel - Oparad - AML' : 'Myeloid'  ,
              'Myeloisk Panel - Oparad - AlloSCT' : 'Myeloid'  ,
              'SureSelectXTHS - Trio Exome' : 'SureSelectXTHS'  ,
              'SureSelectXTHS - Single Exome' : 'SureSelectXTHS'  ,
              'SureSelectXTHS - Paired Tumor Exome' : 'SureSelectXTHS'  ,
              'SureSelectXTHS - Unpaired Tumor Exome' : 'SureSelectXTHS'  ,
              'SureSelectXTHS - Paired BRCA' : 'SureSelectXTHS'  ,
              'SureSelectXTHS - Unpaired BRCA' : 'SureSelectXTHS'  ,
              'SureSelectXTHS - CTG Exome' : 'SureSelectXTHS'  ,
              'Microbiology WGS Nextera XT' : 'Microbiology' ,
              'TruSeq Stranded mRNA' : 'TruSeqStrandedmRNA',
              'TruSeq Stranded mRNA - Bladder' : 'TruSeqStrandedmRNA',
              'TruSeq Stranded mRNA - Fusion' : 'TruSeqStrandedmRNA',
              'TruSeq Stranded mRNA - Expression - Breast' : 'TruSeqStrandedmRNA',
              'GMSMyeloidv1.0' : 'TWISTMyeloid',
              'HereditarySolidCancerv1.0' : 'TWISTHereditarySolid',
              'clinicalWESv1.0' : 'TWISTClinicalWES',
              'GMSLymphomav1.0': 'TWISTLymphoma',
              'SciLifePanCancerv1.0' : 'TWISTPanCancer' ,
              'GMSSolidTumorv2.0' : 'TWISTSolidTumor',
              'GMSSolidTumorv1.0' : 'TWISTSolidTumor',
              'MODY_CTFR_AATv1.0' : 'TWISTModyCFRT',
              'Sars-CoV-2 IDPT' : 'SarsIDPT',
              'Microbiology WGS IDPT' : 'MicrobiologyIDPT',
              'Microbiology WGS IDPT - CTG' : 'MicrobiologyIDPT-CTG',
              'Clarigo NIPT Analys' : 'NIPT'}

totVolume = {"NextSeq" : 1300.0 ,
             "MiniSeq" : 500.0,
             "NovaSeq SP 300" : 100.0,
             "NovaSeq S1 300" : 100.0,
             "NovaSeq S2 300" : 150.0,
             "NovaSeq S4 300" : 310.0}

denConc = {"NextSeq" : 20.0 ,
           "MiniSeq" : 5.0  }

#Convert kit selection to number of available reads
KitToReads = { 'NextSeq mid 300 v2' : 260000000.0,
               'NextSeq high 300 v2' : 800000000.0,
               'MiniSeq mid 300' : 26000000.0, # changed from 19000000.0 20210210
               'MiniSeq high 300' : 50000000.0,
               'NovaSeq SP 300' : 2000000000.0, #changed from 1600000000 20201012
               'NovaSeq S1 300' : 3500000000.0, # changed from 3200000000.0 20200810
               'NovaSeq S2 300' : 8200000000.0,
               'NovaSeq S4 300' : 24000000000.0 } #changed from 20000000000.0 20201116

#ng/ul to nM convertion
nMConversionFactor = { 'SureSelectXTHS' : 3.52,
                       'TruSightMyeloid' : 3.85 ,
                       'NexteraQAML' : 3.85 ,
                       'Microbiology' : 3.37,
                       'TruSeqStrandedmRNA' : 3.44,
                       'TWISTMyeloid' : 2.47,
                       'TWISTHereditarySolid' : 2.47,
                       'TWISTClinicalWES' : 2.47,
                       'TWISTLymphoma' : 2.47,
                       'TWISTPanCancer' : 2.47,
                       'TWISTSolidTumor' : 2.47,
                       'TWISTModyCFRT' : 2.47,
                       'SarsIDPT' : 3.37,
                       'MicrobiologyIDPT' : 3.37,
                       'MicrobiologyIDPT-CTG' : 3.37,
                       'NIPT' : 2.5
                       }

