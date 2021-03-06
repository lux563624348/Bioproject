#!/usr/bin/env python
# 
# Authors: Chongzhi Zang, Weiqun Peng
#
# This module compares two libraries on genes, which are potentially overlapping!

# Disclaimer
# 
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# Comments and/or additions are welcome (send e-mail to:
# wpeng@gwu.edu).
#

import re, os, sys, shutil
from math import *   
from string import *
from optparse import OptionParser
import operator
import numpy

import BED
import get_total_tag_counts
import get_read_count_on_genes
import Utility
import scipy.stats
import matplotlib.pyplot as plt
	
def correlation(A_list, B_list, start_cutoff, end_cutoff):
	"""
	Cacluate the pearson and spearman correlation of two list, with cutoff possible at the beginning and the end.
	The cutoff is implemented to probe the effect of outliers. the correlation is calculated for subarray [start_cutoff, ..., len(A_list)-1-end_cutoff)
	
	Returns (pearsonr, spearmanr), pearsonr=(correlation, pvalue), spearmanr=(correlation, pvalue)
	"""
	
	assert len(A_list)==len(B_list);
	assert (len(A_list)- end_cutoff) >= start_cutoff;
	c_list=[];		
	for i in range(len(A_list)):
		c_list.append([A_list[i], B_list[i]]);
	c_list.sort(key = operator.itemgetter(0));

	atemplist=[];
	btemplist=[];
	for index in range(start_cutoff, len(c_list)-end_cutoff):
		atemplist.append(c_list[index][0]);
		btemplist.append(c_list[index][1]);
	
	A_array = numpy.array(atemplist);
	B_array = numpy.array(btemplist);
	
	pearson = scipy.stats.pearsonr(A_array, B_array);
	#print "Pearson's correlation is: ", pearson[0], " with p-value ",  pearson[1];
	spearman = scipy.stats.spearmanr(A_array, B_array);
	#print "Spearman's correlation is: ", spearman[0], " with p-value ",  spearman[1];
	return (pearson, spearman);

