import socket,sys
from threads import *

listen_port = 20100
MAX_BUFFER = 4096
max_conn = 5

def start():
	try:
		s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		s.bind('',listen_port)
		s.listen(max_conn)
	except:
		print("Unable to start socket")
		sys.exit(2)

	while 1:
		try:
			conn,addr = s.accept()
			data = conn.recv(MAX_BUFFER)
			start_new_thread(conn_string,(conn,data,addr))
		except KeyboardInterrupt:
			s.close()
			print("Bye")
			sys.exit(1)
	s.close()

def conn_string(conn,data,addr):
	try:
		first_line = data.split('\n')[0]

		url = first_line.split(' ')[1]

		http_pos = url.find("://")
		if(http_pos==1):
			temp=url
		else:
			temp=url[(http_pos+3):]
		
		port_pos = temp.find(':')
		
		webserver_pos = temp.find('/')
		
		if webserver_pos == -1:
			webserver_pos=len(temp)
		webserver=""
		port = -1
		if(port_pos == -1  or webserver_pos < port_pos):
			port = 80
			webserver = temp[:webserver_pos]
		else:
			port=int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
			webserver = temp[:port_pos]

		proxy_server(webserver,port,conn,addr,data)
	except Exception , e:
		pass

def proxy_server(webserver,port,conn,addr,data):
	try:
		s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		s.connect((webserver,port))
		s.send(data)

		while 1:
			reply = s.recv(MAX_BUFFER)

			if(len(reply)>0):
				conn.send(reply)
				dar = float(len(reply))
				dar = float(dar/1024)
				dar = "%.3s" % (str(dar))
				dar = "%s KB" % (dar)
				print("Request done %s => %s <=" % (str(addr[0])),str(dar))
			else:
				break
		s.close()
		conn.close()
	except socket.error,(value,message) :
		s.close()
		conn.close()
		sys.exit(1)

if __name__ == '__main__':
	start()
