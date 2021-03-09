# misc notes (WIP)

## taskrunner structural notes:

The taskrunner block in `docker-compose.local.yml` starts up three services:
* the `taskrunner` app (calls `python manage.py run -h 0.0.0.0` to start)
* a `redis` service (from the `redis:5.0.7-alpine` image)
* redis `workers` (using an `rq` library call from within the `taskrunner` app)

`manage_task.py`:
* lives at the `taskrunner` project root
* initializes the app via an imported `create_app` method
* starts the redis workers

`project/taskrunner/__init__.py`:
* manages all the app initialization and configuration
* applies configuration settings from paths set in docker-compose
  * `APP_SETTINGS` (a Python class) contains config values that do not need to be secured
  * `APP_SECRETS` (a json file) contains private values; these will be moved to another secrets management system (chef or AWS)
* registers the taskrunner "blueprint" (a new Flask object for managing routing)
  * any new sets of endpoints (such as the incoming request API) will need to be added and registered here
  * connects to the methods in `project/taskrunner/main.py`

to add a new task template:
* define the task in the `task` table in the db (this will be replaced by an admin view from the dashboard)
* add the job template at `project/taskrunner/tasks/` (and register the class name in `project/taskrunner/tasks/__init__.py`)
* add the class import in `project/taskrunner/main.py` (e.g. `from project.taskrunner.tasks import PhonographDeleteTask`)

