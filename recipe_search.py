from datetime import timedelta
from time import time


def main():
    """
    Spec:
    - create an index
    - have an option to add a new document, i.e. update index
    - perform 1 word search
    - log the search query
    """
    print('Search complete!')


if __name__ == '__main__':
    start_t = time()
    main()
    print(f'\nExec time: {timedelta(seconds=time() - start_t)}')
