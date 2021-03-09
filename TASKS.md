# Adding and testing tasks

## Adding a new Task

* Add any GCP credentials you might need for your task to: `project/taskrunner/tasks/creds/`

* Add any missing database connections to `project/config/config.json` 

* Insert a row in the `task` table in the PostgreSQL database (this will eventually be replaced by an admin view from the dashboard, but since we don't have a dashboard yet, this is it for now).
```
INSERT INTO task (job_type, executor_class, name, active, team_contact, description) VALUES ('deletion', 'GaUiDeletionTask', 'GA UI Deletion', true, 'Jory Ruscio', 'Deletion of Chorus ID from the GA UI');
```

* With the task id of the newly created record above, as row to task_instance table (currently, just use request_id from an existing request)
```
INSERT INTO task_instance (task_id, request_id, state, approved_by) VALUES (4, 12, 'active', 'Jory Ruscio');
```

  Required values:
  - `job_type`: 'Records Request' or 'Deletion'
  - `executor_class`:  The name of the code class that will be executed by the scheduler, e.g. `TestTask`
  - `name`:  An arbitrary name for the task, meant to be used in a display list on the eventual dashboard
  - `active`: Available to be executed by the runner, set to True when the task is ready for use

  Optional:
  - `execution_time`:  If the task can only to be run at a specific time, add a time of day (UTC) when the task can be sent to the queue - %H:%M:%S, e.g. 00:04:00
  - `team`: The team within the Vox/NYM organization responsible for the data source that this task interacts with
  - `team_contact`: A specific responsible developer or community contact, email address or Slack channel
  - `description`: A brief description of what this job does (may appear in the display list)
  - `data_source`: The data source that this task interacts with
  - `timeout`: If you expect the job to take longer than two minutes to run, include a timeout value in seconds (default is 120)

* Add the task file at [`project/taskrunner/tasks`](https://github.com/mechanicalgirl/taskrunner/tree/trunk/project/taskrunner/tasks)

* Register the class name in [`project/taskrunner/tasks/__init__.py`](https://github.com/mechanicalgirl/taskrunner/tree/trunk/project/taskrunner/tasks/__init__.py)

* Add the class import in [`project/taskrunner/main.py`](https://github.com/mechanicalgirl/taskrunner/tree/trunk/project/taskrunner/main.py) (e.g. `from project.taskrunner.tasks import PhonographDeleteTask`)

* Requirements for the task file:

  - A class name that matches the `task.executor_class` value in the PostgreSQL database

  - A run() method that accepts keyword args and returns a message, status code, and cost, e.g.:

```
    def run(self, **kwargs):
        """
        This is the only required method in a task - everything else is flexible
        Always return a value for `message` to be included in the response
        Include a status of 200 (success) or 500 (failure)
        """
        message = None
        status = 500     # default; return 200 on success
        cost = 0         # default; return cost based on BigQuery if applicable

        # anything can go in this block

        return {'status': status, 'message': message, 'cost': cost}
```

## Testing a Task

### Adding records

Before you can test, several records need to be in place in the database:
 - a `task` (see above)
 - at least one test user request (based on [`example.json`](https://github.com/mechanicalgirl/taskrunner/blob/trunk/example.json)
 - at least one task instance bridging each user request to a task**

User request and task instances can be added directly into the database, but there is also an API that will handle that work. 

  - Add `task.name` to [this list](https://github.com/mechanicalgirl/taskrunner/blob/trunk/project/api/main.py#L72)

  - Spin up the app:

  `docker-compose -f docker-compose.local.yml up --build`

  - In a separate terminal window, post the JSON file containing your sample user request:

  `curl -X POST http://localhost:5004/userrequest/ -H "Content-Type: application/json" -d @user_request.json`

  Make a note of the task instance ids returned by that request.

### Testing with the task instance

  - Test with a call to the `task` endpoint with your instance ids, e.g.:

  `curl -X POST http://localhost:5004/task/13`

  - Bring the app back down

  `docker-compose -f docker-compose.local.yml down`
