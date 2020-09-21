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


class StockChecker(object):
    def __init__(self):
        self.nflag = False
        self.bflag = False

    @staticmethod
    def check_stock():
        #url = 'https://www.bestbuy.com/site/apple-homepod-space-gray/5902410.p?skuId=5902410'
        url = 'https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440'

        headers = {
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "accept-encoding": "gzip, deflate, br",
                    "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
                    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36"
        }
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error('Something went wrong', extra={'error': e})

        if "/~assets/bby/_img/int/plsvgdef-frontend/svg/cart.svg#cart" in r.text:
            logger.info('GPU in stock!')
            return True
        else:
            logger.info('not in stock')
            return False


    @staticmethod
    def stock_check_nvidia():
        # url = 'https://www.bestbuy.com/site/apple-homepod-space-gray/5902410.p?skuId=5902410'
        url = 'https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3080'
        #url = 'https://www.nvidia.com/en-us/geforce/graphics-cards/rtx-2060-super/'

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36"
        }
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error('Something went wrong', extra={'error': e})

        #if soup.find_all(attrs={'data-title': 'add-to-cart'}):
        if not soup.find_all('span', class_='oos-btn'):
            logger.info('GPU in stock at nvidia!')
            return True
        else:
            logger.info('not in stock at nvidia')
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
        response = r.json()['ok']

    return response


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
        time.sleep(30)


if __name__ == '__main__':
    main()