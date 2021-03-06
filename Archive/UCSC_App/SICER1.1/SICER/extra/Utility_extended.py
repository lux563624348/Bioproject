#!/usr/bin/env python
# Copyright (c) 2010 The George Washington University
# Author: Weiqun Peng
#
# This software is distributable under the terms of the GNU General
# Public License (GPL) v2, the text of which can be found at
# http://www.gnu.org/copyleft/gpl.html. Installing, importing or
# otherwise using this module constitutes acceptance of the terms of
# this License.
#
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
# Version 1.1  6/9/2010

import re, os, sys, shutil
from math import *   
from string import *
from operator import itemgetter
import bisect
import operator
import copy

def sort(infile, columns, outfile):
	# Use command line sort, which is much faster
	# columns is a list: [2], [2,3] etc
	try:
		if os.system('sort -g -k %s %s > %s' % ( ",".join(map(str,columns)), infile, outfile)):
			raise
	except: sys.stderr.write(str(infile) + " can not be sorted and output to " + outfile + "\n");

def separate_by_chrom_sort(chroms, file, extention, columns):
	"""
	It is ok if the chroms do not include all those existing in the file.
	
	The column numbers are 1 based instead of 0 based!
	
	"""
	for chrom in chroms:
		match = chrom + "[[:space:]]";
		tmpFile = chrom + extention;
		mycolumns = ",".join(map(str,columns))
		try:
			if os.system('grep %s %s | sort -g -k %s > %s' %(match, file, mycolumns, tmpFile)): 
				raise
		except: sys.stderr.write( "Warning: " + str(chrom) + " reads do not exist in " + str(file) + "\n");

def separate_by_strand(file_name, p_file_name, n_file_name):
	"""
	separate the bed file into a bed file for reads on positive strand and a bed file for reads on negative strand
	"""
	match = "[[:space:]]+"
	try:
		if os.system('grep %s %s > %s' %(match, file_name, p_file_name)): 
			raise
	except: sys.stderr.write( "Warning: There is no read on positive strand in " + file_name + "\n");
	
	match = "[[:space:]]-"
	try:
		if os.system('grep %s %s > %s' %(match, file_name, n_file_name)): 
			raise
	except: sys.stderr.write( "Warning: There is no read on negative strand in " + file_name + "\n");
	
		
def chrom_files_exist(chroms, extention):
	"""
	To check if the chrom files are already prepared by separate_by_chrom_sort
	"""
	exist = 1
	for chrom in chroms:
		filename = chrom + extention;
		if fileExists(filename):
			exist *= 1
		else:
			exist *= 0
	return exist

def fileExists(f):
	try:
		file = open(f)
	except IOError:
		exists = 0
	else:
		exists = 1
		file.close()
	return exists





def is_bed_sorted(mylist):
	"""
	Check if sorted in ascending order.
	input is a mylist of BED with chrom, start, end and value.
	output: sorted =1 or 0
	"""
	sorted = 1;
	for index in range(0, len(mylist)-1):
		if mylist[index].start > mylist[index+1].start:
			return 0;
	return sorted;

def is_list_sorted(list):
	"""
	Check if sorted in ascending order.
	
	input is a list of values.
	if list is [] or [a],  output 1
	output: sorted =1 or 0
	"""
	sorted = 1
	for index in range(0, len(list)-1):
		if list[index] > list[index+1]:
			return 0;
	return sorted;
				
def is_listT_sorted(mylist):
	"""
	Check if sorted in ascending order.
	input is a list of tuples (key, annotations)
	if list is [] or [a],  output 1
	output: sorted =1 or 0
	"""
	return is_tuplelist_sorted(mylist, 0)

def is_tuplelist_sorted(mylist, column_index):
	"""
	Check if sorted in ascending order.
	input is a list of tuples
	output: sorted =1 or 0
	"""
	sorted = 1;
	for index in range(0, len(mylist)-1):
		if mylist[index][column_index] > mylist[index+1][column_index]:
			return 0;
	return sorted;


