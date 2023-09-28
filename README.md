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
