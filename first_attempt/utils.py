import random
user_id = None

def get_id():
	global user_id
	if not user_id:
		user_id = bytearray(random.getrandbits(8) for _ in range(20))
		user_id[0:7] = str('nekitos').encode()
	return user_id
