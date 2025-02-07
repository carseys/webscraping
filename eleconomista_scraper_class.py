import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from collections import Counter
import time
import json

# Author: Simone Carsey


class EconomistaScrape:
    """
    description
    """

    def __init__(self):
        self.baseurl = 'https://www.alimarket.es'
        self.table_scrape_flag = False

    def setup(self)-> None:
        with open("headers.json", "r") as f:
            headers_dict_1 = json.load(f)