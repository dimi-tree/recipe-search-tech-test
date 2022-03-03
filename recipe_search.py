from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from time import time
import argparse

import logging
import pickle
import re
import unicodedata

DESKTOP = Path('/Users/dimitri/Desktop')
BASE_DIR = Path('.')
PATH_TO_DATABASE = BASE_DIR / '_database.pickle'

ASCII_WORD = re.compile(r'[a-z]+')

# https://gist.github.com/sebleier/554280
STOPWORDS =  {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'}


class Colour:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def unicode_to_ascii(text):
    """Converts Unicode chars to ASCII, e.g. ç --> c."""
    # TODO: investigate further. Is there a better way?
    # TODO: perhaps we want to keep both the unicode and the normalized string?
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('unicode-escape')


def read_file(path):
    """Returns a list words, all lower-case, found in the first line of the text file that path points to."""
    with open(path, 'r') as f:
        text = f.readline().lower()
    
    text = unicode_to_ascii(text)
    return ASCII_WORD.findall(text)


def add_file_to_db(file_path, db):
    """
    Adds a new file/document to the database.
    
    NOTE: this operation is idempotent.
    """
    # TODO: what if the db does not exist?
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


def update_database(path_to_recipe, db):
    # TODO: check if it's a txt file
    file_path = Path(path_to_recipe).expanduser().resolve()

    add_file_to_db(file_path, db)
    persist_database_on_disk(db)


def load_database():
    with open(PATH_TO_DATABASE, 'rb') as f:
        return pickle.load(f)


def perform_search(query, db):
    """
    Returns a dict of the form
        { query_term: set(document_ids) }
    
    given the query in the form
        "term1 term2 term3"
    """
    start_t = time()
    query_terms = ASCII_WORD.findall(unicode_to_ascii(query))

    results = {}
    for term in query_terms:
        results[term] = db.get(term, set())
    end_t = time()

    logging.info({'query': query, 'results_found': sum(len(v) for v in results.values()), 'exec_time_in_seconds': end_t - start_t})
    
    return results


def process_args():
    """CLI interface."""
    parser = argparse.ArgumentParser(description='Recipe Search')
    subparsers = parser.add_subparsers(
        title='Commands', metavar='<command>'+8*' ')  # A little trick to get formatting right
    
    parser_create_db = subparsers.add_parser(
        'create_database', help='Create recipe database')
    parser_create_db.add_argument(
        'path_to_recipes', help='Path to directory where recipe txt files are located')

    parser_add_recipe = subparsers.add_parser(
        'add_recipe', help='Add a new recipe to database')
    parser_add_recipe.add_argument(
        'path_to_recipe', help='Path to recipe txt file')
    
    parser_find = subparsers.add_parser('find', help='Search recipe database')
    parser_find.add_argument(
        'query', help='Search query consisting of one or more words separated by space, e.g. "tomato soup"')
    parser_find.add_argument('-n', nargs='?', default=5, type=int, help='Limit the number of results returned. Defaults to 5')

    args = parser.parse_args()
    return args


def main():
    # Configure the logging system
    logging.basicConfig(
        filename='_search.log',
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s'
    )

    args = process_args()

    if getattr(args, 'path_to_recipes', None):
        create_database(args.path_to_recipes)
        print('Database created!')

    else:
        db = load_database()

        if getattr(args, 'path_to_recipe', None):
            update_database(args.path_to_recipe, db)
            print('Recipe added!')
        
        elif getattr(args, 'query', None):
            max_nb_results_to_print = args.n
            
            found = perform_search(args.query, db)
            exact_matches = set.intersection(*found.values())
            partial_matches = set.union(*found.values()) - exact_matches

            # Most relevant results, priority 1
            results_1 = list(exact_matches)

            for document_id in results_1[:max_nb_results_to_print]:
                print(f'{Colour.BOLD}{document_id}.txt{Colour.ENDC}')
            
            printed = len(results_1)
            if max_nb_results_to_print - printed > 0:
                
                # Secondary results, priority 2
                results_2 = list(partial_matches)
                for document_id in results_2[:(max_nb_results_to_print-printed)]:
                    print(f'{document_id}.txt')


if __name__ == '__main__':
    start_t = time()
    main()
    print(f'\nExec time: {timedelta(seconds=time() - start_t)}')