def find_islands_overlapping_with_region(region, islands):
	"""
	Efficient algorithm
	region: (start,end)
	islands:[(start,end, annotation)] non overlapping islands, needs to be sorted
	returns the indices (start_position, end_position) that overlaps with region: note it is start_position, start_position+1, ...end_position-1!
	"""
	assert (is_listT_sorted(islands) == 1)
	
	start = region[0]
	end = region[1]
	assert (start <= end);
	start_list = [island[0] for island in islands]
	end_list = [island[1] for island in islands]
	start_position = bisect.bisect_left(end_list, start);
	end_position = bisect.bisect_right(start_list, end); 
	return (start_position, end_position)

def find_islands_overlapping_with_islands(islands_1, islands_2):
	"""
	Efficient algorithm
	islands_1:[(start,end, annotation)] non-overlapping, needs to be pre-sorted 
	islands_2:[(start,end, annotation)] non-overlapping, needs to be pre-sorted 
	Return:
	island_overlaps with regard to island 1:[((start,end,annotation), (start_index, end_index))] 
	"""
	assert (is_listT_sorted(islands_1) == 1)
	assert (is_listT_sorted(islands_2) == 1)
	
	island_overlaps = []
	previous_end_index = 1
	for island in islands_1:
		region = (island[0], island[1])
		(start_index, end_index) = find_islands_overlapping_with_region(region, islands_2[previous_end_index - 1:])#end index is not inclusive
		start_index += previous_end_index - 1 #shift back into original reference frame
		end_index += previous_end_index - 1 #shift back into original reference frame
		island_overlaps.append((island, (start_index, end_index)))
		previous_end_index = end_index
	return island_overlaps

def find_islands_overlapping_with_regions(islands,regions):
	"""
	Efficient algorithm
	regions can be overlapping:[(start, end, annotation)]
	islands are non-overlapping:[(start, end, annotation)]
	
	Returns: [island, regions overlapping with islands]
	[((start, end, annotation), [(start, end, annotation)])]
	"""
	if is_listT_sorted(islands) == 0:
		my_islands = [item for item in sorted(islands, key = itemgetter(0))]
	else:
		my_islands = [item for item in islands]
		
	# remove overlaps. {(start, end):[list elements that contribute to that region]}
	unionized_regions = union_with_trace(regions)
	#print unionized_regions
	#convert to a list:  [(start, end, [list elements that contribute to that region])]
	unionized_islands = []
	for myid in unionized_regions.keys():
		unionized_islands.append((myid[0], myid[1], unionized_regions[myid]))
	#sort the unionized_islands
	unionized_islands.sort(key=itemgetter(0))
	#print unionized_islands
	#[((start,end,annotation), (start_index, end_index))] 
	my_islands_annotated = find_islands_overlapping_with_islands(my_islands, unionized_islands)
	#print "my_islands_annotated", my_islands_annotated
	
	my_islands_annotated_w_overlapping_regions = []
	#Flatten my_islands_annotated, associate each island with the original regions
	for item in my_islands_annotated:
		island = item[0]
		island_start = island[0]
		island_end = island[1]
		start_index = item[1][0]
		end_index = item[1][1]
		likely_overlapping_original_regions = [] #[(start, end, annotation)]
		# The unionized island covers multiple overlapping regions, each of which might not be really overlapping. First collect all these regions, then filter out those not really overlapping
		for index in range(start_index, end_index):
			original_regions = unionized_islands[index][2] #[list elements that contribute to that region]
			likely_overlapping_original_regions.extend(original_regions)
		#print likely_overlapping_original_regions, start_index, end_index	
		#Get the truly overlapping regions:
		#[(start, end, annotation)]
		overlapping_regions = []
		for region in likely_overlapping_original_regions:
			start = region[0]
			end = region[1]
			if overlap(island_start, island_end, start, end) == 1:
				overlapping_regions.append(region)		
		my_islands_annotated_w_overlapping_regions.append((island, overlapping_regions))
	
	return my_islands_annotated_w_overlapping_regions

