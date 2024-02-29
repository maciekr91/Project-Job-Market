from bs4 import BeautifulSoup
from bs4.element import Tag
import pandas as pd
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from commons import get_driver, close_popup

# TODO zmienić w extract tak, żeby parsowało dla otwartych multiple loc


# def extract_features_pracuj(offer: Tag, links: list):
#     whole_offer = offer.find('div', class_="c1fljezf")
#     offer_details = whole_offer.find('div', class_="c1wygkax")
#     keywords = whole_offer.find_all('div', class_='b1fdzgc4')
#
#     link = offer_details.a['href']
#
#     if link in links:
#         return None, links
#
#     links.append(link)
#
#     experience = offer_details.find('li').text
#     name = offer_details.h2.text
#     company = offer_details.h4.text
#     location = offer_details.h5.text
#     work_mode = offer_details.find_all('li')[-1].text
#     try:
#         salary = offer_details.find('span', class_="s1jki39v").text.replace(u'\xa0', u'')
#     except (IndexError, AttributeError):
#         salary = 'Undisclosed Salary'
#     techs = [keyword.text for keyword in keywords[0].find_all('span')] if keywords else []
#
#     new_offer = [experience, name, company, location, work_mode, salary, techs, link]
#
#     return new_offer, links


def extract_features_pracuj(offer: Tag, links: list):
    whole_offer = offer.find('div', class_="c1fljezf")
    offer_details = whole_offer.find('div', class_="c1wygkax")
    keywords = whole_offer.find_all('div', class_='b1fdzgc4')

    simple_location = offer_details.h5.text

    if 'lokalizacj' in simple_location:
        locations = whole_offer.find_all('div', class_="tiles_lov4ye4")
        multi_locations = []

        for loc in locations:
            single_location = loc.a.text
            multi_locations.append(single_location)

        link = locations[0].a['href']
        location = multi_locations

    else:
        link = offer_details.a['href']
        location = [simple_location]

    if link in links:
        return None, links

    links.append(link)

    experience = offer_details.find('li').text
    name = offer_details.h2.text
    company = offer_details.h4.text
    work_mode = offer_details.find_all('li')[-1].text
    try:
        salary = offer_details.find('span', class_="s1jki39v").text.replace(u'\xa0', u'')
    except (IndexError, AttributeError):
        salary = 'Undisclosed Salary'
    techs = [keyword.text for keyword in keywords[0].find_all('span')] if keywords else []

    new_offer = [experience, name, company, location, work_mode, salary, techs, link]

    return new_offer, links


def open_multiple_locations(driver):
    css1 = "h5.tiles_r1rl4c7t.size-caption.core_t1rst47b[data-test='text-region']"
    css2 = "h5.tiles_ttlhhld.size-caption.core_t1rst47b[data-test='text-region']"
    elements1 = driver.find_elements(By.CSS_SELECTOR, css1)
    elements2 = driver.find_elements(By.CSS_SELECTOR, css2)
    elements = elements1 + elements2

    actions = ActionChains(driver)

    for element in elements:
        try:
            location = element.text
            if location and 'lokalizac' in location:
                actions.move_to_element(element).click().perform()
        except Exception as e:
            print(f"Couldn't click {location}, because: \n", e)


def parse_data_pracuj(driver, url_page: str, offers: list, links: list):
    driver.get(url_page)

    open_multiple_locations(driver)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for offer in soup.find_all('div', class_="be8lukl core_po9665q"):

        new_offer, links = extract_features_pracuj(offer, links)
        if new_offer:
            offers.append(new_offer)

    return offers, links


def scrape_pracuj(url: str):
    driver = get_driver()
    driver.get(url)

    close_popup(driver, "div.popup_p1c6glb0")
    close_popup(driver, "button[data-test='button-submitCookie']")

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    try:
        no_pages = int(soup.find_all('div', class_="listing_w13k878q")[0].p.find_all('span')[1].text)
    except (IndexError, AttributeError):
        no_pages = 1

    offers = []
    links = []

    for page in range(1, no_pages + 1):
        url_page = url + '&pn=' + str(page)
        offers, links = parse_data_pracuj(driver, url_page, offers, links)

    driver.quit()

    return offers, links


def clear_salary_pracuj(row):
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


def clear_location_pracuj(row: list):
    if len(row) == 1:
        row = row[0]
        if ':' in row:
            row = row.split(':')[-1]
        row = row.split(',')[0]

    return row


def clear_mode_pracuj(row):
    if 'Praca zdalna' in row:
        return 'Praca zdalna'
    elif 'Praca hybrydowa' in row:
        return 'Praca hybrydowa'
    else:
        return 'Praca stacjonarna'


def clear_data_pracuj(offers_list: list):
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
    offers_df[['salary_low', 'salary_high', 'salary_avg']] = offers_df['salary'].apply(clear_salary_pracuj)
    offers_df['location'] = offers_df['location'].apply(clear_location_pracuj)
    offers_df['work_mode'] = offers_df['work_mode'].apply(clear_mode_pracuj)
    offers_df['site'] = "pracuj.pl"
    offers_df = offers_df[['site', 'experience', 'name', 'company', 'location', 'work_mode',
                           'salary_avg', 'salary_low', 'salary_high', 'technologies', 'link']]

    return offers_df


def search_pracuj(url: str):
    offers, _ = scrape_pracuj(url)
    offers_df = clear_data_pracuj(offers)

    return offers_df
