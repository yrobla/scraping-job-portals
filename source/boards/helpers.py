import string
import re
from time import sleep
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from selenium import webdriver


def download_url(url):
    '''Downloads the given url and adds a delay according to time tracked'''
    try:
        driver = webdriver.Chrome()
        driver.get(url)

        navigationStart = driver.execute_script("return window.performance.timing.navigationStart")
        domComplete = driver.execute_script("return window.performance.timing.domComplete")

        timing = (domComplete - navigationStart)/1000
        if timing < 0:
            timing=1

        # we detect the time that takes to load the page.
        # Then we sleep a proportional number of seconds
        # to don't overload the server
        sleep(timing*5)

        return driver
    except Exception as e:
        print(str(e))

    return None

def parse_number(number, currency="€", units_separator=".", decimal_separator=","):
    '''Converts a formatted number to float one'''
    # strip currency symbol
    number = number.replace(currency, "")
    # strip dots
    number = number.replace(units_separator, "")
    # split by decimal
    number_items = number.split(decimal_separator)
    if len(number_items)==2:
        final_number = int(number_items[0]) + float(int(number_items[1])/len(number_items[1]))
    else:
        final_number = int(number_items[0])
    return final_number

def cleanup_text(text):
    '''Strips html and normalizes text using language processing'''
    final_text = BeautifulSoup(text, "lxml").text
    # convirtiendo en palabras
    tokens = word_tokenize(final_text)
    # convertir a minúsculas
    tokens = [w.lower() for w in tokens]
    # prepare a regex para el filtrado de caracteres
    re_punc = re.compile('[%s]' % re.escape(string.punctuation))
    # eliminar la puntuación de cada palabra
    stripped = [re_punc.sub(' ', w) for w in tokens]
    # eliminar los tokens restantes que no estén en orden alfabético
    words = [word for word in stripped if word.isalpha()]
    # filtrar las palabras de interrupción
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if not w in stop_words]
    stop_words = set(stopwords.words('spanish'))
    words = [w for w in words if not w in stop_words]
    return " ".join(words[:255])
