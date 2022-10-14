"""
Script to time requests.
"""
import time
import string
import random
import click
import requests
import pandas as pd
import matplotlib.pyplot as plt


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def time_request(url, cachebust=False):
    """
    Time a single request, returning time and status code.
    """
    params = {}
    # Cache busting by using a unique query string per request.
    if cachebust:
        generated = id_generator()
        params[generated] = generated

    resp = requests.get(url, params=params)
    resp_time = resp.elapsed.total_seconds()
    return (resp.status_code, len(resp.content), resp_time)


def batch_time(url, tests=5, sleep=1, cachebust=False):
    """
    Time a batch of requests.
    """
    results = []
    for i in range(tests):
        status, resp_len, resp_time = time_request(url, cachebust)
        result = {
            'url': url,
            'status': status,
            'size': resp_len,
            'time': resp_time,
            'test': i,
            'cachebust': cachebust
        }
        results.append(result)
        time.sleep(sleep)
    return results


@click.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--tests', type=int, default=5)
@click.option('--sleep', type=float, default=1)
@click.option('--cachebust', is_flag=True, default=False)
@click.option('--graph', is_flag=True, default=False)
def experiment(urls, tests, sleep, cachebust, graph):
    """
    CLI for timing a url.
    """
    data = []
    for test_url in urls:
        data += batch_time(
            test_url,
            tests=tests,
            sleep=sleep,
            cachebust=cachebust
        )
    df = pd.DataFrame(data)
    df = df.drop(columns=['test'])

    # Compute Mean and Std, and group by URL.
    gb = df.groupby(['url', 'status', 'size', 'cachebust'])
    df_display = gb.agg(
        mean=('time', 'mean'),
        std=('time', 'std')
    ).reset_index().sort_values(by='url')

    print(df_display)

    # Generic Histogram plot.
    if graph:
        for url in urls:
            plt.hist(
                df[df['url'] == url]['time'],
                alpha=0.25,
                bins=10,
                label=url
            )
        plt.style.use('ggplot')
        plt.legend(loc='upper right')
        plt.xlabel('Time')
        plt.ylabel('Requests')
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    experiment()
