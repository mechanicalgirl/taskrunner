FROM python:3.8.0-alpine
## RUN pip install rq-dashboard
## EXPOSE 9181
## CMD ["rq-dashboard"]

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ADD ./project/dashboard/requirements.txt /usr/src/app/requirements.txt

RUN pip3 install --upgrade pip
# the slimmer alpine image is missing some gcc stuff we need for psycopg2/Flask/google to work together
RUN \
 apk update && \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 apk add libc-dev make git libffi-dev openssl-dev python3-dev libxml2-dev libxslt-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

COPY . /usr/src/app

RUN chmod +x ./manage_dash.py

# for debugging
RUN pwd
RUN ls -lha /usr/src/app
# CMD echo Hello world Dashboard

# ENTRYPOINT ["python3"]
# CMD ["/usr/src/app/manage_dash.py", "run", "-h", "0.0.0.0"]
