'''
Created on Sep 28, 2013

@author: ralekar
'''
import urllib
import json
import requests
import string
import xmltodict

class NewsFeed:
    
    def __init__(self):
        print "Yahoo Query Language"
        
    ''' Rest Call to Yahoo Query Language ''' 
    def get_entities(self,table,text):
        url = "http://query.yahooapis.com/v1/public/yql?q=select * from "+table+" where text=\""+text+"\"+&format=json"
        u = urllib.urlopen(url)
        data = u.read()    
        return data
    
 
class Search_Api:
    
    bing_search_api = "https://api.datamarket.azure.com/Data.ashx/Bing/Search/v1/Composite?"
    bing_syms_api = "https://api.datamarket.azure.com/Bing/Synonyms/v1/GetSynonyms"
    
    def __init__(self, key):
        self.key = key
        self.skip = 0
        self.params = {
              #'format': 'json',
              '$top': 30,
              '$skip': self.skip}
       

    def replace_symbols(self, request):
 
        request = string.replace(request, "'", '%27')
        request = string.replace(request, '"', '%27')
        request = string.replace(request, '+', '%2b')
        request = string.replace(request, ' ', '%20')
        request = string.replace(request, ':', '%3a')
        return request
        
    def search(self, sources, query):
        request =  'Sources="' + sources    + '"'
        request += '&Query="'  + str(query) + '"'
        for key,value in self.params.iteritems():
            request += '&' + key + '=' + str(value) 
        request = self.bing_search_api + self.replace_symbols(request)
        xml = requests.get(request, auth=(self.key, self.key))
        json_response = xmltodict.parse(xml.text)
        return json.dumps(json_response)
     
    def synonyms(self,entity):
        request = '?Query="'  + str(entity) + '"'
        request = self.bing_syms_api + self.replace_symbols(request)
        r=requests.get(request, auth=(self.key, self.key))
        json_response = xmltodict.parse(r.text)
        return json.dumps(json_response)
    

if __name__ == '__main__' :
    
    ''' TEST THE API '''
    feed = NewsFeed()
    print feed.get_entities("contentanalysis.analyze","Mitt Romney had a nice time talking to Monica Lewinsky")
    
    my_key = "1CwlOHlzyZJU60mk8lHl6L83DLl+LJuK5ayKz4Q9rAA"
    query_string = "Brad Pitt"
    bing = Search_Api(my_key)
    
    print bing.search('news',query_string)
    bing.skip=100
    print bing.search('news',query_string)
    #print bing.synonyms("apple")
    
    
    
    