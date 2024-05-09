from elasticsearch7 import Elasticsearch
from elasticsearch7.client import IndicesClient
import re
import os
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer 
from tqdm import tqdm
import string
import math

def ES_search(es, query, INDEX_NAME):
    
    res_es_search = es.search(index = INDEX_NAME, query = {'match': {'content': query }} , size = 1000)
    
    return res_es_search


def output_txt(filename, string):
    output_path = './'
    with open(output_path+filename+'.txt', 'a') as f:
        f.write(string)


def process_res(es, queries, INDEX_NAME):
    i = 0
    for num, query in queries.items():
        result = ES_search(es, query, INDEX_NAME)
        for hit in result['hits']['hits']:
            docno = hit['_id']
            rank = i + 1
            score = hit['_score']
            output_line = num + ' Q0 ' + str(docno) + ' ' + str(rank) + ' ' + str(score) + ' Exp' + "\n"
            output_txt('query_result_es_builtin_hw3',output_line)
            i += 1


def main():
    INDEX_NAME = 'crawler' 
    CLOUD_ID = "6200:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyRiZTllZjE5NDRkNTg0MDE3YTU0NDg0MzcwYjk5MjQzMSQ2Zjg1ODJhNWRjMGY0NDBhODU1Njk1MDQ4NzMyNmU2Yg=="                  
    es = Elasticsearch(request_timeout = 10000, 
                        cloud_id = CLOUD_ID,
                        http_auth = ('elastic', 'fwOhKti7myB3PKFHQavQBhcr'))
    print(es.ping())
    queries = dict({'152901': 'West African Ebola epidemic', '152902': 'H1N1 Swine Flu pandemic', '152903': 'COVID 19'  })
    process_res(es, queries, INDEX_NAME)
    print('Completed')

if __name__ ==  '__main__':
    main()

