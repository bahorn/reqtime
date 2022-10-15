"""
Script to time requests.
"""
import itertools
import time
import string
import random
import click
import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from tqdm import tqdm

# For HTTPS servers without valid certificates, like your dev / experimental
# setup.
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def padding(base, length=32, padchar='f'):
    if len(base) > length:
        return base

    return base + padchar * (length - len(base))


class TimingExperiment:
    """
    Wrapper around timing experiments.
    """

    def __init__(self, tests=5, sleep=1, cachebust=False, verifySSL=False,
                 headers={}):
        self.tests = tests
        self.sleep = sleep
        self.cachebust = cachebust
        self.verifySSL = verifySSL
        self.headers = headers
        self.headers['Accept-Encoding'] = 'identity'

    def time_request(self, url, cookies={}):
        """
        Time a single request, returning time and status code.

        Need to work on something more accurate.
        """
        params = {}
        # Cache busting by using a unique query string per request.
        if self.cachebust:
            generated = TimingExperiment.id_generator()
            params[generated] = generated

        resp = requests.get(
            url,
            params=params,
            cookies=cookies,
            headers=self.headers,
            verify=self.verifySSL,
            allow_redirects=False
        )
        resp_time = resp.elapsed.total_seconds()
        return (resp.status_code, len(resp.content), resp_time)

    def batch_time_urls(self, urls):
        """
        Intermix urls together when doing a batch time.
        """
        results = []
        pbar = tqdm(itertools.product(range(self.tests), urls))
        for i, url in pbar:
            status, resp_len, resp_time = self.time_request(
                url
            )
            result = {
                'url': url,
                'status': status,
                'size': resp_len,
                'time': resp_time,
                'test': i,
                'cachebust': self.cachebust,
                'sample_time': time.time()
            }

            results.append(result)
            time.sleep(self.sleep)

        return results

    def batch_time_cookies(self, url, cookies):
        """
        Intermix urls together when doing a batch time.
        """
        results = []
        pbar = tqdm(range(self.tests))
        for i in pbar:
            for cookie in cookies:
                status, resp_len, resp_time = self.time_request(
                    url, cookies={cookie[0]: cookie[1]}
                )
                result = {
                    'cookie': cookie[1],
                    'status': status,
                    'size': resp_len,
                    'time': resp_time,
                    'test': i,
                    'cachebust': self.cachebust,
                    'sample_time': time.monotonic()
                }

                results.append(result)
                time.sleep(self.sleep)
            time.sleep(self.sleep)

        return results

    @staticmethod
    def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))


class ResultsViewer:
    """
    Viewing the results generated by TimingExperiment
    """

    def __init__(self, data, exptype):
        self.exptype = exptype
        to_drop = ['test']

        df = pd.DataFrame(data)
        self.df = df.drop(columns=to_drop)

    def table(self):
        """
        Print a table of results.
        """
        gb = self.df.groupby([self.exptype, 'status', 'size', 'cachebust'])
        df_display = gb.agg(
            mean=('time', 'mean'),
            std=('time', 'std')
        ).reset_index().sort_values(by=self.exptype)
        print(df_display)

    def histogram(self, rows, preprocess=lambda x: x):
        """
        Display a histogram of results
        """
        for row in rows:
            plt.hist(
                self.df[self.df[self.exptype] == preprocess(row)]['time'],
                alpha=0.25,
                bins=10,
                label=row
            )
        plt.style.use('ggplot')
        plt.legend(loc='upper right')
        plt.xlabel('Time')
        plt.ylabel('Requests')
        plt.tight_layout()
        plt.show()

    def scatter(self, rows, preprocess=lambda x: x):
        for row in rows:
            base = self.df[self.df[self.exptype] == preprocess(row)]
            x = base['sample_time']
            y = base['time']
            plt.scatter(
                x=x,
                y=y,
                alpha=0.25,
                label=row
            )
        plt.style.use('ggplot')
        plt.legend(loc='upper right')
        plt.xlabel('Sample Time')
        plt.ylabel('Request Time')
        plt.tight_layout()
        plt.show()


@click.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--tests', type=int, default=5)
@click.option('--sleep', type=float, default=1)
@click.option('--cachebust', is_flag=True, default=False)
@click.option('--histogram', is_flag=True, default=False)
@click.option('--scatter', is_flag=True, default=False)
def url_test(urls, tests, sleep, cachebust, histogram, scatter):
    """
    CLI for timing a url.
    """
    ts = TimingExperiment(tests=tests, sleep=sleep, cachebust=cachebust)
    data = ts.batch_time_urls(urls)

    viewer = ResultsViewer(data, 'url')
    viewer.table()

    if histogram:
        viewer.histogram(urls)

    if scatter:
        viewer.scatter(urls)


@click.command()
@click.argument('url')
@click.argument('cookie-name')
@click.argument('cookies', nargs=-1, required=True)
@click.option('--tests', type=int, default=5)
@click.option('--sleep', type=float, default=1)
@click.option('--length', default=32)
@click.option('--cachebust', is_flag=True, default=False)
@click.option('--histogram', is_flag=True, default=False)
@click.option('--scatter', is_flag=True, default=False)
def cookie_test(url, cookie_name, cookies, length, tests, sleep, cachebust,
                histogram, scatter):
    """
    Time differences with a cookie.
    """
    appendchar = '0'
    ts = TimingExperiment(tests=tests, sleep=sleep, cachebust=cachebust)

    cleaned_cookies = list(map(
        lambda x: (cookie_name, padding(x, length, appendchar)),
        cookies
    ))

    data = ts.batch_time_cookies(
        url,
        cleaned_cookies
    )

    viewer = ResultsViewer(data, 'cookie')
    viewer.table()

    if histogram:
        viewer.histogram(
            cookies,
            preprocess=lambda x: padding(x, length, appendchar)
        )

    if scatter:
        viewer.scatter(
            cookies,
            preprocess=lambda x: padding(x, length, appendchar)
        )


@click.command()
@click.argument('url')
@click.option('--sleep', type=float, default=1)
@click.option('--points', type=int, default=100)
@click.option('--cachebust', is_flag=True, default=False)
def live_update(url, sleep, points, cachebust):
    """
    Display RTT in real time.
    """

    ts = TimingExperiment(cachebust=cachebust)

    x_data, y_data = [], []

    figure = plt.figure()
    line, = plt.plot_date(x_data, y_data, '-')

    def update(frame):
        _, _, req_time = ts.time_request(url)
        timestamp = time.monotonic()
        x_data.append(timestamp)
        y_data.append(req_time)
        line.set_data(x_data[-points:], y_data[-points:])
        figure.gca().relim()
        figure.gca().autoscale_view()
        return line,

    animation = FuncAnimation(figure, update, interval=1000*sleep)
    plt.show()


@click.group()
def main():
    pass


main.add_command(url_test)
main.add_command(cookie_test)
main.add_command(live_update)


if __name__ == "__main__":
    main()