def find_regions_overlapping_with_islands(regions, islands):
	"""
	Efficient algorithm
	regions can be overlapping:[(start, end, annotation)]
	islands are non-overlapping:[(start, end, annotation)]
	
	Returns: [(region, [islands])]
	[((start, end, annotation), [(start, end, annotation)])]
	"""
	#sort islands
	if is_listT_sorted(islands) == 0:
		my_islands = [item for item in sorted(islands, key = itemgetter(0))]
	else:
		my_islands = [item for item in islands]
		
	# remove overlaps in regions. {(start, end):[list elements that contribute to that region]}
	unionized_regions = union_with_trace(regions)
	#print unionized_regions
	#convert to a list:  [(start, end, [list of elements that contribute to that region])]
	unionized_islands = []
	for myid in unionized_regions.keys():
		unionized_islands.append((myid[0], myid[1], unionized_regions[myid]))
	#sort the unionized_islands by start
	unionized_islands.sort(key=itemgetter(0))
	#print unionized_islands
	#[((start,end, [list of regions that contribute to that island]), (start_index, end_index))] 
	my_unionized_islands_annotated = find_islands_overlapping_with_islands(unionized_islands, my_islands)
	#print "my_islands_annotated", my_islands_annotated
	
	my_regions_annotated_w_overlapping_islands = []
	#Flatten my_islands_annotated, associate each island with the original regions
	for item in my_unionized_islands_annotated:
		unionized_island = item[0]
		regions_in_union = unionized_island[2] #[list of elements that contribute to that region]
		start_index = item[1][0]
		end_index = item[1][1]
		
		for myregion in regions_in_union:
			region_start = myregion[0]
			region_end = myregion[1]
			overlapped_islands = []
			for index in range(start_index, end_index):
				myisland = my_islands[index]
				start = myisland[0]
				end = myisland[1]
				if overlap(region_start, region_end, start, end) == 1:
					overlapped_islands.append(myisland)
			my_regions_annotated_w_overlapping_islands.append( (myregion, overlapped_islands) )		
	return my_regions_annotated_w_overlapping_islands


def find_coverage_by_islands_on_a_region(region, islands):
	"""
	region:(start, end, annotation)
	islands are non-overlapping:[(start, end, annotation)]
	These islands are already known to overlap with the region
	
	if islands = [], coverage = 0
	
	Returns: covered length / total length
	"""
	#The returned shared_region_list (start, end) is sorted 
	min_width = 0
	intersection = intersect([region], islands, min_width)
	total_intersection_length = 0
	region_length = region[1] - region[0] + 1
	for myisland in intersection:
		length = myisland[1] - myisland[0] + 1 
		total_intersection_length += length
	coverage = total_intersection_length*1.0/region_length 
	
	#Coverage should be less than 1
	if coverage > 1.01:
		print "Coverage larger than 1 and should not be!"
		print region
		print islands 
		print coverage, region_length, total_intersection_length
		exit(0)
	return coverage

def find_coverage_by_islands_on_regions(regions, islands):
	"""
	Find the (covered_length/total_length) for each region.
	
	regions:[(start, end, annotation)]
	islands are non-overlapping:[(start, end, annotation)]
	
	Returns: {region:coverage}
	"""
	#[((start, end, annotation), [(start, end, annotation)])]
	my_regions_annotated_w_overlapping_islands = find_regions_overlapping_with_islands(regions, islands)
	regions_w_coverage = {}
	i = 0
	for item in my_regions_annotated_w_overlapping_islands:
		
		myregion = item [0]#(start, end, annotation)
		myislands = item[1]#[(start, end, annotation)]
		#if i <50:
			#print i
			#print myregion
			#print myislands  
		coverage = find_coverage_by_islands_on_a_region(myregion, myislands)
		assert (isinstance(coverage, (int, float)))
		regions_w_coverage[myregion] = coverage
		#if i <50:
			#print "coverage ", coverage
			#print   
		i += 1
	return regions_w_coverage
	
