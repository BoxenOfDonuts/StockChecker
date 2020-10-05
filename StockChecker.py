import requests
from logger import logger
import os
import configparser
import time
from bs4 import BeautifulSoup
import json

config = configparser.ConfigParser(interpolation=None)
configfile = os.path.join(os.path.dirname(__file__), 'config.ini')
jsonfile = os.path.join(os.path.dirname(__file__), 'sites.json')

if not os.path.exists(configfile):
    logger.info('os path doesn\'t work, trying local')
    if os.path.exists('config.ini'):
        print('something else')
        logger.info('found local config file')
        configfile = 'config.ini'
    else:
        logger.error('config file not found!')
else:
    config.read(configfile)

if not os.path.exists(jsonfile):
    logger.error('no sites.json file.. exiting..')
else:
    with open(jsonfile, 'r') as f:
        sites = json.load(f)

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

        if self.site == 'Nvidia':
            soup = BeautifulSoup(self.request, 'html.parser')
            if "Add to Cart" in soup.find_all('div', class_=['cta-button', 'btn', 'show-out-of-stock'])[0]:
                logger.info(inStockMessage.format(self.site))
                return True
            else:
                logger.info(oosMessage.format(self.site))
                return False
        # make it generic? idk
        if self.site == 'Bestbuy' or self.site == 'Newegg':
            #if "/~assets/bby/_img/int/plsvgdef-frontend/svg/cart.svg#cart" in self.request:
            if self.matchTerm in self.request:
                logger.info(inStockMessage.format(self.site))
                return True
            else:
                logger.info(oosMessage.format(self.site))
                return False

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

    def __init__(self, url, site, name, matchTerm=None):
        self.url = url
        self.site = site
        self.matchTerm = matchTerm
        self.name = name
        self.flag = False
        self.request = None


def telegram_send(message):
    bot_token = config['telegram']['token']
    bot_chatID = config['telegram']['chatID']

    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + message
    try:
        r = requests.get(send_text)
        r.raise_for_status()
        response = r.json()['ok']
        logger.info("GET to telegram", extra={"Response": response, 'URL': r.url})
    except requests.exceptions.RequestException as e:
        logger.error("something went wrong", extra={"error": e})
        response = r.json()['ok'] # think this makes it false? Idk lol

    return response


def main():
    gpuList = []
    logger.info('Starting!')
    for site in sites:
        if site['enabled']:
            gpuList.append(GraphicsCard(site['url'], site['site'], site['name'], site['match term']))
        else:
            pass
    while True:
        for gpu in gpuList:
            if gpu.site == 'API':
                stockStatus = gpu.checkStockJSON()
            else:
                stockStatus = gpu.checkStockText()

            # if not in stock and was previously in stock
            if not stockStatus and gpu.flag:
                gpu.flag = False
                logger.info('Flag set to false')
            # if in stock and wasn't previously in stock
            elif stockStatus and not gpu.flag:
                message = 'HOLLY SHIT {} IN STOCK GO NOW!!!!!!!!!\n' \
                          '{}'.format(gpu.name, gpu.url)
                response = telegram_send(message)
                if response:
                    logger.info('Message Sent!')
                    gpu.flag = True
                    logger.info('Flat set to true')
                else:
                    logger.error('Message not Sent')
            # else is not in stock and wasn't
            # or is stock and still is
        time.sleep(30)


if __name__ == '__main__':
    main()