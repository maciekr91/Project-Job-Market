from summary import search_offers


if __name__ == '__main__':

    jjit_categories = ['python', 'data', 'analytics']
    jjit_experience = ['junior', 'mid', 'senior', 'c-level']

    base_url = 'https://it.pracuj.pl/praca?'
    technologies = 'itth=37%2C36'
    specialization = 'its=big-data-science%2Cbusiness-analytics%2Cai-ml'
    pracuj_url = base_url + specialization + '&' + technologies

    search_offers(pracuj_url, jjit_categories, jjit_experience)
