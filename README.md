高效爬虫组件 —— httpCollector<br>
=============================

适用场景<br>
--------
这不是一个像蜘蛛一样在互联网上自动收集网页的爬虫，它有特殊的适用场景。<br>
假设需要爬取百度某个贴吧的一定量帖子，一种办法是先生成这些帖子对应的URL链接，然后再爬取这些链接。<br>
当非常多的链接需要爬取时，爬取这些链接的过程可以交给httpCollector，它可以高效的完成爬取任务，并保证爬取内容的是完整的网页内容。<br>
它可以取代频繁使用python中的urlopen函数的情况。<br>

运行环境<br>
--------
Linux 2.6 或以上的内核<br>

运行示例<br>
--------
```python
import httpCollector

# 加载800个美团店家的URL地址
urls = open("urls.txt", "rb").read().strip().split()

# 设置每一个URL对应的header
headers = []
for i in xrange(len(urls)):
	h = "User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36\r\n"
	headers.append(h)

# 开始爬取
(acc_urls, acc_data) = HttpCollector.start(urls, headers)

```
acc_urls 中保存成功爬取的URL；<br>
acc_data 中保存对应的服务器返回数据。<br>
注意！：<br>
<b>httpCollector只负责请求并完整接收服务器数据，并不对数据进行任何解析，解析数据应由用户自己完成。<b><br>
