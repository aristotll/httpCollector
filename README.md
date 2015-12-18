高效爬虫组件 —— httpCollector<br>
=============================

适用场景<br>
--------
当有非常多的链接需要爬取时，爬取链接的过程可以交给`httpCollector`，它可以高效的完成爬取任务，并保证爬取完整的网页内容。<br>
利用`httpCollector`可以取代频繁调用urlopen的情况。<br>

运行环境<br>
--------
Linux 2.6 或以上的内核<br>

运行示例<br>
--------
```python
import httpCollector

# 加载800个美团店家的URL地址
urls = open("urls.txt", "rb").read().strip().split()

# 用户需要设置每一个http请求对应的header
headers = []
for i in xrange(len(urls)):
	h = "User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36\r\n"
	headers.append(h)

# 开始爬取
(acc_urls, acc_data) = HttpCollector.start(urls, headers)
```
acc_urls 中保存成功爬取的URL；<br>
acc_data 中保存对应的服务器返回数据。<br>
<b>注意！：</b><br>
<b>httpCollector只负责请求并完整接收服务器数据</b><br>
<b>服务器返回数据包含HTTP协议头部和内容，内容可能是UTF-8编码，可也能经过gzip压缩，需要用户自己查看数据类型并解析</b><br>

支持<br>
----
`HTTP 1.1` 协议中`GET`请求<br>
`HTTP 301`和`HTTP 302`重定向<br>

不支持<br>
------
`Https`协议<br>
被`墙`的网页也无法爬取<br>
