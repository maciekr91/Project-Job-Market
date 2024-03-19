from bs4 import BeautifulSoup
from bs4.element import Tag
import pandas as pd
import re

from commons import get_driver


def extract_features_pracuj(offer: Tag, links: list):
    """
    This function processes a BeautifulSoup Tag representing a job offer and extracts
    various details. It also keeps track of processed links to avoid duplicates.

    Parameters:
    - offer (Tag): A BeautifulSoup Tag object representing the job offer.
    - links (list): A list of links that have already been processed.

    Returns:
    - tuple: A tuple containing the extracted offer details as a list and the updated list of links.
              Returns (None, links) if the offer's link is already in the links list.
    """
    whole_offer = offer.find('div', class_="c1fljezf")
    offer_details = whole_offer.find('div', class_="c1wygkax")
    keywords = whole_offer.find_all('div', class_='b1fdzgc4')

    link = offer_details.a['href']

    if link in links:
        return None, links

    links.append(link)

    experience = offer_details.find('li').text
    name = offer_details.h2.text
    company = offer_details.h4.text
    location = offer_details.h5.text
    work_mode = offer_details.find_all('li')[-1].text
    try:
        salary = offer_details.find('span', class_="s1jki39v").text.replace(u'\xa0', u'')
    except (IndexError, AttributeError):
        salary = 'Undisclosed Salary'
    techs = [keyword.text for keyword in keywords[0].find_all('span')] if keywords else []

    new_offer = [experience, name, company, location, work_mode, salary, techs, link]

    return new_offer, links


def parse_data_pracuj(driver, url_page: str, offers: list, links: list):
    """
    This function navigates to a specified URL using a Selenium WebDriver and parses the page's content
    using BeautifulSoup. It iterates over each job offer on the page, extracts relevant details using the
    'extract_features_pracuj' function, and accumulates them in a list.

    Parameters:
    - driver: The Selenium WebDriver used for web navigation and content extraction.
    - url_page (str): The URL of the webpage to scrape job offers from.
    - offers (list): A list used to accumulate extracted job offers.
    - links (list): A list of links that have already been processed to avoid duplicate processing.

    Returns:
    - tuple: A tuple containing the list of accumulated job offers and the updated list of processed links.
    """
    driver.get(url_page)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for offer in soup.find_all('div', class_="be8lukl core_po9665q"):

        new_offer, links = extract_features_pracuj(offer, links)
        if new_offer:
            offers.append(new_offer)

    return offers, links


def scrape_pracuj(url: str):
    """
    This function initializes a Selenium WebDriver to navigate the provided URL.
    It determies the total number of pages and iterating through each one.
    For each page, it extracts job offers' details using the 'parse_data_pracuj' function.
    It accumulates all the offers and their respective links to avoid duplicates.

    Note: The function contains commented code for closing pop-ups which can be enabled if necessary.

    Parameters:
    - url (str): The base URL of the job listings on the Pracuj.pl website.

    Returns:
    - tuple: A tuple containing a list of job offers and a list of processed links.
    """
    driver = get_driver()
    driver.get(url)

    # close_popup(driver, "div.popup_p1c6glb0")
    # close_popup(driver, "button[data-test='button-submitCookie']")

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


def clear_salary_pracuj(row: str):
    """
    This function takes a string describing the salary from a job offer and extracts the numerical
    salary range and the salary period. It handles cases with undisclosed salaries, single-value
    salaries, and converts hourly wages to monthly wages assuming a standard 160-hour work month.
    It calculates and returns the lower and upper bounds of the salary range and the average salary.

    Parameters:
    - row (str): A string containing the salary information from a job offer.

    Returns:
    - pd.Series: A pandas Series containing three elements: the lower bound of the salary range,
                 the upper bound of the salary range, and the average of these two values. If the
                 salary is undisclosed, all three elements are None.
    """
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


def clear_location_pracuj(row: str):
    """
    This function extracts the primary location from a string that may contain multiple location details.
    The logic is adapted to the specificity of the website
    """
    if ':' in row:
        row = row.split(':')[-1]

    return row.split(',')[0]


def clear_mode_pracuj(row: str):
    """
    Pracuj.pl often contains more than one working mode (i.e. Hybrid and Remote). This function
    searches for most 'flexible' mode and assigns it to offer
    """
    if 'Praca zdalna' in row:
        return 'Praca zdalna'
    elif 'Praca hybrydowa' in row:
        return 'Praca hybrydowa'
    else:
        return 'Praca stacjonarna'


def clear_data_pracuj(offers_list: list):
    """
    This function takes a list of job offers, each as a list of attributes, and converts it into
    a structured pandas DataFrame. It standardizes the experience level using a predefined mapping,
    cleans and splits salary information into structured format using 'clear_salary_pracuj',
    extracts and standardizes the location and work mode. It also adds a source site identifier.

    Parameters:
    - offers_list (list): A list of job offers, where each offer is a list of attributes.

    Returns:
    - DataFrame: A pandas DataFrame with standardized and structured job offer data
    """
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