def main(argv):
	parser = OptionParser()
	parser.add_option("-a", "--rawreadfileA", action="store", type="string", dest="readfileA", metavar="<file>", help="raw read file A in bed format")
	parser.add_option("-b", "--rawreadfileB", action="store", type="string", dest="readfileB", metavar="<file>", help="raw read file B in bed format")
	parser.add_option("-f", "--fragment_size", action="store", type="int", dest="fragment_size", metavar="<int>", help="average size of a fragment after A experiment")
	parser.add_option("-g", "--known_genes_file", action="store", type="string", dest="known_genes", metavar="<file>", help="file with known genes in UCSC format")
	parser.add_option("-r", "--'Promoter' or 'GeneBody' or 'PromoterGenebody' or 'ExonicRegion'", action="store", type="string", dest="region_type", metavar="<str>", help="region to count tags in")
	parser.add_option("-u", "--promoter_upstream_extension", action="store", type="int", dest="promoter_upstream_extension", help="upstream extension of promoter region from TSS", default = 5000, metavar="<int>")
	parser.add_option("-d", "--promoter_downstream_extension", action="store", type="int", dest="promoter_downstream_extension", help="downstream extension of promoter region from TSS", default = 1000, metavar="<int>")
	parser.add_option("-o", "--outfile", action="store", type="string", dest="out_file", metavar="<file>", help="output file name for genes and tag numbers")
	
	(opt, args) = parser.parse_args(argv)
	if len(argv) < 16:
        	parser.print_help()
        	sys.exit(1)
	
	if not Utility.fileExists(opt.readfileA):
		print opt.readfileA, " not found";
		sys.exit(1)
	if not Utility.fileExists(opt.readfileB):
		print opt.readfileB, " not found";
		sys.exit(1)	

	scaling_factor = 1000000;
	
	
	A_read_count_on_genes = get_read_count_on_genes.get_read_count_on_genes (opt.readfileA, opt.fragment_size, opt.known_genes, opt.region_type, opt.promoter_upstream_extension, opt.promoter_downstream_extension);
	B_read_count_on_genes = get_read_count_on_genes.get_read_count_on_genes (opt.readfileB, opt.fragment_size, opt.known_genes, opt.region_type, opt.promoter_upstream_extension, opt.promoter_downstream_extension);
	assert len(A_read_count_on_genes.keys()) == len(B_read_count_on_genes.keys());
	
	A_library_size = get_total_tag_counts.get_total_tag_counts(opt.readfileA);
	B_library_size = get_total_tag_counts.get_total_tag_counts(opt.readfileB);
	non_zero_A_genes = 0;
	non_zero_B_genes = 0;
	total_A_read_count_on_genes = 0;
	total_B_read_count_on_genes = 0;	
	
	f = open(opt.out_file, 'w')
	for g in A_read_count_on_genes.keys():
		if A_read_count_on_genes[g] > 0: 
			non_zero_A_genes += 1;
			total_A_read_count_on_genes += A_read_count_on_genes[g];
		normalized_A_count = A_read_count_on_genes[g]/float(A_library_size) * scaling_factor; 
		if B_read_count_on_genes[g] > 0: 
			non_zero_B_genes += 1;
			total_B_read_count_on_genes += B_read_count_on_genes[g];
		normalized_B_count = B_read_count_on_genes[g]/float(B_library_size) * scaling_factor; 
		outline = g + '\t' + str(A_read_count_on_genes[g]) + '\t' + str(normalized_A_count) + '\t' + str(B_read_count_on_genes[g]) + '\t' + str(normalized_B_count) + '\n';
		f.write(outline)
	f.close()
	
	print "Total number of ",  opt.region_type , ": ", len(A_read_count_on_genes.keys());
	print "Number of ",  opt.region_type , " overlapped with ", opt.readfileA, " islands: ", non_zero_A_genes;
	print "Number of ",  opt.region_type , " overlapped with ", opt.readfileB, " islands: ", non_zero_B_genes;
	print  total_A_read_count_on_genes, "of the ", A_library_size, " ", opt.readfileA, " reads are on ", opt.region_type;
	print  total_B_read_count_on_genes, "of the ", B_library_size, " ", opt.readfileB, " reads are on ", opt.region_type;
	

	# Calculate the correlations, those genes whose read counts are zero in both libraries are not counted.
	A_list=[];
	B_list=[];
	
	for g in A_read_count_on_genes.keys():
		#if A_read_count_on_genes[g] > 0.5  or B_read_count_on_genes[g] > 0.5 :
		if A_read_count_on_genes[g] >= -1  or B_read_count_on_genes[g] >= -1 :
			A_list.append(A_read_count_on_genes[g]);
			B_list.append(B_read_count_on_genes[g]);

	A_array = scipy.array(A_list)/float(A_library_size) * scaling_factor;
	B_array = scipy.array(B_list)/float(B_library_size) * scaling_factor;
	
	print "Number of ", opt.region_type, " with non-zero read count in either libraries: ", len(A_list);
	pearson=scipy.stats.pearsonr(A_array, B_array);
	print "Pearson's correlation is: ", pearson[0], " with p-value ",  pearson[1];
	spearman = scipy.stats.spearmanr(A_array, B_array);
	print "Spearman's correlation is: ", spearman[0], " with p-value ",  spearman[1];
	
	#Calculate the non-parametric Kolmogorov-Smirnof statistic on 2 samples
	#From scipy.stats: This tests whether 2 samples are drawn from the same distribution. Note that, like in the case of the one-sample K-S test, the distribution is assumed to be continuous.This is the two-sided test, one-sided tests are not implemented. The test uses the two-sided asymptotic Kolmogorov-Smirnov distribution. If the K-S statistic is small or the p-value is high, then we cannot reject the hypothesis that the distributions of the two samples are the same.
	#The ideal situation would be the following. For example, we have a gene and we made measurement of the expression of this gene multiple times under two conditions. To address the questions whether this gene is expressed in a similar manner under the two conditions (w/o assuming normal distribution etc), we can use KS test.In this case, the situation is different, we have only one measurement for each gene under each condition. What we are doing is to pool all genes together to generate the distribution of gene expressions/mark-levels for each condition, and we are asking whether the distributions differ in the two conditions. The caveat is that even if the two distributions are the same, the behavior of individual genes can be quite different under different conditions. 
	 
	ksTestResult = scipy.stats.ks_2samp(A_array, B_array);
	print "P-value from Kolmogorov-Smirnof test is ", ksTestResult[1], " with statistic value: ", ksTestResult[0];
	
	#Generate the scatter plot figure.
	size = len(A_list) * len(A_list);
	plt.plot(A_array, B_array, "bo", markersize=3.0);
	#plt.scatter(A_array, B_array, s=size)
	mytext="PearsonR=" + str(pearson[0]) + "; SpearmanR=" + str(spearman[0])
	title_line = "Read count correlation on " + opt.region_type;
	#plt.title(title_line, fontsize=6)	
	plt.title(title_line)
	x=opt.readfileA.split("/")[-1]
	y=opt.readfileB.split("/")[-1]
	plt.ylabel(y)
	plt.xlabel(x)
	ax = plt.gca();
	ax.set_xscale('log')
	ax.set_yscale('log')
	xmin, xmax = ax.get_xlim()
	ymin, ymax = ax.get_xlim()
	plt.text(xmin, ymax*0.8, mytext, fontsize=7);
	ax.set_aspect(1.) 
	epsfilename = opt.out_file.split(".")[0] + ".eps"
	plt.savefig(epsfilename, format="eps")
	pngfilename = opt.out_file.split(".")[0] + ".png"
	plt.savefig(pngfilename, format="png")
	
	
	

if __name__ == "__main__":
	main(sys.argv)
