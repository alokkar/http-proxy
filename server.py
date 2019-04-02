import sys,socket,time
from thread import *

listen_port = 20100
max_conn = 50
buffer_size = 8192

cache = {}

def start():
	try:
		s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		s.bind(('',listen_port))
		s.listen(max_conn)
	except Exception as e:
		print(e)
		print("Unable to start socket")
		sys.exit(2)

	while 1:
		try:
			conn,addr = s.accept()
			data = conn.recv(buffer_size)
			start_new_thread(conn_string,(conn,data,addr))
		except KeyboardInterrupt:
			s.close()
			sys.exit(1)

	s.close()

def conn_string(conn,data,addr):
	try:
		first_line = data.split('\n')[0]
		url = first_line.split(' ')[1]
		http_pos = url.find('://')

		if http_pos==-1:
			temp = url
		else:
			temp=url[(http_pos+3):]

		port_pos = temp.find(":")

		webserver_pos = temp.find("/")

		if webserver_pos == -1:
			webserver_pos = len(temp)

		webserver=""
		port = -1

		if (port_pos==-1 or webserver_pos<port_pos):
			port=80
			webserver=temp[:webserver_pos]
		else:
			port=int((temp[(port_pos+1):])[webserver_pos-port_pos-1])
			webserver=temp[:port_pos]

		proxy_server(webserver,port,conn,addr,data,url)

	except:
		pass


def cache_check(url,conn,data):
	TIMEOUT = 600
	global cache_check

	orig_url = url
	url_file=""
	for i in range(len(url)):
		if url[i]!= "/":
			url_file+=url[i]

	if url not in cache or time.time()-cache[orig_url]["time"]>=TIMEOUT:
		entry = {"time":time.time(),"calls":1}
		cache[orig_url]=entry
		return False

	cache[orig_url]["calls"]+=1

	if cache[orig_url]["calls"]<1:
		return False

	req = data.split('\r\n')
	host = req[1].split(":")[1][1:]
	if len(req[1].split(":"))<3:
		port=80
	else:
		port=int(req[1].split(":")[2])

	sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.connect((host,port))

	method = req[0].split(" ")[0]

	http_pos = url.find("://")
	if http_pos != -1:
		url=url[(http_pos+3):]

	file_pos = url.find("/")
	url = url[file_pos:]


	http_ver = req[0].split(" ")[2]


	req[0]= "{0} {1} {2}".format(method,url,http_ver)


	if cache[orig_url]["calls"]>1:
		req.insert(2,"If-Modified-Since: {0}".format(time.strftime('%a, %d %b %Y %H:%M:%S GMT',time.gmtime(cache[orig_url]["time"]))))

	new_req = ""
	for l in req:
		new_req +=(l+"\r\n")

	sock.send(new_req)

	response=sock.recv(buffer_size)
	change=False
	if "304" in response.split("\r\n"):
		change=True

	temp = response.split("\r\n")
	if not change:
		conn.send(response)
	else:
		temp2 = temp[0].split(" ")
		temp2[1] = "200"
		temp2[2] = "OK"
		temp2 = " ".join(temp2)
		temp[0]=temp2
		response="\r\n".join(temp)
		conn.send(response)

	if(cache[orig_url]["calls"]>1):
		if change:
			cache[orig_url]["calls"]=1
		else:
			with open(url_file,'r') as f:
				while True:
					data = f.read(buffer_size)
					conn.send(data)
					if not data:
						break


	if cache[orig_url]["calls"] == 1:
		cache[orig_url]["time"] = time.time()
		with open(url_file,'wb') as f:
			while True:
				data = sock.recv(buffer_size)
				f.write(data)
				conn.send(data)
				if not data:
					break

	return True


def proxy_server(webserver,port,conn,addr,data,url):
	try:
		if cache_check(url,conn,data):
			conn.close()
			sys.exit()
		s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		s.connect((webserver,port))
		s.send(data)

		while 1:
			reply =  s.recv(buffer_size)

			if (len(reply)>0):
				conn.send(reply)
				print("Sent reply")
			else:
				break
		s.close()
		conn.close()

	except Exception as e:
		print(e)
		s.close()
		conn.close()
		sys.exit(1)


if __name__ == '__main__':
	start()