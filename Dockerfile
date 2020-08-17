FROM python:3.7-alpine

COPY source /source

RUN bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"

RUN pip install --no-cache-dir -r /source/requirements.txt
RUN chmod -R 755 /source

ENTRYPOINT ["/source/run.sh"]