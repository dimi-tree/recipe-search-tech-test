from datetime import timedelta
from time import time
from pathlib import Path
import re
from collections import defaultdict
import pickle
import unicodedata

DESKTOP = Path('/Users/dimitri/Desktop')
# BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path('.')
PATH_TO_DATABASE = BASE_DIR / '_database.pickle'
ASCII_WORD = re.compile(r'[a-z]+')

# https://gist.github.com/sebleier/554280
STOPWORDS =  {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'}


def unicode_to_ascii(text):
    """Converts Unicode chars to ASCII, e.g. ç --> c."""
    # TODO: investigate further. Is there a better way?
    # TODO: perhaps we want to keep both the unicode and the normalized string?
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('unicode-escape')


def read_file(path):
    """Returns a list words, all lower-case, found in the first line of the text file."""
    with open(path, 'r') as f:
        text = f.readline().lower()
    
    text = unicode_to_ascii(text)
    return ASCII_WORD.findall(text)


def add_file_to_db(file_path, db):
    document_id = file_path.stem
    document = read_file(file_path)

    for word in document:
        if word not in STOPWORDS:
            db[word].add(document_id)


def persist_database_on_disk(db):
    # NOTE: if the DB already exists, it will be overwritten
    with open(PATH_TO_DATABASE, 'wb') as f:
        pickle.dump(db, f)


def create_database(path_to_recipes_dir):
    path_to_recipes_dir = Path(path_to_recipes_dir).expanduser().resolve()

    db = defaultdict(set)
    for file_path in path_to_recipes_dir.glob('*.txt'):
        add_file_to_db(file_path, db)

    persist_database_on_disk(db)


def update_database(path_to_recipe):
    # TODO: check if it's a txt file
    file_path = Path(path_to_recipe).expanduser().resolve()

    db = load_database()
    add_file_to_db(file_path, db)
    persist_database_on_disk(db)


def load_database():
    with open(PATH_TO_DATABASE, 'rb') as f:
        return pickle.load(f)


def perform_search(query, db):
    query_terms = ASCII_WORD.findall(unicode_to_ascii(query))

    found = {}
    for term in query_terms:
        found[term] = db.get(term, set())
    
    results = list(set.intersection(*found.values()))
    
    if not results:
        results = list(set.union(*found.values()))
    
    # TODO: perhaps have a combination of intersection and union when not enough results
    
    return results


def main():
    """
    Spec:
    - create an index
    - have an option to add a new document, i.e. update index
    - perform 1 word search
    - log the search query
    """
    # filename = 'sweet-potato-carrot-ginger-soup.txt'
    # text = read_a_file(DESKTOP / 'recipes' / filename)
    # # print(PAT.findall(text))
    # print(text)
    # print(PAT.split(text))
    # print(ASCII_WORD.findall(text))

    # print('Search complete!')
    # db = defaultdict(set)
    # for file_path in (DESKTOP / 'recipes').glob('*.txt'):
    #     document_id = file_path.stem
    #     document = read_file(file_path)
    #     print(type(document))

    #     for word in document:
    #         if word not in STOPWORDS:
    #             db[word].add(document_id)

    #     print(document_id, document, end='\n'*2)
    
    # print(db)

    # create_index('../../Desktop/recipes')
    # update_database(Path('~/Downloads/recipes/tomato-nicoise-salad.txt').expanduser())
    # db = load_index()
    # print(db)
    # print(len(db))
    # print(read_file(Path('~/Downloads/recipes/tomato-nicoise-salad.txt').expanduser()))

    # print(db.keys())
    # query = 'tomatillo juice'
    # terms = query.lower().split(' ')
    # results = set()
    # found = {}
    # for term in query.split(' '):
    #     found[term] = db.get(term, set())
    
    # print(found)
    
    # # results = list(set.intersection(*found.values()))
    # results = None
    # if not results:
    #     results = list(set.union(*found.values()))
    
    # print(results)


    # db = load_database()
    # # query = 'tomatillo juice'
    # # ['tomatillo-carrot-apple-ginger-juice', 'tomatillo-apple-cucumber-juice']

    # # query = 'tomato'
    # # ['tomatillo-mango-coriander-sauce', 'tomato-nicoise-salad']

    # query = 'niçoise    '
    # # ['tomato-nicoise-salad']
    # results = perform_search(query, db)
    # print(results)


    # create_database('~/Downloads/recipes')

    db = load_database()

    query = 'broccoli stilton soup'
    # ['broccoli-soup-with-stilton']
    
    results = perform_search(query, db)
    print(results)




if __name__ == '__main__':
    start_t = time()
    main()
    print(f'\nExec time: {timedelta(seconds=time() - start_t)}')