def check_overlaps_in_beds(bed_list):
	"""
	input is a list of BED with chrom, start, end and value.
	make copy to avoid unintentional consequences
	"""
	if is_bed_sorted(bed_list) == 0:
		my_bed_list = sorted(bed_list, key = operator.attrgetter('start'))
	else:
		my_bed_list = bed_list
	for i in xrange(len(my_bed_list)-1):
		if my_bed_list[i+1].start <= my_bed_list[i].end:
			return 1
	return 0

def check_overlaps_in_regions (mylist):
	"""
	input is a list (start, end, annotation) or (start, end).
	"""
	# sort according to the start
	if is_listT_sorted(mylist) == 0:
		my_list = sorted(mylist, key = itemgetter(0))
	else:
		my_list = mylist
		
	for i in xrange(len(my_list)-1):
		if my_list[i+1][0] <= my_list[i][1]:
			return 1
	return 0

def union(mylist):
	"""
	Input
		mylist: [(start, end, annotation)], [(start, end)]
		or assume that end is inclusive.
	Output [(start, end)]
	Output is already sorted
	"""
	if is_listT_sorted(mylist) == 0:
		my_new_list = sorted(mylist, key = itemgetter(0))
	else:
		my_new_list = [item for item in mylist]
		
	if len(my_new_list) == 0:
		return []	
	if len(my_new_list) == 1:
		start = my_new_list[0][0]
		end = my_new_list[0][1]
		return [(start, end)]
	else:
		outlist=[]
		current_start = my_new_list[0][0]
		current_end = my_new_list[0][1]
		i = 1
		while i < len(my_new_list):
			compare_start = my_new_list[i][0]
			compare_end = my_new_list[i][1]
			if compare_start > current_end:
				outlist.append((current_start, current_end))
				current_start = compare_start
				current_end = compare_end
			else: 
				current_end = max(current_end, compare_end)
			i += 1
		outlist.append((current_start, current_end))
		return outlist

		
		
def union_with_trace(mylist, extension = 0):
	"""
	mylist: [(start, end, annotation)], assume that end is inclusive.
	extension: when union extend both start and end with extension, but they are not recorded in output
	
	Output {(start, end):[list elements that contribute to that region]}
	"""
	if is_listT_sorted(mylist) == 0:
		my_new_list = sorted(mylist, key = itemgetter(0)) # sort by start
	else:
		my_new_list = [item for item in  mylist]
	
	out = {}	
	if len(my_new_list) == 0:
		return out
	elif len(my_new_list) == 1:
		start = my_new_list[0][0]
		end = my_new_list[0][1]
		region = (start, end)
		cluster = [my_new_list[0]]
		out [region] = cluster
		return out
	else:
		cluster = [my_new_list[0]]
		current_start, current_end = my_new_list[0][0], my_new_list[0][1]
		i = 1
		while i < len(my_new_list):
			compare_start, compare_end = my_new_list[i][0], my_new_list[i][1]
			if (compare_start - extension) > (current_end + extension):
				out[(current_start, current_end)] = [item for item in cluster]
				current_start = compare_start
				current_end = compare_end
				cluster = [my_new_list[i]]
			else: 
				cluster.append(my_new_list[i])
				current_end = max(current_end, compare_end)
			i += 1
		out[(current_start, current_end)] = [item for item in cluster]
		return out	
		
		
def shared(mylist):
	"""
	Find the intersection of the entire mylist
	
	Input:[(start, end, annotation)], assume that end is inclusive.
	Output:(start, end)
	
	"""
	if is_listT_sorted(mylist) == 0:
		my_new_list = sorted(mylist, key = itemgetter(0))
	else:
		my_new_list = mylist
		
	if len(my_new_list) == 0:
		return ()	
	if len(my_new_list) == 1:
		start = my_new_list[0][0]
		end = my_new_list[0][1]
		return (start, end)
	else:
		start = my_new_list[0][0]
		end = my_new_list[0][1]
		for region in my_new_list[1:]:
			if overlap(start, end, region[0], region[1]) == 1:
				start = max (start, region[0])
				end = min (end, region[1])
			else:# intersection is zero
				return ()
		return (start, end)

