from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

import pandas as pd
import re
import os


def pracuj_switch(url):

    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(current_dir, 'chromedriver.exe')
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    try:
        no_pages = int(soup.find_all('div', class_="listing_w13k878q")[0].p.find_all('span')[1].text)
    except:
        no_pages = 1

    offers = []
    links = []

    for page in range(1, no_pages + 1):
        url_page = url + '&pn=' + str(page)

        offers, links = scrap_data_pracuj(driver, url_page, offers, links)

    driver.quit()

    return offers, links

def scrap_data_pracuj(driver, url_page, offers, links):

    driver.get(url_page)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for offer in soup.find_all('div', class_ = "be8lukl core_po9665q"):

        whole_offer = offer.find_all('div', class_ = "c1fljezf")[0]
        offer_details = whole_offer.find_all('div', class_ = "c1wygkax")[0]
        keywords = whole_offer.find_all('div', class_ = 'b1fdzgc4')

        link = offer_details.a['href']

        if link in links:
            continue

        links.append(link)

        experience = offer_details.find_all('li')[0].text
        name = offer_details.a.text
        company = offer_details.h4.text
        location = offer_details.h5.text
        work_mode = offer_details.find_all('li')[-1].text
        try:
            salary = offer_details.find_all('span', class_ = "s1jki39v")[0].text.replace(u'\xa0', u'')
        except:
            salary = 'Undisclosed Salary'

        techs = [keyword.text for keyword in keywords[0].find_all('span')] if keywords else []

        new_offer = [experience, name, company, location, work_mode, salary, techs, link]

        offers.append(new_offer)

    return offers, links


def clear_salary(row):
    if 'Undisclosed Salary' in row:
        return pd.Series([None, None, None])

    salary_range = [int(x) for x in re.findall(r'\d+', row.split('/')[0])]
    salary_period = row.split('/')[1].strip().split(" ")[0]

    if len(salary_range) == 1:
        salary_range = salary_range * 2

    if salary_period == 'godz.':
        salary_range = [salary_range[0] * 160, salary_range[1] * 160]

    salary_avg = (salary_range[0] + salary_range[1]) / 2

    return pd.Series([salary_range[0], salary_range[1], salary_avg])


def clear_location(row):
    if ':' in row:
        row = row.split(':')[-1]

    return row.split(',')[0]

def clear_mode(row):
    if 'Praca zdalna' in row:
        return 'Praca zdalna'
    elif 'Praca hybrydowa' in row:
        return 'Praca hybrydowa'
    else:
        return 'Praca stacjonarna'


def clear_data_pracuj(offers_list):
    exp_dict = {
        "Praktykant / Stażysta": "junior",
        "Asystent": "junior",
        "Młodszy specjalista (Junior)": "junior",
        "Specjalista (Mid / Regular)": "mid",
        "Starszy specjalista (Senior)": "senior",
        "Ekspert": "senior",
        "Kierownik / Koordynator": "c-level",
        "Menedżer": "c-level",
        "Dyrektor": "c-level",
        "Prezes": "c-level",
    }

    columns = ['experience', 'name', 'company', 'location', 'work_mode', 'salary', 'technologies', 'link']
    offers_df = pd.DataFrame(data=offers_list, columns=columns)

    offers_df['experience'] = offers_df['experience'].apply(lambda x: x.split(',')[0]).map(exp_dict)

    offers_df[['salary_low', 'salary_high', 'salary_avg']] = offers_df['salary'].apply(clear_salary)

    offers_df['location'] = offers_df['location'].apply(clear_location)

    offers_df['work_mode'] = offers_df['work_mode'].apply(clear_mode)

    offers_df['site'] = "pracuj.pl"

    offers_df = offers_df[['site', 'experience', 'name', 'company', 'location', 'work_mode',
                           'salary_avg', 'salary_low', 'salary_high', 'technologies', 'link']]

    return offers_df

def search_pracuj(url):
    offers, links = pracuj_switch(url)
    offers_df = clear_data_pracuj(offers)

    return offers_df