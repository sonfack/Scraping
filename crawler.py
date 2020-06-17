from pymongo import MongoClient
from datetime import datetime
import requests
import re
from urllib.parse import urlparse, urlsplit    


class Crawler(object):
    
    def __init__(self, startUrl):
        self.startUrl = startUrl
        self.visitedUrl = set()


    def getHtml(self, url):
        try:
            htmlPage = requests.get(url)
        except Exception as e:
            print(e)
            return None 
        return htmlPage.content.decode("latin-1")

    def getLinks(self, url):
        client = MongoClient("172.17.0.2", 27017)
        htmlPage = self.getHtml(url)
        if htmlPage:           
            urlParts = urlsplit(url)
            base = "{}://{}".format(urlParts.scheme, urlParts.netloc)
            links = re.findall('''<a\s+(?:[^>]*?\s+)?href="([^"]*)"''', htmlPage)
            for i, link in enumerate(links):    
                if not urlparse(link).netloc:
                    linkWithBase = base + link    
                    links[i] = linkWithBase       

            setLinks =  set(filter(lambda x: 'mailto' not in x, links))
            page = {
                "url": url,
                "title":"ici le titre",
                "description": "text",
                "keywords":["news"],
                "links": setLinks,
                "date":datetime.now()
            }
            db = client.shortnews
            db.page.insert_one(page)
            return setLinks


    def extractInfo(self, url):                                
        htmlPage = self.getHtml(url)
        if htmlPage:
            meta = re.findall("<meta.*?name=[\"'](.*?)['\"].*?content=[\"'](.*?)['\"].*?>", htmlPage)    
            return dict(meta)    


    def crawl(self, url):                   
        for link in self.getLinks(url):    
            if link in self.visitedUrl:        
                continue                                    
            self.visitedUrl.add(link)            
            print(self.extractInfo(link))    
            self.crawl(link)                  

    
    
    def start(self):
        self.crawl(self.startUrl)

if __name__=="__main__":
    crawler = Crawler("http://minjec.gov.cm/index.php/fr/")
    crawler.start()