def intersect(region_list_A, region_list_B, min_width=5):
	"""
	Objective:
	Find the intersection of region_list_A with region_list_B.We want to find the shared regions from both list, with regions whose length less than min_width ignored
	Input:
	region_list_A: [(start, end, annotation)]
	region_list_B: [(start, end, annotation)]
	A,B can be unsorted and overlapping 
	Output:
	The returned shared_region_list [(start, end)] is sorted 
	"""
	if len(region_list_A) == 0 or len(region_list_B) == 0:
		return []
	else:
		shared_region_list = []
		flattened_region_list_A = [region[0] for region in region_list_A] + [region[1] for region in region_list_A]
		flattened_region_list_B = [region[0] for region in region_list_B] + [region[1] for region in region_list_B]
		flattened_region_list = flattened_region_list_A + flattened_region_list_B
		flattened_region_list = sorted(flattened_region_list)
		#print flattened_region_list
		#if len(flattened_region_list) == 0:
			#print region_list_A
			#print region_list_B
		start = flattened_region_list[0]
		end = flattened_region_list[1]
		index = 2
		while index <len(flattened_region_list):
			if end-start >= min_width: # ignore islands too small
				position = (end-start)/2.0 + start
				if is_inside(position, region_list_A)==1 and is_inside(position, region_list_B)==1:
					shared_region_list.append((start,end))
			start = end
			end = flattened_region_list[index]
			index += 1
		return shared_region_list 


def is_inside(position, region_list):
	"""
	region_list: [(start, end)] can be overlapping and unsorted
	regions are closed
	if the position == start or == end, it is still counted as inside.
	
	if region_list = [], should return 0
	
	"""
	# union the region_list to get rid of overlaps and to sort them
	unioned_list = union(region_list) #[(start,end)]
	
	starts = [region[0] for region in unioned_list]
	ends = [region[1] for region in unioned_list]
	# The index for the unioned-region where the position will be in is bisect.bisect_left(ends, position)
	if (bisect.bisect_right(starts, position) - bisect.bisect_left(ends, position)) == 1:
		return 1
	else:
		return 0	

	
	
		
def find_covering_cluster_of_regions(position, region_list, extension = 0):
	"""
	First unionize the region_list (with consideration of extension), and then identify the unioned region that covers the position.
	
	region_list: [(start, end, annotation)] can be overlapping and unsorted
	extension: when consider clustering, extend extension on both sides of each region
	
	return: the CLUSTER of region_list elements in the list where the position is inside: [(start, end, annotation)]
	
	Compared to find_covering_regions, this one does NOT examine the coverage of individual element in the cluster.
	
	"""
	# cluster the region_list to get rid of overlaps and to sort them
	unioned_region_dic = union_with_trace(region_list, extension) # {(start, end):[list elements that contribute to that region]}
	
	# Flatten the dic into a list: [(start, end, [list elements that contribute to that region])]
	unioned_region_list = []
	for region in unioned_region_dic.keys():
		start = region[0]
		end = region[1]
		unioned_region_list.append((start, end, unioned_region_dic[region])) 
	#sort according to start
	unioned_region_list =sorted(unioned_region_list, key = itemgetter(0)) #[(start, end, [list elements that contribute to that region])]
	
	starts = [region[0] for region in unioned_region_list]
	ends = [region[1] for region in unioned_region_list]
	bisect_start_index = bisect.bisect_right(starts, position)
	#This is the index where the position is in.
	bisect_end_index = bisect.bisect_left(ends, position)
	if ( bisect_start_index - bisect_end_index) == 1: # is in
		cluster = unioned_region_list[bisect_end_index][2] #[list elements that contribute to that region]
		return cluster
	else:
		return []			

