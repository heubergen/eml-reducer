#!/usr/bin/env python3
from email import policy
from email.parser import BytesParser
from os import walk, path as ospath
from traceback import print_exc
from io import BytesIO

path = "./mail-archive"
fname = []
typlist = ['text/plain', 'text/html']
osize = 0
asize = 0
trivialsize = 524288 # In Bytes

for root,d_names,f_names in walk(path):
	for f in f_names:
		fname.append(ospath.join(root, f))
		
def removeAttachment(attachment):
	global nrchanges
	if attachment.get_content_type() not in typlist:
		attachment.clear()
		nrchanges += 1
		
def collectAttachments(list):
	for attachment in list.iter_attachments():
		removeAttachment(attachment)

def iterateAttachments(msg):
	for part in msg.iter_parts():
		for attachment in msg.iter_attachments():
			removeAttachment(attachment)
		if part.get_content_type().startswith('multipart'):
			for parts in part.iter_parts():
				collectAttachments(parts)
				for partss in parts.iter_parts():
					collectAttachments(partss)
			collectAttachments(part)
		
def updateFile(mailfile, msg):
	global asize
	try: #Until https://github.com/python/cpython/issues/94306 is fixed
		buffer = BytesIO()
		buffer.write(msg.as_bytes())
	except IndexError:
		print('Caught error! with ' + mailfile)
	except Exception as e:
		print_exc()
		exit()
	else:
		with open(mailfile, 'wb') as wp:
			buffer.seek(0)
			wp.write(buffer.read())
	finally:
		asize += ospath.getsize(mailfile)
		
def reducesize(mailfile):
	global osize
	global asize
	global nrchanges
	if mailfile.endswith('.eml'):
		osize += ospath.getsize(mailfile)
		if ospath.getsize(mailfile) > trivialsize:
			with open(mailfile, 'rb') as fp:
				nrchanges = 0
				msg = BytesParser(policy=policy.default).parse(fp)
				iterateAttachments(msg)
				if nrchanges > 0:
					updateFile(mailfile, msg)
				else:
					asize += ospath.getsize(mailfile)
		else:
			asize += ospath.getsize(mailfile)

def printoutput():
	global osize
	global asize
	if osize == asize:
		print("Nothing has changed")
	elif osize > 1073741824 or asize > 1073741824:
		osize = round(osize/1024/1024/1024,2)
		asize = round(asize/1024/1024/1024,2)
		print('Total old file size: ' + str(osize) + 'GB, Total new file size: ' + str(asize) + 'GB')
		pass
	elif osize > 1048576 or asize > 1048576:
		osize = round(osize/1024/1024,2)
		asize = round(asize/1024/1024,2)
		print('Total old file size: ' + str(osize) + 'MB, Total new file size: ' + str(asize) + 'MB')
	elif osize < 1024 and asize < 1024:
		print('Total old file size: ' + str(osize) + 'Bytes, Total new file size: ' + str(asize) + 'Bytes')
	else:
		osize = round(osize/1024,2)
		asize = round(asize/1024,2)
		print('Total old file size: ' + str(osize) + 'KB, Total new file size: ' + str(asize) + 'KB')

if __name__ == "__main__":
	for mailfile in fname:
		reducesize(mailfile)
	printoutput()