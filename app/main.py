from jjit import search_jjit
from pracuj import search_pracuj
from common import merge_offers


if __name__ == '__main__':
    jjit_categories = ['python', 'data', 'analytics']
    jjit_experience = ['junior', 'mid', 'senior', 'c-level']
    base_url = 'https://it.pracuj.pl/praca?'
    technologies = 'itth=37%2C36'
    specialization = 'its=big-data-science%2Cbusiness-analytics%2Cai-ml'
    pracuj_url = base_url + specialization + '&' + technologies

    offers_jjit = search_jjit(jjit_categories, jjit_experience)
    offers_pracuj = search_pracuj(pracuj_url)
    merge_offers(offers_jjit, offers_pracuj)
