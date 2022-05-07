from bs4 import BeautifulSoup
import requests


def crawl_mobiles():
    url = 'https://www.npa.gov.tw/ch/app/openData/artwebsite/data?module=artwebsite&serno=d08673f4-0775-4a09-b4d8-d47c2c4edca2&type=json'
    res = requests.get(url)
    html = res.json()['detailContent']
    soup = BeautifulSoup(html, 'html.parser')
    police_departments = [tag.text for tag in soup.find_all(
        'td', attrs={'data-th': '單位'})]
    numbers = [tag.text.replace('-', '') for tag in soup.find_all(
        'td', attrs={'data-th': '手機簡訊報案號碼'})]
    numbers = list(zip(police_departments, numbers))
    return numbers
