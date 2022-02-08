
# pull official base image
FROM corilo/corems:base-mono-pythonnet

# set work directory
WORKDIR /usr/src/corems

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/corems/requirements.txt
RUN pip install -U -r requirements.txt

# copy project
COPY . /usr/src/corems
CMD ["gunicorn", "-w", "2","-t", "1200","--threads", "4","--worker-tmp-dir", " /dev/shm", "-b", ":80", "app:create_app()"]
