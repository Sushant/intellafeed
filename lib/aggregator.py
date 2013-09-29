'''
Created on Sep 28, 2013

@author: ralekar
'''
import string
import unicodedata, re, json
from news_feed import News_Feed, Search_Api 
import params, sys
import nltk   
from urllib import urlopen
import mongo_handler
import operator

class Aggregator :
    ''''1. Take the input in the form of dictionary yahoo term extraction tool
    2. Calculate the Score of the terms in the document
    3. take it and run on bing search and get the urls
    3. Run the term extraction for each url
    4. Take the First scores as the centroids and form the clusters for each term 
    5. Find the common urls and rank them according to date and then cumulative scores
    '''
    def __init__(self):
        self.news = News_Feed()
        my_key = params.BING_API_KEY
        self.news_search = Search_Api(my_key)
        self.org_feed = None
        self.original = False
        self.data = open("test.txt", "r").read()
        self.mongo = mongo_handler.MongoHandler() 
        #print self.mongo.db.entity_score.find()
        self.entities = {}
        self.feed_list = []
        self.url_scores = {}
        
    def clean_text(self, data):
        return re.sub('[^A-Za-z0-9]+', ' ', data)
 
    def get_feed_object(self, data):
        # print self.news.get_entities("contentanalysis.analyze", self.clean_text(data))
        try:
           return json.loads(self.news.get_entities("contentanalysis.analyze", self.clean_text(data)))
        except:
           pass
        return None 
        
    def get_feed_entities(self, data):
        
        try: 
            if self.original == False :
               self.org_feed = self.get_feed_object(data)
               feed = self.org_feed
               self.original = True
               self.feed_list.append(self.org_feed)
            else :     
               feed = self.get_feed_object(data)
               
            query = ""
            if feed['query']['results']['entities']['entity']:
               for entity in feed['query']['results']['entities']['entity']:
                   if float(entity['score']) >= 0.80 :
                       self.entities[entity['text']['content']] = entity['score']
                       query += entity['text']['content'] + "+"
            if query[-1] == "+" :
               return query[:-1]
            return query
            
        except :
            #print "Error in getting the news entities"
            pass    
        return None
   
    def get_search_urls(self, data=None):
        query = self.get_feed_entities(self.data)
        result = self.news_search.search('news', query)
        for row in result['d']['results']:
            if row['News']:
               for url in row['News']:
                   text = self.html_to_text(url['Url'])
                   content_analysis = self.get_feed_object(text)
                   self.set_entities_url_score(content_analysis, url['Url'])
        sorted_x = sorted(self.url_scores.iteritems(), key=operator.itemgetter(1))
        URLS = []
        for i in range(len(sorted_x)):
            URLS.append(sorted_x[i][0])
        return URLS
            
    def set_entities_url_score(self,content_analysis,url):
        try:
            temp_entities = {}
            score = 0.0
            s=0.0
            if content_analysis['query']['results']['entities']['entity']:
                
               for entity in content_analysis['query']['results']['entities']['entity']:
                   if entity['text']['content'] in self.entities:
                         s+=float(entity['score'])-float(self.entities[entity['text']['content']])
            self.url_scores[url]=s
                                     
        except:
            pass                        
                   
                           
    def html_to_text(self, url):
        html = urlopen(url).read()    
        return nltk.clean_html(html)  
           
                        
    

    
y = Aggregator()
y.get_search_urls()
y.news_search.skip += 100
y.get_search_urls()
#print bing.search('news',query_string)
#bing.skip=100
#print bing.search('news',query_string)        
     