def find_covering_regions(position, region_list):
	"""
	region_list: [(start, end, annotation)] can be overlapping and unsorted
	regions are closed-ended
	if the position == start or == end, it is still counted as inside.
	
	"""
	cluster = find_covering_cluster_of_regions(position, region_list, extension = 0)#[region_list elements that contribute to that region]
	if len(cluster) > 0:
		#Examine each element in the cluster for coverage
		covering_regions = []
		for region in cluster:
			start = region[0]
			end = region[1]
			if position >= start and position <=end:
				covering_regions.append(region)
		return covering_regions
	else:
		return []				
		

def overlap(start1, end1, start2, end2):
	assert start1 <= end1
	assert start2 <= end2
	if end1 < start2 or end2 < start1: #Non-overlap
		return 0
	else:
		return 1 
		
def intersection(a, b):
	"""
	Find the intersection of two lists
	"""
	return list(set(a) & set(b))


def find_distance_distribution(mylist):
	"""
	Input is a list of (start, end).
	Merge them before calculate the distance
	
	Output: a list of distances
	"""
	distance_distribution=[]
	unioned_list = union(mylist)
	for i in xrange(len(unioned_list) - 1):
		distance_distribution.append( unioned_list[i+1][0] - unioned_list[i][1] )
	return distance_distribution

def countTagsInWindow(start, end, tag_starts):
	"""
	tag_starts: [position]
	"""
	# Require that the tag_starts are sorted!
	if is_list_sorted(tag_starts) == 0:
		my_tag_starts = sorted(tag_starts)
	else:
		my_tag_starts = tag_starts
		
	assert( start<=end )
	start_ind = bisect.bisect_left(my_tag_starts, start);
	end_ind = bisect.bisect_right(my_tag_starts, end);
	tag_counts = end_ind - start_ind; # end_ind not inclusive
	return tag_counts;

def associate_simple_tags_with_regions(positions, region_list):
	'''
	positions: [ position ]
	regions: [region=(start, end, annotation)]    The regions could overlap !!
	returns a list, [(region, [tags])]
	'''
	region_list_with_tags = []
	if (is_list_sorted(positions)==0):
		my_tag_list = sorted(positions)
	else:
		my_tag_list = positions	
	
	for region in region_list:
		start = region [0]
		end = region [1]
		assert (start<=end)
		start_ind = bisect.bisect_left(my_tag_list, start)
		end_ind = bisect.bisect_right(my_tag_list, end)
		tags = my_tag_list[start_ind : end_ind] # End ind not inclusive
		combo = (region, tags) 
		region_list_with_tags.append(combo)
	return region_list_with_tags


def associate_tags_with_regions(tag_list, region_list):
	'''
	tag_list: [ tag=(position, annotation) ], individual tag is immutable.
	regions: [region=(start, end, annotation)]    The regions could overlap !!
	returns a list, [(region, [tags])]
	'''
	region_list_with_tags = []
	if (is_listT_sorted(tag_list)==0):
		my_tag_list = sorted(tag_list, key=itemgetter(0))
	else:
		my_tag_list = tag_list
	positions = [tag[0] for tag in my_tag_list]	
	
	for region in region_list:
		start = region [0]
		end = region [1]
		assert (start<=end)
		start_ind = bisect.bisect_left(positions, start)
		end_ind = bisect.bisect_right(positions, end)
		tags = my_tag_list[start_ind : end_ind] # Is this passing reference or a copy
		combo = (region, tags) 
		region_list_with_tags.append(combo)
	return region_list_with_tags	

