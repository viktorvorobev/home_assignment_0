[![CI checks](https://github.com/viktorvorobev/home_assignment_0/actions/workflows/ci-checks.yaml/badge.svg?branch=main)](https://github.com/viktorvorobev/home_assignment_0/actions/workflows/ci-checks.yaml)
[![linkedin](https://img.shields.io/badge/LinkedIn-0077B5?&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mr-viktor-vorobev/)
[![](https://img.shields.io/badge/My%20CV-00A98F?logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1e45Z14JU7wt4H0zuaQfNd0Xz4Yu0q1h-/view?usp=share_link)

# Exercise

Your task is to implement a program that monitors the availability of many websites over the network, produces metrics
about these and stores the metrics into an PostgreSQL database.

The website monitor should perform the checks periodically and collect the request timestamp, the response time, the
HTTP status code, as well as optionally checking the returned page contents for a regex pattern that is expected to be
found on the page. Each URL should be checked periodically, with the ability to configure the interval (between 5 and
300 seconds) and the regexp on a per-URL basis. The monitored URLs can be anything found online.

The solution should **NOT** include using any of the following:

- **Database ORM libraries** - use a Python DB API or similar library and raw SQL queries instead.
- **External Scheduling libraries** - we really want to see your take on concurrency.
- Extensive container build recipes - rather focus your effort on the Python code, tests, documentation, etc.

## Installation

1. Clone the repo
2. Create a virtual environment of a choice, e.g. with `venv`:  
   `python3.11 -m venv .venv`
3. Activate the virtual environment, e.g. for `venv` and linux:
   `source .venv/bin/activate`
4. Install the package:
   `pip install .`

## Local launch

To test with the local PostgreSQL, the attached docker-file can be used as follows:

```bash
docker compose --env-file .test.env up
```

Then to use it:

```bash
monitor --settings example_settings.yaml --envfile .test.env --verbose
```

Thanks to `argparse`, there is a help as well:

```
monitor --help                                                        
usage: monitor [-h] --settings SETTINGS [--verbose] [--envfile ENVFILE]

Util to monitor and log state of websites

options:
  -h, --help           show this help message and exit
  --settings SETTINGS  Path to settings.yaml file
  --verbose            Set logging level to DEBUG
  --envfile ENVFILE    Path to environment file with credentials of postgres
```
