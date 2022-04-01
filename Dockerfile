FROM python:3.7

ADD source/requirements.txt /source/requirements.txt
RUN pip install --no-cache-dir -r /source/requirements.txt

COPY source /source


RUN chmod -R 755 /source

ENTRYPOINT ["/source/run.sh"]