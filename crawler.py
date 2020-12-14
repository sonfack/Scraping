from pymongo import MongoClient
from datetime import datetime
from htmldate import find_date
import requests
import re
from urllib.parse import urlparse, urlsplit    


class Crawler(object):
    
    def __init__(self, url,  dbName="short_news", dbHost="172.17.0.2", dbPort=27017):
        self.url = url
        self.client = MongoClient(dbHost, dbPort)
        self.db = self.client[dbName]
        dblist = self.client.list_database_names()
        if dbName in dblist:
            print("The database exists.")

            
    def getHtml(self):
        try:
            htmlPage = requests.get(self.url)
        except Exception as e:
            print(e)
            return None 
        return htmlPage.content.decode("latin-1")

    def getTitle(self):
        htmlPage = self.getHtml()
        match = re.search('<title>(.*?)</title>', htmlPage, re.IGNORECASE)
        if match:
            return match.group(1)
        else:
            return " "
    
    def getLinks(self):
        htmlPage = self.getHtml()
        if htmlPage:           
            urlParts = urlsplit(self.url)
            base = "{}://{}".format(urlParts.scheme, urlParts.netloc)
            links = re.findall('''<a\s+(?:[^>]*?\s+)?href="([^"]*)"''', htmlPage)
            for i, link in enumerate(links):    
                if not urlparse(link).netloc:
                    linkWithBase = base + link    
                    links[i] = linkWithBase       
            links =  set(filter(lambda x: 'mailto' not in x, links))            
            page = {
                'site' : self.url,
                'title': self.getTitle(),
                'published': find_date(self.url),
                'meta': self.extractInfo(),
                'links' : list(links),
                'visited': str(datetime.now())
            }
            print("URL ", self.url)
            print("Published date ", find_date(self.url))
            self.db.page.insert_one(page)
            return list(links)


    def extractInfo(self):                                
        htmlPage = self.getHtml()
        if htmlPage:
            meta = re.findall("<meta.*?name=[\"'](.*?)['\"].*?content=[\"'](.*?)['\"].*?>", htmlPage)    
            return dict(meta)
        
        
    def crawl(self):
        links = self.getLinks()
        if links:
            for link in links:
                findLink = self.db.link.find({"link":link})
                if not findLink:
                    self.db.link.insert_one({"link": link})
        url = self.db.link.find_one({'link': {"$not" : "/.*pdf$/"} })
        print(url)
        #self.db.link.delete_one({"link":url["link"]})
        #self.url = url["link"]
        #self.crawl()

if __name__=="__main__":
    url = "http://minjec.gov.cm/index.php/fr/"
    crawler = Crawler(url)
    crawler.crawl()
    