def separate_and_map(list_to_edit):
    """
    One of the goals of the project is to unify searching regardless the website. Although every
    website has its own specifity we decided to unify the names of categories to those on justjoin.it.
    As pracuj has two different ways to filter offer: technology and specialization we map name of categories
    from jjit to most appropriate searching criteria in pracuj.pl - sometimes it's through technology and
    sometimes through specialization. We don't mix those two beacuse it narrows down the search area
    which is undesirable. That's why we need to perform search through technology and specialization
    if both are needed.

    Parameters:
    - list_to_edit (list): A list of keywords representing technologies and specializations.

    Returns:
    - tuple: A tuple containing two elements. The first element is a URL parameter string for technologies,
             and the second is a URL parameter string for specializations. Each is None if the respective
             category is not present in the input list.
    """
    tech_dict = {
        'javascript': '33',
        'html': '34',
        'php': '40',
        'ruby': '86%2C49',
        'python': '37',
        'java': '38',
        'net': '75',
        'scala': '45',
        'c': '39%2C41%2C54',
        'mobile': 'mobile',
        'testing': 'testing',
        'devops': 'devops',
        'admin': 'it-admin',
        'ux': 'ux-ui',
        'pm': 'product-management%2Cproject-management',
        'game': 'gamedev',
        'analytics': 'business-analytics%2Csystem-analytics',
        'security': 'security',
        'data': 'big-data-science%2Cai-ml',
        'go': '50',
        'support': 'helpdesk',
        'erp': 'sap-erp',
        'architecture': 'architecture',
        'other': 'agile'
    }

    all_technologies = ['javascript', 'html', 'php', 'ruby', 'python', 'java', 'net', 'scala', 'c', 'go']
    all_specializations = ['mobile', 'testing', 'devops', 'admin', 'ux', 'pm', 'game', 'analytics',
                           'security', 'data', 'support', 'erp', 'architecture', 'other']

    technologies = [tech_dict[element] for element in list_to_edit if element in all_technologies]
    if technologies:
        tech_url = 'itth=' + '%2C'.join(technologies)
    else:
        tech_url = None

    specializations = [tech_dict[element] for element in list_to_edit if element in all_specializations]
    if specializations:
        spec_url = 'its=' + '%2C'.join(specializations)
    else:
        spec_url = None

    return tech_url, spec_url


def search_pracuj(categories_list: list):
    """
    This function compiles the whole process from preparing URLS, through scraping, cleaning data
    and returning structured DataFrame of offers from pracuj.pl

    Parameters:
    - categories_list (list): A list of category keywords to search for.

    Returns:
    - DataFrame: A pandas DataFrame containing structured data of the aggregated job offers from Pracuj.pl.
    """
    base_url = 'https://it.pracuj.pl/praca?'
    urls = [base_url + url for url in separate_and_map(categories_list) if url is not None]

    new_offers = []

    for url in urls:
        offers, _ = scrape_pracuj(url)
        new_offers += offers

    offers_df = clear_data_pracuj(new_offers)

    return offers_df


# EXTRA FEATURES - FOR LATER USE

# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.action_chains import ActionChains

# def extract_multiple_locations(whole_offer, simple_location):
#     locations = whole_offer.find_all('div', class_="tiles_lov4ye4")
#     multi_locations = []
#
#     for loc in locations:
#         single_location = loc.a.text
#         multi_locations.append(single_location)
#
#     link = locations[0].a['href']
#     location = multi_locations
#
#     return location, link
#
#
# def extract_features_pracuj(offer: Tag, links: list):
#     whole_offer = offer.find('div', class_="c1fljezf")
#     offer_details = whole_offer.find('div', class_="c1wygkax")
#     keywords = whole_offer.find_all('div', class_='b1fdzgc4')
#
#     simple_location = offer_details.h5.text
#
#     if 'lokalizacj' in simple_location:
#         try:
#             location, link = extract_multiple_locations
#         except Exception as n:
#             link = offer_details.a['href']
#             location = [simple_location]
#             print(f"Couldn't extract multiple locations because: {n}")
#
#     else:
#         link = offer_details.a['href']
#         location = [simple_location]
#
#     if link in links:
#         return None, links
#
#     links.append(link)
#
#     experience = offer_details.find('li').text
#     name = offer_details.h2.text
#     company = offer_details.h4.text
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
#
#
# def open_multiple_locations(driver):
#     css1 = "h5.tiles_r1rl4c7t.size-caption.core_t1rst47b[data-test='text-region']"
#     css2 = "h5.tiles_ttlhhld.size-caption.core_t1rst47b[data-test='text-region']"
#     elements1 = driver.find_elements(By.CSS_SELECTOR, css1)
#     elements2 = driver.find_elements(By.CSS_SELECTOR, css2)
#     elements = elements1 + elements2
#
#     actions = ActionChains(driver)
#
#     for element in elements:
#         try:
#             location = element.text
#             if location and 'lokalizac' in location:
#                 print(f"Próbuję kliknąć w element z lokalizacją: {location}")  # debug
#                 actions.move_to_element(element).click().perform()
#         except Exception as e:
#             print(f"Couldn't click {location}, because: \n", e)
