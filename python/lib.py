import pandas as pd
import json, re
import base64
import collections


def info(df):
    if isinstance(df, list):
        for i in df:
            i.info(verbose=True)
            print("=" * 30)
    else:
        df.info(verbose=True)

def base64_encode(s):
    return base64.b64encode(str(s).encode('ascii')).decode("ascii")

def find_duplicates_in_list(a):
    '''https://stackoverflow.com/questions/9835762/how-do-i-find-the-duplicates-in-a-list-and-create-another-list-with-them'''   
    print([item for item, count in collections.Counter(a).items() if count > 1], len(a), len(set(a)))