def get_read_counts_on_regions(tag_list, region_list):
	'''
	strategy: sort the tags and go over the regions one by one
	
	tag_list: [ tag=(position, annotation) ]
	regions: [region=(start, end, annotation)]    The regions could overlap !!
	returns a list, [region, read_count]
	'''
	region_list_with_read_count = []
	
	if (is_listT_sorted(tag_list)==0):
		my_tag_list = sorted(tag_list, key=itemgetter(0))
		positions = [tag[0] for tag in my_tag_list]
	else:
		positions = [tag[0] for tag in tag_list]
	for region in region_list:
		start = region [0]
		end = region [1]
		assert (start<=end)
		start_ind = bisect.bisect_left(positions, start)
		end_ind = bisect.bisect_right(positions, end)
		read_count = end_ind - start_ind
		combo = (region, read_count) 
		region_list_with_read_count.append(combo)
	return region_list_with_read_count

	
def group(tuple_list, key_index, interval_list):
	"""
	Used to partition group elements of the tuple_list in terms of interval_list
	input: 
	tuple_list: [(value,value, value, ....)]
	key_index: key used for grouping
	interval_list: an ordered  list of intervals, 
	return:
	list of list of tuples [[(value,value, value, ....)]]
	"""
	if is_tuplelist_sorted(interval_list, 0) <= 0:
		interval_list = sorted(interval_list, key = itemgetter(0))
	starts = [item[0] for item in interval_list]
	#print starts
	ends = [item[1] for item in interval_list]
	#print ends
	
	result = [] # list of list
	for i in xrange(len(interval_list)): 
		result.append([])
		
	before = [] # elements before the first interval
	after = [] # elements after the last interval	
	for item in tuple_list:
		value = item[key_index]
		if value < starts[0]:
			before.append(item)
			#print value, before
		elif value >= ends[-1]:
			after.append(item)
			#print value, after
		else:
			# identify the interval that the item belows to
			# Here the intervals are half open
			start_ind = bisect.bisect_right(starts, value);
			end_ind = bisect.bisect_right(ends, value); # if the value is sitting on top of the end, it does not count in this interval, 
			if (start_ind - end_ind) == 1:
				result[end_ind].append(item)
			#print value, start_ind, end_ind
	result.insert(0, before)
	result.append(after)
	return result
	
def group_by_number_of_bins(tuple_list, key_index, number_of_bins):
	"""
	Used to bin elements of the tuple_list into number_of_bins bins
	input: 
	tuple_list: [(value, value, value, ....)]
	key_index: key used for grouping
	number_of_groups:
	return:
		list of list [[(value,value, value, ....)]]
	"""
	if is_tuplelist_sorted(tuple_list, key_index) <= 0:
		sorted_tuple_list = sorted(tuple_list, key = itemgetter(key_index))

	result = [] # list of list
	for i in xrange(number_of_bins): 
		result.append([])
	
	# round to an integer above
	if len(tuple_list)%int(number_of_bins) == 0:
		size_in_bin = len(tuple_list)/int(number_of_bins)
	else:
		size_in_bin = len(tuple_list)/int(number_of_bins) + 1
		
	for i in xrange(len(tuple_list)):
		index = i/int(size_in_bin)
		result[index].append(sorted_tuple_list[i])
	return result
	

def extract_column_from_binned_tuple_list(result, key_index):
	"""
	result: list of list [[(value,value, value, ....)]]
	"""
	myresult = []
	for item in result:
		myresult.append([myitem[key_index] for myitem in item])
	return myresult
	

"""
Dictionary Operation
"""
def get_subset_ids_from_dic(dic, idset=None):
	"""
	"""
	if idset is not None:
		mykeys = list(set(dic.keys()) & set(idset))
		if len(mykeys) < min(len(dic), len(idset)):
			print "%d ids are thrown out" % (min(len(dic), len(idset)) - len(mykeys))
	else:
		mykeys = dic.keys()
	return mykeys
	
def	get_subset_from_dic(dic, idset=None):
	"""
	"""
	mydic = {}
	if idset is not None:
		mykeys = list(set(dic.keys()) & set(idset))
		
		if len(mykeys) < min(len(dic), len(idset)):
			print "%d ids are thrown out" % (min(len(dic), len(idset)) - len(mykeys))
		for myid in mykeys:
			mydic[myid] = copy.deepcopy(dic[myid])
	else:
		mydic = copy.deepcopy(dic)
	return mydic
	
