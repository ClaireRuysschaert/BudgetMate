#######################
# Base image
#######################

FROM python:3.10-slim-bullseye AS deps

ARG RUNAS_UID=1000
ENV PYTHONUNBUFFERED 1

RUN useradd -m -u $RUNAS_UID -N bmate
WORKDIR /home/bmate

RUN mkdir -p /var/log/supervisord
RUN chown -R bmate:users /var/log/supervisord

RUN apt-get update \
    && apt-get install -y curl pkg-config libxml2-dev libxmlsec1-dev libxmlsec1-openssl gcc \
    && apt clean -y \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*

RUN curl -s https://bootstrap.pypa.io/get-pip.py | python

USER bmate

RUN python -m pip install virtualenv && rm -rf ~/.cache/pip
ENV PATH="/home/bmate/.local/bin:$PATH"
RUN virtualenv env -p /usr/local/bin/python
ENV VIRTUAL_ENV=/home/bmate/env
RUN python -m pip install --upgrade pip setuptools wheel && rm -rf ~/.cache/pip

CMD bash


#######################
# Development image
#######################
FROM deps AS dev

ENV APP_EXEC_MODE_RUNSERVER=1

USER root
RUN apt-get update \
    && apt-get install -y git graphviz graphviz-dev \
    && apt clean -y \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_*
USER bmate

COPY --chown=bmate:users ./backend/requirements.txt .
COPY --chown=bmate:users ./backend/requirements-dev.txt .
RUN pip3 install -r requirements.txt -r requirements-dev.txt \
    && rm -rf ~/.cache/pip

COPY --chown=bmate:users ./backend/BudgetMate ./BudgetMate

COPY --chown=bmate:users ./backend/supervisord.conf ./supervisord.conf

CMD supervisord -c /home/bmate/supervisord.conf
