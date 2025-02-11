# webscraping

A set of python classes that scrape business listing websites.

* Alimarket web scraper: The python class here scrapes the specified page of alimarket.es for business entries, visits the specific pages to scrape further information, and saves the results in a csv file. It takes input of business area and number of pages, which references the number of pages of business listings to scrape.
* ElEconomista web scraper: The python class takes in a csv of business names (which should be in a single column, no header, and no other information in the csv) and searches the ElEconomista website for each business. If a possible page is found, the link to possible page is saved. Then the scraper visits that page and attempts to scrape contact information. Any businesses for which no search result can be found or no contact information is found will not be included in the output file. Results are saved in a csv file.

##### Packages used:
* BeautifulSoup
* pandas
* requests
* tqdm
* json

##### Usage:
* See .ipynb files for sample code on usage. For example, alimarket-scraper-class.ipynb contains sample code for usage in lower cells.

##### Notes:
* The .json files contain headers for use with requests library. These are indexed '0' to '49'.