"""
File operation
"""
def rescale_a_column(input_file, c, rescale_factor, output_file):
	"""
	c is the 0-based column number 
	Return a list of names
	
	"""
	infile = open(input_file,'r')
	outfile = open(output_file, 'w')
	outfile.write('\t'.join(["#GeneName",	"Read Count",	"RPKM"])+'\n')
	for line in infile:
		if not re.match("#", line):
			line = line.strip()
			sline = line.split()
			if (len(sline)>0):
				new_value = atof(sline[c]) * rescale_factor;
				sline[c] = str(new_value);
				outfile.write('\t'.join(sline)+'\n')
	infile.close()
	outfile.close()
	
def normalize_a_column(input_file, c, output_file):
	"""
	c is the 0-based column number 
	Return a list of names
	
	"""
	line_number = 0;
	infile = open(input_file,'r')
	outfile = open(output_file, 'w')
	for line in infile:
		if not re.match("#", line):
			line = line.strip()
			sline = line.split()
			if (len(sline)>0):
				if (line_number == 0): 
					rescale_factor = atof(sline[c])
				new_value = atof(sline[c]) / rescale_factor;
				sline[c] = str(new_value);
				outfile.write('\t'.join(sline)+'\n')
				line_number += 1;
	infile.close()
	outfile.close()

def add_column (infile, c, outfile, const=-1):
	"""
	c is the 0-based column number 
	add a column to the original file 
	default value would be the line number 
	"""
	file = open(infile,'r')
	ofile = open(outfile, 'w')
	counter = 0;
	for line in file:
		if not re.match("#", line):
			counter += 1
			line = line.strip()
			sline = line.split()
			if const == -1:
				sline.insert(c, "L" + str(counter));
			else:
				sline.insert(c, str(const)); 
			line =  '\t '.join(sline) + '\n';
			ofile.write(line);
	file.close()
	ofile.close()

def extract_two_columns(gene_file, c1, c2, outfile):
	"""
	c is the 0-based column number 
	"""
	maxi = max (c1, c2);
	mini = min (c1, c2);
	file = open(gene_file,'r')
	ofile = open(outfile, 'w')
	for line in file:
		line = line.strip()
		sline = line.split()
		if len(sline)> maxi:
			outline = sline[c1] + '\t' + sline[c2] + '\n';
		elif len(sline)>mini:
			outline = sline[mini]+ '\n';
		ofile.write(outline);
	ofile.close();
	file.close();


def output_list(mylist, myfile):
	"""
	Only simple list 
	"""
	out = open(myfile, "w")
	for item in mylist:
		out.write( str(item) + "\n")
	out.close()

def output_dic(dic, myfile, sort_by = "value", reverse_order=False):
	"""
	Only simple dictionary, output in an ordered manner
	sort_by can be either "key" or "value"
	"""
	out = open(myfile, "w")
	if sort_by == "value":
		sorted_tuple_list = sorted(dic.items(), key=itemgetter(1), reverse=reverse_order)
	elif sort_by == "key" :
		sorted_tuple_list = sorted(dic.items(), key=itemgetter(0), reverse=reverse_order)
	for item in sorted_tuple_list:
		myid = item[0]
		value = item[1]
		out.write(str(myid) + "\t" + str(value) + "\n")
	out.close()

"""
Data structure manipulation
"""

def flatten(l, ltypes=(list, tuple)):
	"""
	Making a flat list out of list of lists in Python
	"""
	ltype = type(l)
	l = list(l)
	i = 0
	while i < len(l):
		while isinstance(l[i], ltypes):
			if not l[i]:
				l.pop(i)
				i -= 1
				break
			else:
				l[i:i + 1] = l[i]
		i += 1
	return ltype(l)

def get_sub_dictionary(d, keys):
	"""
	get a subset of a dictionary
	"""
	return dict((k, d[k]) for k in keys if k in d)
