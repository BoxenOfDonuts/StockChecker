import requests
from logger import logger
import os
import configparser
import time
from bs4 import BeautifulSoup

config = configparser.ConfigParser(interpolation=None)
configfile = os.path.join(os.path.dirname(__file__), 'config.ini')

if not os.path.exists(configfile):
    logger.info('os path doesn\'t work, trying local')
    if os.path.exists('config.ini'):
        print('something else')
        logger.info('found local config file')
        configfile = 'config.ini'
    else:
        logger.error('config file not found!')

config.read(configfile)


class GettingStuff(object):
    inStockMessage = 'GPU In Stock at {}!'
    oosMessage = 'Not in stock at {}'

    def getWebpage(self, type='text'):
        url = self.url
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
            "Cache-Control": "no-cache"
        }

        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            if type == 'json':
                self.request = r.json()
            else:
                self.request = r.text
        # return something that returns the whole thing to an error?
        except requests.exceptions.RequestException as e:
            logger.error('Something went wrong', extra={'error': e})
            self.request = "Error, Nothing Will Match"
        except requests.exceptions as e:
            logger.error('Something went wrong', extra={'error': e})
            self.request = "Error, Nothing Will Match"

    def checkStockText(self):
        inStockMessage = self.inStockMessage
        oosMessage = self.oosMessage

        if self.site == 'API':
            self.getWebpage(type='json')
        else:
            self.getWebpage()

        if self.site == 'BestBuy':
            if "/~assets/bby/_img/int/plsvgdef-frontend/svg/cart.svg#cart" in self.request:
                logger.info(inStockMessage.format(self.site))
                return True
            else:
                logger.info(oosMessage.format(self.site))
                return False
        elif self.site == 'Nvidia':
            soup = BeautifulSoup(self.request, 'html.parser')
            if "Add to Cart" in soup.find_all('div', class_=['cta-button', 'btn', 'show-out-of-stock'])[0]:
                logger.info(inStockMessage.format(self.site))
                return True
            else:
                logger.info(oosMessage.format(self.site))
                return False
        elif self.site == 'Newegg':
            pass
        else:
            logger.error('no site somehow!')

    def checkStockJSON(self):
        self.getWebpage()

        try:
            stockStatus = self.request['products']['product'][0]['inventoryStatus']['status']
            if stockStatus == 'PRODUCT_INVENTORY_IN_STOCK':
                logger.info('GPU in stock via nvidia API!')
                return True
            elif stockStatus != 'PRODUCT_INVENTORY_OUT_OF_STOCK':
                logger.info('GPU in stock via nvidia API!')
                return True
            else:
                logger.info('not in stock via nvidia API')
                return False
        except KeyError as e:
            logger.error('KeyError getting stock level', extra={'error': e})
            return False
        except TypeError as e:
            logger.error('Type Error, most likely bad response form api', extra={'error': e})
            return False


class GraphicsCard(GettingStuff):

    def __init__(self, url, site):
        self.url = url
        self.site = site
        self.flag = False
        self.request = None


FE_API = GraphicsCard('https://api-prod.nvidia.com/direct-sales-shop/DR/products/en_us/USD/5438481700', 'API')
FE_API.checkStockJSON()