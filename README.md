# data-privacy-request
Vox Media's Privacy Request Management System

## local development:

Use docker-compose.local to bring up all five services (API, taskrunner, dashboard, redis queue, redis workers):

```
docker-compose -f docker-compose.local.yml up --build
docker-compose -f docker-compose.local.yml down
```

### Dashboard

http://localhost:5002


If you want to test the API or taskrunner separately:

### API

`curl -X POST http://localhost:5001/userrequest/ -H "Content-Type: application/json" -d @example.json`

### Taskrunner

Sample tasks based on sample requests in the staging db:

* test task:  `curl -X POST http://localhost:5004/taskrunner/task/13`

* phonograph delete (no UUID):  `curl -X POST http://localhost:5004/taskrunner/task/30`

* phonograph delete (UUID):  `curl -X POST http://localhost:5004/taskrunner/task/33`

* phonograph extract with a chorus id = 31:  `curl -X POST http://localhost:5004/taskrunner/task/31`

* phonograph extract with a uuid = 32:  `curl -X POST http://localhost:5004/taskrunner/task/32`



### Redis/worker/app on host:
* start redis and rq-worker (install: https://redis.io/topics/quickstart and https://github.com/rq/rq)
```
$ redis-server
$ rq worker high default low
```
* call job directly in the interpreter
```
>>> from redis import Redis
>>> from rq import Queue
>>> queue = Queue(connection=Redis('127.0.0.1', 6379))
>>> from project.taskrunner.tasks import TestTask
>>> job = queue.enqueue(TestTask.run, 'http://nvie.com')
>>> job.result
339
```
