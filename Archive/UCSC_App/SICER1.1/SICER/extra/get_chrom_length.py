#!/usr/bin/env python

# Get the length of the self-defined chroms from a fasta file

import re, os, sys, shutil
from math import *   
from string import *
from optparse import OptionParser
import operator

from Bio import SeqIO
from Bio.Seq import *
from Bio.SeqRecord import SeqRecord

def get_chrom_lengths(fasta_file):
	chrom_lengths = {}
	for seq_record in SeqIO.parse(fasta_file, "fasta"):
		chrom_lengths [seq_record.id] = len(seq_record)
	return chrom_lengths

def main(argv):
	parser = OptionParser()
	parser.add_option("-f", "--fastafile", action="store", type="string", dest="fasta_File", metavar="<file>", help="fasta file for the sequences")
	parser.add_option("-o", "--outfile", action="store", type="string", dest="out_file", metavar="<file>", help="output file name for lengths of chroms")
	
	(opt, args) = parser.parse_args(argv)
	if len(argv) < 4:
		parser.print_help()
		sys.exit(1)
	
	chrom_lengths = get_chrom_lengths(opt.fasta_File)
	
	outf = open(opt.out_file, "w")
	for chrom in chrom_lengths.keys():
		sline = chrom + "\t" + str(chrom_lengths[chrom]) + "\n" 
		outf.write(sline)
	outf.close()
	

if __name__ == "__main__":
	main(sys.argv)