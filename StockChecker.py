import requests
from logger import logger
import os
import configparser
import time
from bs4 import BeautifulSoup

BBURL = 'https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440'
NVIDIAURL = 'https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3080'
NVIDIAAPIURL = 'https://api-prod.nvidia.com/direct-sales-shop/DR/products/en_us/USD/5438481700'
EVGAURL = 'https://www.evga.com/products/product.aspx?pn=10G-P5-3881-KR'

#"https://in-and-ru-store-api.uk-e1.cloudhub.io/DR/products/en_us/USD/5438481700"

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


class StockChecker(object):
    def __init__(self):
        self.nflag = False
        self.bflag = False
        self.napiflag = False
        self.eflag = False

    def getWebpage(self, url, type='text'):
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
            if type=='json':
                return r.json()
            else:
                return r.text
        except requests.exceptions.RequestException as e:
            logger.error('Something went wrong', extra={'error': e})
            return "Error, Nothing Will Match"
        except requests.exceptions as e:
            logger.error('Something went wrong', extra={'error': e})
            return "Error, Nothing Will Match"

    def check_stock(self):
        #url = 'https://www.bestbuy.com/site/apple-homepod-space-gray/5902410.p?skuId=5902410'

        bbCards = {
            'evga': 'https://www.bestbuy.com/site/evga-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card/6432399.p?skuId=6432399',
            'FE': 'https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440'
        }

        pageText = self.getWebpage(BBURL)

        if "/~assets/bby/_img/int/plsvgdef-frontend/svg/cart.svg#cart" in pageText:
            logger.info('GPU in stock!')
            return True
        else:
            logger.info('not in stock')
            return False


    def check_evga(self):
        #url = 'https://www.bestbuy.com/site/apple-homepod-space-gray/5902410.p?skuId=5902410'


        evgaurl = 'https://www.bestbuy.com/site/evga-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card/6432399.p?skuId=6432399'

        pageText = self.getWebpage(evgaurl)

        if "/~assets/bby/_img/int/plsvgdef-frontend/svg/cart.svg#cart" in pageText:
            logger.info('GPU in stock!')
            return True
        else:
            logger.info('evga not in stock')
            return False


    def stock_check_nvidia(self):
        # url = 'https://www.bestbuy.com/site/apple-homepod-space-gray/5902410.p?skuId=5902410'
        #url = 'https://www.nvidia.com/en-us/geforce/graphics-cards/rtx-2060-super/'

        pageText = self.getWebpage(NVIDIAURL)
        soup = BeautifulSoup(pageText, 'html.parser')

        #soup.find_all(attrs={'data-theme-override': "null"})[0]['class'] = ['cta-button', 'btn', 'show-out-of-stock']


        #if soup.find_all(attrs={'data-title': 'add-to-cart'}):
        #if not soup.find_all('span', class_='oos-btn'):
        #if not soup.find_all('div', class_=['cta-button', 'btn', 'show-out-of-stock']):
        if "Add to Cart" in soup.find_all('div', class_=['cta-button', 'btn', 'show-out-of-stock'])[0]:
            logger.info('GPU in stock at nvidia!')
            return True
        else:
            logger.info('not in stock at nvidia')
            return False

    def stock_check_nvidia_api(self):

        pageJSON = self.getWebpage(NVIDIAAPIURL, type='json')

        try:
            stockStatus = pageJSON['products']['product'][0]['inventoryStatus']['status']

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


def isgpuInStockSomewhere(check, flag, url):
    if check:
        if not flag:
            message = 'HOLLY SHIT ITS IN STOCK GO NOW!!!!!!!!!\n' \
                      '{}'.format(url)
            response = telegram_send(message)

            if response:
                logger.info("Message Sent")
                flag = True
                logger.info('{} set to true'.format(flag))
            else:
                logger.error("Message Not Sent")
        else:
            if flag:
                logger.info('back out of stock, updating {}'.format(flag))
                flag = False


def main():
    logger.info("Starting!")
    st = StockChecker()
    while True:
        if st.check_stock():
            if not st.bflag:
                message = 'HOLLY SHIT ITS IN STOCK GO NOW!!!!!!!!!\n' \
                          'https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440'
                response = telegram_send(message)

                if response:
                    logger.info("Message Sent")
                    st.bflag = True
                    logger.info('blfag set to true')
                else:
                    logger.error("Message Not Sent")
        else:
            if st.bflag:
                logger.info('back out of stock, updating bflag')
                st.bflag = False
            #time.sleep(30)

        if st.stock_check_nvidia():
            if not st.nflag:
                message = 'HOLLY SHIT ITS IN STOCK GO NOW!!!!!!!!!\n' \
                          'https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3080'
                response = telegram_send(message)

                if response:
                    logger.info("Message Sent")
                    st.nflag = True
                    logger.info('nlfag set to true')
                else:
                    logger.error("Message Not Sent")
        else:
            if st.nflag:
                logger.info('back out of stock, updating nflag')
                st.nflag = False
            #time.sleep(30)

        if st.stock_check_nvidia_api():
            if not st.napiflag:
                message = 'HOLLY SHIT ITS IN STOCK GO NOW!!!!!!!!!\n' \
                          'https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3080'
                response = telegram_send(message)

                if response:
                    logger.info("Message Sent")
                    st.napiflag = True
                    logger.info('nlfag set to true')
                else:
                    logger.error("Message Not Sent")
        else:
            if st.napiflag:
                logger.info('back out of stock, updating napiflag')
                st.napiflag = False

        if st.check_evga():
            if not st.eflag:
                message = 'HOLLY SHIT ITS IN STOCK GO NOW!!!!!!!!!\n' \
                          'https://www.bestbuy.com/site/evga-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card/6432399.p?skuId=6432399'
                response = telegram_send(message)

                if response:
                    logger.info("Message Sent")
                    st.eflag = True
                    logger.info('blfag set to true')
                else:
                    logger.error("Message Not Sent")
        else:
            if st.eflag:
                logger.info('back out of stock, updating bflag')
                st.eflag = False

        time.sleep(30)


if __name__ == '__main__':
    main()