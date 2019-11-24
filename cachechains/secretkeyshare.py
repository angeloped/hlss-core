#!/bin/python
# -*- coding: utf-8 -*- 

import os
from hashlib import md5
from operator import itemgetter

"""
name: secret_share.py
description: Algorithm for secure multi-circuit key distribution.
             This will add another extra layer of security when sharing encryption keys for every encrypted requests.
             Similar technique used in the distribution of missile launch codes, numbered bank accounts, etc.
learn more: https://en.wikipedia.org/wiki/Secret_sharing
author: Bryan Angelo Pedrosa
date: 10/02/2019
"""


security_keys = {} # [now called a session] {batch_id:key}
keys_metadata = {} # [in process] {batch_id:[[part, content],..] ,..}


def split_key(batch_id, data_key):
	key_parts = []
	
	n = 1
	while len(data_key):
		data_key_chunk = data_key[:4]
		data_key = data_key[4:]
		
		# append chunk
		key_parts.append([batch_id, n, data_key_chunk])
		
		# increment part number
		n += 1
	
	return key_parts



def build_key(batch_id, part, content): # try to build a shared key
	# add new secret share batch list
	if not batch_id in keys_metadata:
		keys_metadata[batch_id] = list()
	
	# make sure part has no duplicate
	hasduplicate = False
	for key_mdata in keys_metadata[batch_id]:
		if key_mdata[0] == part:
			hasduplicate = True
			break
	
	if not hasduplicate:
		# finally, append to keys_metadata
		#print("push: {0}: {1}, {2}".format(batch_id, part, content))
		keys_metadata[batch_id].append([part, content])
	
	# get the data and metadata info ; get [[part, content],..]
	batch_mdata = keys_metadata[batch_id]
	
	# determine if whole batch is completed
	if len(batch_mdata) == 8: # 8 is total shared key parts
		# sort batch parts in ascending order
		batch_mdata = sorted(batch_mdata, key=itemgetter(0))
		
		# extract only the content & join together & push to security_keys
		security_keys[batch_id] = "".join([mdata[1] for mdata in batch_mdata])
		
		# remove from keys_metadata
		del keys_metadata[batch_id]
		
		print("[{0}] -- secret shared key build.".format(batch_id))
		
		return True
	else:
		return False



# I'll just leave this here for demonstration purposes.
if __name__ == "__main__":
	for i in range(3):
		# encryption key for the session
		batch_id = md5(os.urandom(64)).hexdigest()
		secured_key = md5(os.urandom(64)).hexdigest()
		
		key_meta_data = split_key(batch_id, secured_key)
		
		# build key for every batch
		for key_metadata in key_meta_data:
			# batch_id, part, content
			build_status = build_key(key_metadata[0], key_metadata[1], key_metadata[2])
	
	# print all processed secret keys data
	print("printing all constructed keys....")
	print(security_keys)




