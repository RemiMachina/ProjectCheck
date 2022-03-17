FROM remimachina/client-base:test AS base

COPY source /source

RUN chmod -R 755 /source

ENTRYPOINT ["/source/run.sh"]