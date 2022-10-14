# ReqTime

Quick tool to time requests, meant to looking at different endpoints that might
produce an observable difference.

Based partly on some ideas from the article ["Threat Alert: Private npm Packages Disclosed via Timing Attacks" by Yakir Kadkoda.](https://blog.aquasec.com/private-packages-disclosed-via-timing-attack-on-npm), which I thought was cool.

There is more research on timing attacks on web applications, but this was a
nice case where it was pretty observable.

## Usage

Install dependencies by setting up a virtualenv:
```
virtualenv -p python3 .venv
source .venv/bin/activate
pip install -r requirements.txt
```

After that, you can setup a test environment for observing a timing difference
between PHP scripts masquarading as 404 pages and real 404 pages like so:
```
docker run -p 8080:8080 -v `pwd`/test-pages:/var/www/html trafex/php-nginx
```

Then run the experiment with:
```
python3 reqtime.py url-test --sleep 0.01 --tests 100 \
    http://localhost:8080/testb.php \
    http://localhost:8080/exist.php \
    http://localhost:8080/test.html \
    http://localhost:8080/ee404.php \
    http://localhost:8080/ee404.txt
```

Which should output something like:
```
                               url  status  size  cachebust      mean       std
0  http://localhost:8080/ee404.php     404   146      False  0.001213  0.000133
1  http://localhost:8080/ee404.txt     404   146      False  0.001212  0.000140
2  http://localhost:8080/exist.php     200     0      False  0.001435  0.000138
3  http://localhost:8080/test.html     200   146      False  0.001247  0.000132
4  http://localhost:8080/testb.php     404   146      False  0.001494  0.000206
```

As you can see, several of the URLS don't exist in `test-pages`, and take ~100us
less time on my machine when they have to go though the PHP interpreter.

Outside of the flags used in the example, there is:
* `--histogram` for producing a histogram of each experiment.
* `--scatter` Scatter plot of time of request / time the request took.
* `--cachebust` for adding a random query string.


It can also do experiments where it times how long specific cookies take.
