from bs4 import BeautifulSoup
import requests

# crawl https://www.npa.gov.tw/ch/app/openData/artwebsite/data?module=artwebsite&serno=d08673f4-0775-4a09-b4d8-d47c2c4edca2&type=json to get the data
# https://www.npa.gov.tw/ch/app/openData/artwebsite/data?module=artwebsite&serno=d08673f4-0775-4a09-b4d8-d47c2c4edca2&type=json


def get_numbers():
    url = 'https://www.npa.gov.tw/ch/app/openData/artwebsite/data?module=artwebsite&serno=d08673f4-0775-4a09-b4d8-d47c2c4edca2&type=json'
    res = requests.get(url)
    html = res.json()['detailContent']
    soup = BeautifulSoup(html, 'html.parser')
    units = [tag.text for tag in soup.find_all('td', attrs={'data-th': '單位'})]
    numbers = [tag.text.replace('-', '') for tag in soup.find_all(
        'td', attrs={'data-th': '手機簡訊報案號碼'})]
    numbers = list(zip(units, numbers))
    return numbers
