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
    Searches empresite.eleconomista.es for businesses in provided csv and scrapes top search result's contact information.

    Parameters
    ----------


    Functions
    ---------
    setup
        Imports jsons, csv (csv as specified by filename parameter).
    url_search_term
        Takes business names and formats for use in URL.
    business_search_rotate
        Searches business names on baseurl website.
    cleanup_found_links_rotate
        Adds column of found links and removes error rows.
    get_contact_info_rotate
        Scrapes pages of found links for contact information.
    add_found_info
        Compiles new info into existing df to match businesses and info, and fixes some formatting issues.
    export_to_csv
        As the name says.
    scrape_through
        Runs all the above functions.
    """

    def __init__(self):
        self.baseurl = 'https://empresite.eleconomista.es/Actividad/'

        self.setup_flag = False
        self.business_search_flag = False
        self.cleanup_found_links_flag = False
        self.get_contact_info_flag = False
        self.add_info_flag = False

    def setup(self, filename: str)-> None:
        """
        Import requisite json files of headers from directory.
        """
        with open("headers.json", "r") as f:
            self.headers_dict_1 = json.load(f)

        with open("headers_2.json", "r") as f:
            self.headers_dict_2 = json.load(f)
        
        self.csv_entries = pd.read_csv(f'{filename}.csv', encoding ='latin1', names = ['company names'])
        self.csv_entries['company names'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

        self.setup_flag = True
        return None
    
    def url_search_term(business_name: str):
        business_name = business_name.replace(",", "")
        business_name = business_name.replace(".", "")
        url_st = business_name.upper().replace(' ', '-')
        return url_st
    
    def business_search_rotate(self, n: float):
        """
        This function searches the baseurl site for the business names given in the DataFrame csv_entries.
        
        Parameters
        ----------
        'n' : float
            number of seconds to wait after each iteration. Recommended to set 2 but higher values don't seem to improve performance.
        """
        self.link_list = []
        header_index = 0
        print("Beginning business search.")

        for i, company in enumerate(tqdm(list(self.csv_entries['company names']))):
            search_term = self.url_search_term(company)
            search_url = self.baseurl + search_term + '/'
            mini_header_dict = {
                'User-Agent' : self.headers_dict_1[str(header_index)]
            }
            try:
                r = requests.get(search_url,headers=mini_header_dict, timeout=30)
                soup = BeautifulSoup(r.content)
                # print(company)
                # print(str(r.status_code))
                try:
                    if str(r.status_code)== '200':
                        # first_result = soup.find_all('a', href=True, title=lambda value: value and value.startswith("Ver perfil de"))[0].text
                        # first_result = first_result.capitalize().split(' ')[0]
                        # company_name_start = company.split(' ')[0]
                        
                        # if first_result.split(' ')[0]==company.split(' ')[0]:
                        url_results = soup.find_all('a', href=True, title=lambda value: value and value.startswith("Ver perfil de"))[0]['href']
                        self.link_list.append(url_results)
                    elif str(r.status_code)== '429':
                        header_index = header_index + 1
                        try:
                            r = requests.get(search_url,headers=mini_header_dict, timeout=30)
                            soup = BeautifulSoup(r.content)
                            url_results = soup.find_all('a', href=True, title=lambda value: value and value.startswith("Ver perfil de"))[0]['href']
                            self.link_list.append(url_results)
                        except:
                            self.link_list.append('reset but result issue')
                    else:
                        self.link_list.append('possible 404 not found')
                except IndexError:
                    self.link_list.append('no results found')
                time.sleep(n)
            except:
                self.link_list.append('requests issue')
        self.business_search_flag = True
        print(f'The cooldown this time was {n} seconds.')
        print("Completed business search.")
        return None

    def cleanup_found_links_rotate(self) -> None:
        """
        This function adds urls to company listings that were found and removes rows of companies which were not found listed.

        Parameters
        ----------
        'df' : pd.DataFrame
            DataFrame of companies from csv import.
        'link_list' : list of links found from 'business_search' 
        """
        assert self.business_search_flag, "Please run business_search_rotate before cleanup_found_links_rotate."

        print("Cleaning up links found.")
        self.entries_with_info = self.csv_entries.copy()

        self.entries_with_info.reset_index(drop=True,inplace=True)
        self.entries_with_info['found_links'] = pd.DataFrame(self.link_list, columns=['found_links'])
        excluded_rows = self.entries_with_info[(self.entries_with_info['found_links']=='possible 404 not found') | (self.entries_with_info['found_links']=='reset but result issue') | (self.entries_with_info['found_links']=='429 issue') | (self.entries_with_info['found_links']=='requests issue')].index
        self.entries_with_info.drop(index=excluded_rows, inplace=True)
        self.entries_with_info = self.entries_with_info.drop_duplicates(subset=['found_links'], keep=False) #mutiplicities of url found are generally because of search issues
        self.entries_with_info = self.entries_with_info.dropna(subset='found_links')
        self.entries_with_info.reset_index(drop=True,inplace=True)
        self.cleanup_found_links_flag = True
        print("Link results cleaned.")
    
        return None
    
    def get_contact_info_rotate(self, n: int):
        """
        This company scrapes info of companies for which links were found.

        Parameters
        ----------
        'df' : pd.DataFrame
        """
        assert self.cleanup_found_links_flag, "Please run cleanup_found_links_rotate before get_contact_info_rotate."
        phonenumbers_found = []
        urls_found = []
        emails_found = []
        header_index = 0
        print("Scraping for contact information.")

        for i, link in enumerate(tqdm(self.entries_with_info['found_links'])):
            mini_header_dict = {
                'User-Agent' : self.headers_dict_2[str(header_index)]
            }
            r = requests.get(link,headers=mini_header_dict, timeout=20)
            if r.status_code == 429:
                header_index = header_index + 1
                r = requests.get(link,headers=mini_header_dict, timeout=20)
            if (r.status_code != 200) & (r.status_code != 429):
                print(str(r.status_code))
            soup = BeautifulSoup(r.content)
            try:
                found_url = soup.find_all('a', href=True, target = '_blank', class_ = lambda value: value and value.startswith('text-bodytext-m text-secondary-800 underline'))[0]['href']
            except:
                found_url='not found'
            urls_found.append(found_url)
            try:
                found_email = soup.find_all('a', href=True, target = '_blank', class_ = lambda value: value and value.startswith('text-bodytext-m text-secondary-800 underline email'))[0]['href'].split('?')[0]
            except:
                found_email = 'not found'
            emails_found.append(found_email)
            try:
                found_phone = soup.find_all('span', class_=lambda value: value and value.startswith('text-bodytext-m text-neutrals-700 md:block hidden'))[0].text
            except:
                found_phone = 'not found'
            phonenumbers_found.append(found_phone)
            time.sleep(n)

        self.info_dict = {'phones': phonenumbers_found, 'urls': urls_found, 'emails': emails_found}
        self.get_contact_info_flag = True
        print(f'The cooldown this time was {n} seconds.')
        print("Contact information scraped.")
        return None

    def add_found_info(self)-> None:
        """
        compiles phone numbers, emails, urls into df and fixes some formatting issues.

        Parameters
        ----------
        """
        print("Compiling information into df and cleaning results.")
        assert self.get_contact_info_flag, "Please run get_contact_info_rotate before add_found_info."

        phone_list = self.info_dict['phones']
        url_list = self.info_dict['urls']
        email_list = self.info_dict['emails']
        
        self.entries_with_info['phones'] = pd.DataFrame(phone_list, columns=['phones'])
        self.entries_with_info['urls'] = pd.DataFrame(url_list, columns=['urls'])
        self.entries_with_info['emails'] = pd.DataFrame(email_list, columns=['emails'])

        # Cleaning Results:
        self.entries_with_info['urls'] = self.entries_with_info['urls'].apply(lambda x: 'not found' if x.startswith('mailto')==True else x)
        self.entries_with_info['urls'] = self.entries_with_info['urls'].apply(lambda x: 'not found' if x.startswith('https://ranking-empresas.eleconomista.es/')==True else x)

        # Format corrections:
        self.entries_with_info['urls'] = self.entries_with_info['urls'].apply(lambda x: x[2:] if x.startswith('//')==True else x)
        self.entries_with_info['emails'] = self.entries_with_info['emails'].apply(lambda x: x.split(':')[1] if x.startswith('mailto')==True else x)
        self.entries_with_info.drop(columns=['found_links'],inplace=True)

        # Removing companies w no info:
        no_info_indices = self.entries_with_info.loc[(self.entries_with_info['emails']=='not found') & (self.entries_with_info['phones']=='not found') & (self.entries_with_info['urls']=='not found')].index
        self.entries_with_info.drop(index = no_info_indices, inplace=True)
        self.entries_with_info.reset_index(drop=True, inplace=True)
        self.add_info_flag = True
        print("Information compiled and cleaned.")
        return None
    
    def export_to_csv(self, newfilename: str)-> None:
        assert self.add_info_flag, "Please run add_found_info before export_to_csv."
        self.entries_with_info.to_csv(f'{newfilename}.csv')
        print("Successfully exported csv.")
        return None
    
    def scrape_through(self, filename: str, n: float, newfilename: str):
        """
        Runs from start to end through the scraping process.

        Parameters
        ----------
        'filename' : str
        'n' : float
        'newfilename' : str
        """

        self.setup(filename=filename)
        self.business_search_rotate(n=n)
        self.cleanup_found_links_rotate()
        self.get_contact_info_rotate(n=n)
        self.add_found_info()
        self.export_to_csv(newfilename=newfilename)
        