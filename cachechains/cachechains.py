#!/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import os
import base64
from hashlib import sha256


"""
subject: Experimental Fragments Processing (Experiment A)
description: A Dispersal Algorithm used in splitting and stitching msg fragments. This is a snippet for ANNNet.
author: Bryan Angelo Pedrosa
date: 9/10/2019


metadata information example:
*
	chain-ini: 87428fc522803d31065e7bce3cf03fe475096631e5e07bbd7a0fde60c4cf25c7   // start of chain
	chain-end: 0263829989b6fd954f72baaf2fc64bc2e2f01d692d4de72986ea808f6e99813f   // end of chain
	chain-sha: 539b9f77a4c9840da32d59e50ed831be29f06bedd25b62c21029078cfb1712a0   // chain batch's hash id
	chain-set: 123409                                                             // chain parts
	chain-get: 4563                                                               // total chained parts
*
"""



chunk_sz  = 63000 # max data to split; standard size, don't change!
qty_circuit = 13 # 13 circuit as default, you can change this 


metadata_done = [] # [done building] [[batch_id, start, end, fixed len, len],]
metadata = [] # [in process] [[batch_id, start, end, fixed len, len],]


#### Cache File Management ####
def clean_cache(sessn=""):
	inprocs = os.path.join("cache","inprocess")
	merged  = os.path.join("cache","merged")

	for paths in ["cache", inprocs, merged]:
		# create path if it's non-existent
		if not os.path.exists(paths):
			print("[!] No {0} path found. Creating one.....".format(paths))
			os.mkdir(paths)
		
		# remove leftovers from cache folder
		for cachefl in os.listdir(paths):
			filename = os.path.join(paths, cachefl)
			
			if sessn != "" and len(filename.split()) == 5:
				# clean a session's data
				if os.path.isfile(filename) and sessn == filename.split()[0]:
					print("deleting session cache: '{0}'".format(filename))
					os.remove(filename)
			elif os.path.isfile(filename):
				# clean all data at the moment
				print("deleting dirty cache: '{0}'".format(filename))
				os.remove(filename)




#### The Dispersal Algorithm (splitter) ####
class SPLITTING:
	def __init__(self):
		self.total_parts = 0      # parts to be registered
		self.regtred_parts = 0    # total registered parts
		self.BATCH_ID_HASH = sha256(os.urandom(64)).hexdigest() # batch hash id
		self.recent_EOC_hash = "" # recent end of chain hash
	
	
	def regtr(self, chopped_data=""):
		# generate chain hash for next chunk
		SEEDCHUNK_HASH = sha256("{0}{1}{2}".format(sha256(os.urandom(64)).hexdigest(), self.BATCH_ID_HASH, chopped_data).encode()).hexdigest()
		
		# increment registered chunks indicator
		self.regtred_parts += 1
		
		# decide how metadata stamp would be added on each chopped data
		if not bool(self.recent_EOC_hash): # recent EOC is empty; initial process
			chunk_metadata = [self.BATCH_ID_HASH, "INIT", SEEDCHUNK_HASH, self.total_parts, 1]                  # batch_id, initial, next
		elif self.total_parts == self.regtred_parts: # total & registered parts match; end of process
			chunk_metadata = [self.BATCH_ID_HASH, self.recent_EOC_hash, "FINL", self.total_parts, 1]            # batch_id, prev, final
		elif bool(self.recent_EOC_hash): # EOC aren't empty; internal process
			chunk_metadata = [self.BATCH_ID_HASH, self.recent_EOC_hash, SEEDCHUNK_HASH, self.total_parts, 1]    # batch_id, prev, next
		
		# push chunk_metadata to metadata
		metadata.append(chunk_metadata)
		
		# push next hash to self.recent_EOC_hash
		self.recent_EOC_hash = SEEDCHUNK_HASH
		
		# split cache file... save chopped_data
		filename_s = os.path.join("cache", "inprocess", " ".join([str(meta_d) for meta_d in chunk_metadata]))
		with open(filename_s, "wb") as cache_fs:
			#cache_fs.write(base64.b64encode(chopped_data))
			cache_fs.write(chopped_data.encode())
	
	
	def slash(self, data=""):
		# how much chunks will be distributed equally
		circuit_chunk_sz = int(len(data) / qty_circuit)
		
		# slice by 'qty_circuit'
		# then slice by chunk_sz
		# split by 1 if data length lower than circuit
		if len(data) <= qty_circuit and len(data) != 0:    # single buffer
			self.total_parts = len(data)
			chunk_buffer = 1
		elif circuit_chunk_sz > chunk_sz:                  # standard size buffer
			chunk_buffer = chunk_sz
			# determine total iterations
			self.total_parts = len(data) // chunk_sz
			if bool(len(data) % chunk_sz):
				self.total_parts += 1
		elif circuit_chunk_sz <= chunk_sz:                 # custom size buffer
			chunk_buffer = circuit_chunk_sz
			# determine total iterations
			self.total_parts = len(data) // circuit_chunk_sz
			if bool(len(data) % circuit_chunk_sz):
				self.total_parts += 1 
		elif len(data) == 0:
			raise ValueError("class SPLITTING: Couldn't process 0 length data.")
		else:
			raise ValueError("class SPLITTING: Unknown error. datatype: {0} ; length: {1}".format(type(data), len(data)))
		
		# data chopping loop
		while bool(data):
			chopped_data = data[:chunk_buffer]
			data = data[chunk_buffer:]
			self.regtr(chopped_data=chopped_data)
		
		# return hash id
		return self.BATCH_ID_HASH




