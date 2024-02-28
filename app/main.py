from jjit import search_jjit
from pracuj import search_pracuj
from commons import merge_offers


# TODO stworzyć funkcje i słowniki do wyboru kryteriów wyszukiwania

if __name__ == '__main__':
    jjit_categories = ['python', 'data', 'analytics']
    jjit_experience = ['junior', 'mid', 'senior', 'c-level']
    # jjit_categories = ['python']
    # jjit_experience = ['junior']
    base_url = 'https://it.pracuj.pl/praca?'
    technologies = 'itth=37%2C36'
    specialization = 'its=big-data-science%2Cbusiness-analytics%2Cai-ml'
    # technologies = 'itth=37'
    # specialization = 'its=big-data-science'
    pracuj_url = base_url + specialization + '&' + technologies

    offers_jjit = search_jjit(jjit_categories, jjit_experience)
    offers_pracuj = search_pracuj(pracuj_url)
    merge_offers(offers_jjit, offers_pracuj)
