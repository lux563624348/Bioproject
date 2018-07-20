## Library: Vlad
## This file contains the basic function of PCA.
## Author: Xiang Li

###Sample
#### Imput Package
import pandas as pd
import numpy as np
import sys

INPUT_FILE_NAME = sys.argv[1]
__EXE_PATH_DIR = sys.argv[2]


def main():
	DATA_PATH = __EXE_PATH_DIR + '/' + INPUT_FILE_NAME + '.bed'
	
	print ("")
	print ("Calculate RPKM from bedtools intersect results.")
	print (DATA_PATH)
	###format of bedtools gives,
	### 0   1   2    3          4
	###chr TSS TES gene_id   Read_count
	df_tem = pd.read_csv(DATA_PATH, sep='\t', header=-1)
	df_tem = df_tem.rename(index=str, columns={0: "chr", 1: "TSS", 2: "TES", 3: "gene_id", 4: "#_reads"})
	df_tem['len'] = np.abs(df_tem.loc[:,'TSS'] - df_tem.loc[:,'TES'])
	number_of_total_reads = np.sum(df_tem['#_reads'])
	RPKM=df_tem.loc[:,'#_reads']*(10.0**9)/((df_tem.loc[:,'len'])*number_of_total_reads)

	df = pd.DataFrame(columns=['gene_id','RPKM'])
	df['gene_id'] = df_tem['gene_id']
	df.loc[:,'RPKM'] = RPKM.values
	df = df.set_index('gene_id')
	
	OUT_PATH= __EXE_PATH_DIR + '/RPKM_' + INPUT_FILE_NAME + '.csv'
	
	df.to_csv(OUT_PATH, sep='\t')
	

print "Start"
main()
print "End"