#### The Dispersal Algorithm (merger) ####
class STITCHING:
	# merging two metadata as well as cache data
	def merge(self, metadata_a, metadata_b):
		merge_status = False
		merge_output = None
		merge_order = None
		if metadata_a[0] == metadata_b[0]:
			# merge if inner fragment identifier match
			if metadata_a[2] == metadata_b[1]: # merge order (ascending): metadata_a - metadata_b
				merge_status = True
				merge_order = "ASCD" # ascending
				merge_output = [metadata_a[0], metadata_a[1], metadata_b[2], metadata_a[3], (metadata_a[4] + metadata_b[4])]
			elif metadata_b[2] == metadata_a[1]: # merge order (desceding): metadata_b - metadata_a
				merge_status = True
				merge_order = "DESC" # desceding
				merge_output = [metadata_a[0], metadata_b[1], metadata_a[2], metadata_a[3], (metadata_a[4] + metadata_b[4])]
		
		return (merge_status, merge_output, merge_order)
	
	
	# building fragments
	def build(self, metadata=[]):
		while len(metadata):
			metadata_index_f = 0
			while len(metadata) and len(metadata) > metadata_index_f:
				metadata_index_s = 0
				while len(metadata) and len(metadata) > metadata_index_s:
					metadata_frag_f = metadata[metadata_index_f]
					metadata_frag_s = metadata[metadata_index_s]
					metadata_resp = self.merge(metadata_frag_f, metadata_frag_s)
					
					# if metadata has completely merged
					if metadata_frag_f[3] == metadata_frag_f[4]:
						# move to metadata_done
						metadata_done.append(metadata.pop(metadata_index_f)) #[,,,]
						
						# move this file to the merged
						filename_fr = os.path.join("cache", "inprocess", " ".join([str(meta_d) for meta_d in metadata_frag_f]))
						filename_to = os.path.join("cache", "merged", " ".join([str(meta_d) for meta_d in metadata_frag_f]))
						os.rename(filename_fr, filename_to)
						
						break
						
					elif metadata_resp[0]:
						# update metadata that has merged
						metadata.append(metadata_resp[1])
						
						# remove two metadata that has merged
						metadata.remove(metadata_frag_f)
						metadata.remove(metadata_frag_s)
						
						# merge two cache files to form new entity...
						filename_m = os.path.join("cache", "inprocess", " ".join([str(meta_d) for meta_d in metadata_resp[1]])) # 
						filename_a = os.path.join("cache", "inprocess", " ".join([str(meta_d) for meta_d in metadata_frag_f]))  # 
						filename_b = os.path.join("cache", "inprocess", " ".join([str(meta_d) for meta_d in metadata_frag_s]))  # 
						
						# merge the two via file i/o
						with open(filename_m, "a") as cache_fm, open(filename_a, "rb") as cache_fa, open(filename_b, "rb") as cache_fb:
							if metadata_resp[2] == "ASCD":
								#cache_fm.write(base64.b64encode(base64.b64decode(cache_fa.read()) + base64.b64decode(cache_fb.read())))
								cache_fm.write(cache_fa.read().decode("utf-8") + cache_fb.read().decode("utf-8")) # no encoding
							elif metadata_resp[2] == "DESC":
								#cache_fm.write(base64.b64encode(base64.b64decode(cache_fa.read()) + base64.b64decode(cache_fb.read())))
								cache_fm.write(cache_fb.read().decode("utf-8") + cache_fa.read().decode("utf-8")) # no encoding
						
						# delete two cache files that has merged
						os.remove(filename_a)
						os.remove(filename_b)
						
						break
					
					metadata_index_s += 1
				metadata_index_f += 1



# clean cache at start
clean_cache()


# I'll just leave these here for demonstration purposes.
if __name__ == "__main__":
	print("[+] starting up....")
	
	import time
	import atexit
	
	uh = time.time()
	
	data = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz" * 999
	"""
	metadata = [
		# Sample batch A
		["a_sample_batch", "a", "b", 4, 1],
		["a_sample_batch", "c", "d", 4, 1],
		["a_sample_batch", "b", "c", 4, 1],
		["a_sample_batch", "d", "e", 4, 1],
		# Sample batch B
		["b_sample_batch", "a", "b", 4, 1],
		["b_sample_batch", "c", "d", 4, 1],
		["b_sample_batch", "b", "c", 4, 1],
		["b_sample_batch", "d", "e", 4, 1]
	]
	"""
	
	batch_id = SPLITTING().slash(data=data)
	print(time.time() - uh)
	#print(metadata)
	#print(batch_id)
	
	STITCHING().build(metadata=metadata)
	print(time.time() - uh)
	
	print(metadata_done)
	
	# clean cache at exit
	#atexit.register(clean_cache)
	
	print("[+] exitting....")




