import os
import errno
import time
		
import socket
import select

class ServerDataBuff:

	def __init__(self):
		
		self.data = ""
		self.page_type = None # 'Transfer-Encoding' or 'Content-Length'
		self.content_length = None # valid only when page_type == Content-Length is True

class Url:

	def __init__(self, url, host, uri, header):
		
		self.url = url
		self.host = host
		self.uri  = uri
		self.header = header
	
class HttpCollector:

	@staticmethod
	def start(urls, headers=None):

		if headers != None:
			assert len(urls) == len(headers)

		final_urls = []
		final_data = []

		(acc_urls, acc_data) = HttpCollector.__collect(urls, headers)
		print "The Number of Collected Page : %d" % len(acc_urls)
		
		# collect pages with return code are http 301 or 302
		url_2_header = {}
		if headers != None:
			for i in xrange(len(urls)):
				url_2_header[urls[i]] = headers[i]

		urls_301 = []
		headers_301 = None
		if headers != None:
			headers_301 = []
		for i in xrange(len(acc_data)):
			http_code = HttpCollector.__get_http_return_code(acc_data[i])
			if http_code == "200":
				final_urls.append(acc_urls[i])
				final_data.append(acc_data[i])
			elif http_code == "301" or http_code == "302":
				url = HttpCollector.__get_redirect_301_url(acc_data[i])
				urls_301.append(url)
				if headers_301 != None:
					headers_301.append(url_2_header[acc_urls[i]])
			elif http_code == None:
				pass
			else:
				pass

		if len(urls_301) > 0:
			print "URL Redirection Brgin ..."
			(urls_301, data_301) = HttpCollector.__collect(urls_301, headers_301)
			final_urls.extend(urls_301)
			final_data.extend(data_301)
			print "The Number of Collected 301 Redirect Page : %d" % len(urls_301)
			assert len(final_urls) == len(final_data)
		
		print "The Number of Total Collected Page : %d" % len(final_urls)
		print "Collection Ratio : " + str(len(final_urls)*1.0/len(urls))
		return (final_urls, final_data)

	@staticmethod
	def __get_http_return_code(data):
		
		i = data.find("HTTP/1.1 ")
		if i >= 0:
			b = i + len("HTTP/1.1 ")
			e = data.find(" ", b)
			code = data[b:e]
			return code
		else:
			return None

	@staticmethod
	def __get_redirect_301_url(data):

		try:
			b = data.index("location:") + len("location:")
		except:
			b = data.find("Location:") + len("Location:")
		e = data.find("\n", b)
		redirect_url = data[b:e].strip()
		return redirect_url

	@staticmethod
	def __collect(urls, headers=None):
		'''
		collect web pages using asynchronous method
		return : two lists, accepted_urls, accepted_data
				 which len(accepted_urls) = len(accepted_data)
		'''

		if headers != None:
			assert len(urls) == len(headers)
	
		# split url into host and uri
		hosts, uris = HttpCollector.__split_host_uri(urls)
		
		# create sockets
		sockets = []
		fd_2_sock   = {}
		fd_2_url	= {}
		fd_2_data 	= {}
	
		for i in xrange(len(hosts)):
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.setblocking(0)
			sockets.append(sock)
			fd_2_sock[sock.fileno()] = sock
			if headers != None:
				fd_2_url[sock.fileno()] = Url(urls[i], hosts[i], uris[i], headers[i])
			else:
				fd_2_url[sock.fileno()] = Url(urls[i], hosts[i]. uris[i], None)
	
		# create listener
		epoll = select.epoll()
	
		# non-blocking connect
		b = time.time()
		for i in xrange(len(sockets)):
			try:
				sockets[i].connect( (hosts[i], 80) )
			except Exception, e:
				if e.args[0] == 115:
					epoll.register(sockets[i].fileno(), select.EPOLLOUT)
				else:
					print "[Connection Error] Url %s : %s" % (urls[i], str(e))
		print "Time Consuming Of Non-Blocking Connection : " + str(time.time() - b)
	
		# listen connection result
		b = time.time()
		while True:
			events = epoll.poll(5.0)
			if len(events) == 0: break
			for fd, event in events:
				if event & select.EPOLLOUT:
					# connection event ready
					err = fd_2_sock[fd].getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
					if err == 0:
						req = HttpCollector.__generate_request(fd_2_url[fd])
						n_send = fd_2_sock[fd].send(req)
						epoll.modify(fd, select.EPOLLIN)
					else:
						print "[Connection Error] Connect %s Fail, Errno : %d" % (fd_2_url[fd].url, err)
						fd_2_sock[fd].close()
				elif event & select.EPOLLIN:
					# data is returned by server
					if not fd_2_data.has_key(fd):
						fd_2_data[fd] = ServerDataBuff()
					try:
						if HttpCollector.__read_to_buff(fd_2_sock[fd], fd_2_data[fd]) == True:
							fd_2_sock[fd].close()
					except Exception as e:
						print str(e)
						fd_2_sock[fd].close()
		print "Time Consuming Of Geting Data : " + str(time.time()-b)
	
		# return accepted_urls, accepted_data
		acc_urls = []
		acc_data = []
		for fd, server_data in fd_2_data.items():
			if HttpCollector.__has_finished_data_sending(server_data):	
				acc_urls.append(fd_2_url[fd].url)
				acc_data.append(server_data.data)
		return (acc_urls, acc_data)
		
	@staticmethod
	def __split_host_uri(urls):
		
		hosts = []
		uris  = []
		for url in urls:
			i = url.find("?")
			if i >= 0:
				tmp_str = url[i:]
				url = url.replace(tmp_str, "")
			url = url.replace("http://", "")
			pos = url.find("/")
			if pos >= 0:
				host = url[:pos]
				uri  = url[pos:]
			else:
				host = url
				uri  = "/"
			hosts.append(host)
			uris.append(uri)
		
		return hosts, uris

	@staticmethod
	def __generate_request(url):
		'''
		url is a Url object
		'''

		req = "GET " + url.uri + " HTTP/1.1\r\n"
		if url.header != None:
			req += url.header
			req += "Host:" + url.host + "\r\n"
		req += "\r\n"
		return req
	
	@staticmethod	
	def __read_to_buff(sock, buff):
		'''
		return 	True if server has finished data sending, 
				Two cases indicate the server has finished data sending:
				(1) receive a "fin" 
				(2) for "Transfer-Encoding": received "\r\n0\r\n\r\n"
				    for "Content-Length": received length of data is Satisfied
		'''
	
		while True:
			try:
				data = sock.recv(2048)
				if len(data) == 0:
					return True # (1) server has finished data sending by sending a "fin"
				buff.data += data
			except Exception as e:
				if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
					break
				raise

		if HttpCollector.__has_finished_data_sending(buff):
			return True # (2) data has been sending over, though server do not send "fin"
		else:
			return False 
	
	@staticmethod
	def __has_finished_data_sending(buff):
		'''
		return  True if buff.data is a complete response data
		'''

		if not buff.page_type:
			if buff.data.find("Transfer-Encoding") >= 0 or buff.data.find("transfer-encoding") >= 0:
				buff.page_type = "TE"
			elif buff.data.find("Content-Length") >= 0 or buff.data.find("content-length") >= 0:
				buff.page_type = "CL"
			else:
				return False
	
		if buff.page_type == "TE":
			#print "hi, i am Transfer-Encoding"
			if buff.data.find("\r\n0\r\n\r\n") >= 0:
				#print "read over!"
				return True
			else:
				return False
		
		elif buff.page_type == "CL":
			#print "hi, i am Content-Length"
			if not buff.content_length:
				b = buff.data.find("Content-Length:")
				if b < 0:
					b = buff.data.find("content-length:")
				b += len("Content-Length:")
				e = buff.data.find("\r\n", b)
				buff.content_length = int(buff.data[b:e].strip())
			b_content = buff.data.find("\r\n\r\n")+len("\r\n\r\n")
			if len(buff.data) - b_content == buff.content_length:
				#print "read over!"
				return True
			else:
				return False
	
		else:
			raise ValueError("page_type error")

if __name__ == "__main__":
	
	urls = open("urls.txt", "rb").read().strip().split()
	print "Url Number : %d" % len(urls)

	headers = []
	for i in xrange(len(urls)):
		h = ""
		#h += "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
		#h += "Accept-Encoding:gzip, deflate, sdch\r\n"
		#h += "Accept-Language:en-US,en;q=0.8\r\n"
		#h += "Cache-Control:max-age=0\r\n"
		#h += "Proxy-Connection:keep-alive\r\n"
		h += "User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36\r\n"
		headers.append(h)

	(acc_urls, acc_data) = HttpCollector.start(urls, headers)

	os.system("rm -r data")
	os.system("mkdir data")
	for i in xrange(len(acc_urls)):
		url = acc_urls[i]
		data = acc_data[i]
		with open("data/"+url.split("/")[-1]+".txt", "wb") as fo:
			fo.write(data)
