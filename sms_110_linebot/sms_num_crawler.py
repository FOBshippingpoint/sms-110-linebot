from bs4 import BeautifulSoup
import requests
import re


def crawl_mobiles():
    url = 'https://www.npa.gov.tw/ch/app/artwebsite/view?module=artwebsite&id=1048&serno=e3ad2889-4dee-41cf-aef8-9b9d26dc6950'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    police_departments = [tag.text for tag in soup.find_all(
        'td', attrs={'data-th': '單位'})]
    numbers = [re.sub('\(|\)|-|\s', '', tag.text) for tag in soup.find_all(
        'td', attrs={'data-th': '電話'})]
    numbers = list(zip(police_departments, numbers))
    return numbers
