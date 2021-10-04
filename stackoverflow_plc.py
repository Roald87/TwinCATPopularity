import matplotlib.pyplot as plt
import pandas as pd
import requests

from collections import defaultdict
from datetime import timedelta, datetime
from glob import glob


def all_tags(path):
    return [tag.split(".")[-2] for tag in glob(path)]


def cumulative_entries(dataframe):
    return (~dataframe.sort_index().duplicated()).cumsum().values


def get_latest_questions(tag: str) -> str:
    '''Get the last 30 questions for a certain tag'''
    STACKEXCHANGE_API_URL = "https://api.stackexchange.com/2.3/search"
    payload = {
        'sort': 'creation',
        'order': 'desc',
        'site': 'stackoverflow',
        'tagged': tag,
    }
    r = requests.get(STACKEXCHANGE_API_URL, params=payload)

    return r.json()


def get_question_id_and_date(questions) -> pd.DataFrame:
    '''Return question ID and creation date from questions in json'''
    new_questions = defaultdict(list)
    for item in questions['items']:
        new_questions['Post Link'].append(item['question_id'])
        date = pd.to_datetime(item['creation_date'], unit='s')
        new_questions['Creation Date'].append(date)

    new_questions = pd.DataFrame.from_dict(new_questions)
    new_questions.set_index("Post Link", inplace=True)

    return new_questions


def get_questions_from_csv(fname):
    return pd.read_csv(
        fname, index_col=0, parse_dates=['Creation Date']
    )


so_tag_style = dict(
    color="#797ca0",
    bbox=dict(
        boxstyle="round",
        ec=('#e1ecf4'),
        fc=('#e1ecf4'),
    )
)

if __name__ == "__main__":
    plt.rcParams.update({'font.size': 18})
    plt.figure(figsize=(10, 6))
    ax = plt.subplot(111)

    for tag in all_tags("*.csv"):
        latest_questions = get_question_id_and_date(
            get_latest_questions(tag)
        )
        fname = f"{tag}.csv"
        old_questions = get_questions_from_csv(fname)
        old_and_new = old_questions.combine_first(latest_questions)
        old_and_new['Cumulative questions'] = cumulative_entries(old_and_new)
        old_and_new.to_csv(fname)

        t = old_and_new['Creation Date']
        y = old_and_new['Cumulative questions']
        plt.semilogy(t, y)
        plt.text(
            t.iat[-1] + timedelta(days=150),
            y.iat[-1],
            f"{tag}: {y.iat[-1]}",
            **so_tag_style,
        )

    plt.annotate(
        f"Last updated: {datetime.today():%d %B %Y}",
        xy=(0.03, 0.95),
        xycoords='axes fraction',
        ha='left',
        color='gray',
    )
    plt.xlabel("Year")
    plt.title(
        "Number of StackOverflow questions for PLC related tags",
        pad=20,
    )

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.subplots_adjust(right=0.8)

    plt.savefig("questions.png")
