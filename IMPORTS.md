# Importing new users from the privacy spreadsheet

The standalone script that imports data from the privacy spreadsheet lives in the API project:

[~/project/api/import.py]()

That file contains notes about how we build the data source that powers this import - instead of connecting directly to the spreadsheet (there is an API, but authorization is complex), we are using the privacy spreadsheet to populate a table in BigQuery.

Before you run it:

* Make sure that the privacy app is already running in another terminal window - the API endpoint needs to be available to the script.

* Check the privacy spreadsheet and close any requests that have already been completed, so that the importer doesn't try to pull them in again (note: the user_request table in the database has a unique index on email and request type).

Start at the repository root:
```
$ cd /path/to/data-privacy-request
```
If a virtual environment hasn't already been created locally, add it:
```
$ virtualenv venv
```
Then active it:
```
$ source venv/bin/activate
```
Go into the API project and install requirements:
```
$ cd project/api/
$ pip3 install -r requirements.txt
```
To run the script:
```
$ python3 import.py
```
You'll see API responses coming back from the script, but it will also be useful to keep watch on the app log - error handling on the API still needs some work, so if there are any problems with the incoming data, you'll get more information from the API log than the import script log.
