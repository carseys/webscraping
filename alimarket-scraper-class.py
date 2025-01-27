import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

# Author: Simone Carsey

class AMScrape:
    """Class that scrapes business data from alimarket.es.
    Data in particular is scraped from https://www.alimarket.es/buscador_empresas_resultados, based on 'area' specified in the string.
    
    Parameters
    ----------
    'area' : str
        Corresponds to the term in Spanish given on the website, such as 'electro' or 'construccion';
        In particular it must be the term in spanish that then is in the url once the filter is applied.
    
    Functions
    ---------
    table_scrape
        does initial scrape of list in table.
    get_details
        takes links from table_scrape and from each specific business page scrapes the phone number and address if they are listed.
    more_details
        goes to secondary site using link from alimarket and attempts to scrape for phone, email, and website.
    save_as_excel
        saves the scraped data as an excel file, named based on the area of business specified.
    """

    def __init__(self, area:str):
        self.area = area
        self.baseurl = 'https://www.alimarket.es'
        self.headers = {
        'User-Agent =': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.58 Safari/537.36 (AirWatch Browser v21.09.0.9)'
        }
        self.table_scrape_flag = False
        self.details_flag = False
        self.moredetails_flag = False

    def table_scrape(self,pages:int=None) -> None:
        """This function scrapes the company names, sectors, regions, and links from website table, for pages of listings under a certain area.
        It uses the business area and number of pages specified with the class initialization.
        """
        self.company_names = []
        self.region = []
        self.activity_sector = []
        self.company_urls = []
        self.table_scrape_flag = True

        if pages is None:
            r = requests.get(f'https://www.alimarket.es/buscador_empresas_resultados/area-{self.area}/pagina-1')
            soup = BeautifulSoup(r.content)
            self.pages = int(soup.find('span', class_='total-page').text.split(sep=" ")[0])
        else:
            self.pages = pages

        for self.pages in tqdm(range(1,self.pages+1)):
            r = requests.get(f'https://www.alimarket.es/buscador_empresas_resultados/area-{self.area}/pagina-{self.pages}')

            soup = BeautifulSoup(r.content)

            tables = soup.findChildren('table')
            my_table = tables[0]
            rows = my_table.findChildren(['tr'])

            for row in rows:
                cells = row.findChildren('td')
                for cell_no, cell in enumerate(cells):
                    value = cell.string
                    #print("The value in this cell is %s" % value)
                    if cell_no%3 == 0:
                        self.company_names.append(value)
                    if cell_no%3 == 1:
                        self.region.append(value)
                    if cell_no%3 == 2:
                        self.activity_sector.append(value)

            for company in rows:
                for link in company.find_all('a', href=True):
                    self.company_urls.append(self.baseurl+link['href'])
            #        print(link['href'])
        return None
    
    def get_details(self) -> None:
        """This function scrapes extra details of phone number and address if publicly available using links scraped using the table_scrape function."""
        assert self.table_scrape_flag, "Please run table_scrape before get_details."
        self.company_phone = []
        self.company_address = []
        self.details_flag = True
        self.secondary_links = []

        for url in tqdm(self.company_urls):
            r = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(r.content)
            for dt, dd in zip(soup.select('#main-inner dl > dt'),
                            soup.select('#main-inner dl > dd')):
                if 'Dirección' in dt.text.strip():
                    address = dd.text.strip()
                if 'Contacto' in dt.text.strip():
                    phone = dd.get_text(separator=" ").strip()
                    if phone == "Contenido exclusivo para suscriptores o compra":
                        phone = "Phone number not found."
            try:
                secondary_link = soup.find_all('a', class_='btn', target='_blank', href=True)[0].attrs['href']
            except IndexError:
                secondary_link = "not found"

            self.company_phone.append(phone)
            self.company_address.append(address)
            self.secondary_links.append(secondary_link)
        return None
    
    def more_details(self) -> None:
        """This function goes to secondary site and attemps to scrape for phone number, website, and email using links from each alimarket listing obtained in get_details function."""
        assert self.details_flag, "Please run get_details before more_details."
        self.moredetails_flag = True
        self.company_websites = []
        self.company_phones_two = []
        self.company_emails = []
        for url in tqdm(self.secondary_links):
            if url == "not found":
                self.company_websites.append("Website not found. Secondary link not found.")
                self.company_phones_two.append("Phone number not found. Secondary link not found.")
                self.company_emails.append("Email not found. Secondary link not found.")
            else:
                r = requests.get(url)
                soup = BeautifulSoup(r.content)
                try:
                    information_table = soup.find('table', id='tablaInformacionGeneral')
                    table_cells = information_table.select('td')
                    email_var = False
                    phone_var = False
                    website_var = False
                    for i,entries in enumerate(table_cells):
                        entries = entries.text.strip()
                        if entries in ['Email:']:
                            self.company_emails.append(table_cells[i+1].text.strip())
                            email_var = True
                        if entries in ['Teléfono:']:
                            self.company_phones_two.append(table_cells[i+1].text.strip().split(sep=" ")[0])
                            phone_var = True
                        if entries in ['Sitio Web:']:
                            self.company_websites.append(table_cells[i+1].text.strip())
                            website_var = True
                    if email_var == False:
                        self.company_emails.append("Email not found.")
                    if phone_var == False:
                        self.company_phones_two.append("Phone number not found.")
                    if website_var == False:
                        self.company_websites.append("Website not found.")
                except AttributeError:
                    self.company_websites.append("Website not found. Secondary link issue.")
                    self.company_phones_two.append("Phone number not found. Secondary link issue.")
                    self.company_emails.append("Email not found. Secondary link issue.")

    def save_as_excel(self,directory=None) -> None:
        """This function saves scraped data as an excel file, in directory specified if given."""
        assert self.moredetails_flag, "Please run more_details before save_as_excel."
        data = {
            'Company Name': self.company_names,
            'Region': self.region,
            'Activity Sector': self.activity_sector,
            'Company Phone': self.company_phone,
            'Company Phone 2': self.company_phones_two,
            'Company Address': self.company_address,
            'Company Email': self.company_emails,
            'Company Website': self.company_websites
        }
        df = pd.DataFrame(data=data)
        df.to_excel(f'alimarket_scraped_{self.area}.xlsx', index=False)
        print(f'saved excel of {self.area} now.')
        return None