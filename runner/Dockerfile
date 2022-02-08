

# pull official base image
FROM corilo/corems:base-mono-pythonnet

# set work directory
WORKDIR /usr/src/corems-runner

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/corems-runner/requirements.txt
RUN pip install -U -r requirements.txt

# copy project
COPY . /usr/src/corems-runner

CMD ["celery", "-A", "api.celery", "worker", "--loglevel=INFO", "--concurrency=6", "-Q", "ftms.di,gcms.lowres"]
