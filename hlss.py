#!/bin/python
# -*- coding: utf-8 -*- 

from hashlib import md5
import base64
import pyaes
import time
import sys
import os


sys.path.append("cachechains")
from cachechains.cachechains import *
from cachechains.secretkeyshare import *


major_version = sys.version_info.major
if major_version == 2:
	import thread
if major_version == 3:
	import _thread as thread


"""
name: hlss.py
description: High Level Secret Sharing (HLSS) algorithm. Interface for secretkeyshare.py and cachechains.py.
author: Bryan Angelo Pedrosa
date: 11/08/2019
"""


# for timeout functionality
# part - keys_metadata ; len - metadata
conf_intvl = 20.0 # timeout interval; experimental
request_sessions = {} # {batch_id:[expt, part, len]}



class AESCryptography:
	def __init__(self, key=""):
		self.aesmode = pyaes.aes.AESModeOfOperationCTR(md5("{0}".format(key).encode()).hexdigest().encode())
	
	def encrypt(self, data=""):
		if major_version == 2:
			return base64.b64encode(self.aesmode.encrypt("Ok......\n" + data)).decode("utf-8")  # 2
		elif major_version == 3:
			return base64.b64encode(self.aesmode.encrypt("Ok......\n" + data)).decode("utf-8") # 3
			#return base64.b64encode(self.aesmode.encrypt(b"Ok......\n" + data.encode('utf-8'))) # 3
	
	def decrypt(self, data=""):
		return self.aesmode.encrypt(base64.b64decode(data))


def cachechains_loop():
	try:
		while 1:
			STITCHING().build(metadata=metadata)
			time.sleep(.2)
	except Exception as er:
		print(er)


def session_timeout():
	try:
		def sessnformat(batch_id="", part=0, lenn=0):
			# set session expiration; current tm + tmout interval
			expt = time.time() + conf_intvl
			
			# create one if not in session
			if not batch_id in request_sessions:
				request_sessions[batch_id] = [expt, part, lenn]
			else:
				# get reference
				reqref = request_sessions[batch_id]
				
				# if no changes; don't renew expiration
				if reqref[1] == part: # for keys_metadata
					expt = reqref[0]
				if reqref[2] == lenn: # for metadata
					expt = reqref[0]
				
				# if zero value; use reference
				if part == 0: # for keys_metadata
					part = reqref[1]
				if lenn == 0: # for metadata
					lenn = reqref[2]
				
				# update request_sessions
				request_sessions[batch_id] = [expt, part, lenn]
			
			for batch_id,m_data in request_sessions.items():
				# if session's expired, killall inprocess
				if m_data[0] < time.time():
					# if it's in keys_metadata; remove
					if batch_id in keys_metadata:
						del keys_metadata[batch_id]
					
					# if it's in metadata; remove
					for m_data in metadata:
						if m_data[0] == batch_id:
							# delete sessions's metadata
							del metadata[m_data]
							
							# delete session's cache to prevent leaks
							clean_cache(sessn=batch_id)
							
							break
					
					# if it's in session; remove
					if batch_id in request_sessions:
						del request_sessions[batch_id]
		
		while 1:
			# track changes for keys_metadata & metadata
			for batch_id,m_data in keys_metadata.items():
				sessnformat(batch_id=batch_id, part=m_data[0])
			
			for m_data in metadata:# len changes
				sessnformat(batch_id=m_data[0], lenn=m_data[3])
			
			time.sleep(.2)
	except Exception as er:
		print(er)



# I'll just leave these here for demonstration purposes.
if __name__ == "__main__":
	data = """Somebody once told me the world is gonna roll me\nI ain't the sharpest tool in the shed\nShe was looking kind of dumb with her finger and her thumb\nIn the shape of an "L" on her forehead"""
	
	##########################
	#[thread] BOB THE BUILDER
	##########################
	# receive data chunks then merge
	thread.start_new_thread(cachechains_loop,())
	# session timeout for key/data build
	thread.start_new_thread(session_timeout,())
	
	
	##################
	# SENDER
	##################
	
	
	# generate session key
	secured_key = md5(os.urandom(64)).hexdigest()
	
	
	#[ok] data encryption
	data = AESCryptography(key=secured_key).encrypt(data=data)
	print("data: ", data)
	
	
	# split the payload
	batch_id = SPLITTING().slash(data=data)
	
	
	#split session key
	key_meta_data = split_key(batch_id, secured_key)
	
	
	# sending keys/data................
	#;building caches before exit..
	time.sleep(3)
	
	
	# *** harvesting and build keys ***
	for key_metadata in key_meta_data:
		# batch_id, part, content
		build_status = build_key(key_metadata[0], key_metadata[1], key_metadata[2])
	
	
	##################
	# RECEIVER
	##################
	# (this block is supposed to be in loop)
	# while 1:
	
	# get the 'batch_id' of finished secret keys
	for batch_id,secured_key in security_keys.items():
		# now, determine if 'metadata_done' contains 'batch_id' of session key
		if batch_id in [metadat[0] for metadat in metadata_done]:
			# read the data
			mdata = [mdata for mdata in metadata_done if mdata[0] == batch_id]
			filename = os.path.join("cache", "merged", " ".join([str(mdat) for mdat in mdata[0]]))
			with open(filename, "rb") as cachedata_rb: #, open(, "wb") as cachedata_wb:
				data = cachedata_rb.read()
			
			#[ok] data decryption
			data = AESCryptography(key=secured_key).decrypt(data=data)
			
			# use the data now!
			print("data: ", data)
			
			
			# del session key
			del security_keys[batch_id]
			
			break
	
	
	#done!!!!!






"""
I accidenally added a diary. lmao
"""



