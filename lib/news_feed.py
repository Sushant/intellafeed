'''
Created on Sep 28, 2013

@author: ralekar
'''
import urllib
import json
import requests
import string

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
    
    bing_api = "https://api.datamarket.azure.com/Data.ashx/Bing/Search/v1/Composite?"
    
    def __init__(self, key):
        self.key = key
        self.params = {'ImageFilters':'"Face:Face"',
              '$format': 'json',
              '$top': 10,
              '$skip': 0}
        

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
        request = self.bing_api + self.replace_symbols(request)
        return requests.get(request, auth=(self.key, self.key))

    

if __name__ == '__main__' :
    
    ''' TEST THE API '''
    feed = NewsFeed()
    print feed.get_entities("contentanalysis.analyze","Mitt Romney had a nice time talking to Monica Lewinsky")
    
    my_key = "1CwlOHlzyZJU60mk8lHl6L83DLl+LJuK5ayKz4Q9rAA"
    query_string = "Brad Pitt"
    bing = Search_Api(my_key)
    
    print bing.search('image+web',query_string).json() # requests 1.0+
    
    
    
    