import time
import os
import pandas as pd

from target import target

target_len = 32


def padding(base, length=32, padchar='f'):
    if len(base) > length:
        return base
    return base + padchar * (length - len(base))


def time_function(func):
    start = time.monotonic_ns()
    func()
    end = time.monotonic_ns()
    return end - start


def compare_cases(c1, c2, count=2**14):
    t1 = padding(c1)
    t2 = padding(c2)

    f1 = lambda: target(t1)
    f2 = lambda: target(t2)

    results = []

    for i in range(count):
        pair = (time_function(f1) - time_function(f2))
        results.append({'s1': c1, 's2': c2, 'time_diff': pair})

    return results


def base():
    cpu_mask = [0 for i in range(os.cpu_count())]
    cpu_mask[0] = 1
    os.sched_setaffinity(0, cpu_mask)

    base_str = ''
    while len(base_str) < 32:
        curr = []
        # Given each case here, we want a way of classifying how good a result
        # is, so we pick the best with less required samples.
        for i in range(0x20, 0x7f):
            curr += compare_cases(base_str, base_str + chr(i))

        df = pd.DataFrame(curr)
        gb = df.groupby(['s1', 's2'])
        df = gb.mean().reset_index()
        best = df[df['time_diff'] == df['time_diff'].min()]
        possible_base_str = best['s2'].values[0]

        base_str = possible_base_str
        print(base_str)


if __name__ == "__main__":
    base()
