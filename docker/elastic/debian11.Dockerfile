FROM ghcr.io/saltstack/salt-ci-containers/debian:11 as base

ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
RUN ln -sf /etc/localtime /usr/share/zoneinfo/America/Denver

RUN apt update \
    && apt upgrade -y \
    && apt install -y curl sed vim tmux sudo tree net-tools bind9-utils lsof nmap binutils multitail supervisor iputils-ping procps

RUN mkdir -p /etc/supervisor/conf.d/
ADD docker/elastic/conf/supervisord.conf /etc/supervisor/supervisord.conf

RUN mkdir /etc/apt/keyrings \
  && curl -fsSL -o /etc/apt/keyrings/salt-archive-keyring-2023.gpg https://repo.saltproject.io/salt/py3/debian/11/amd64/SALT-PROJECT-GPG-PUBKEY-2023.gpg \
  && echo "deb [signed-by=/etc/apt/keyrings/salt-archive-keyring-2023.gpg arch=amd64] https://repo.saltproject.io/salt/py3/debian/11/amd64/3006 bullseye main" | tee /etc/apt/sources.list.d/salt.list \
  && apt update \
  && apt install -y salt-common

COPY ../../dist/salt*.whl /src/
RUN ls -lah /src \
  && /opt/saltstack/salt/salt-pip install /src/salt_analytics_framework*.whl \
  && rm -f /src/*.whl

COPY ../../examples/dist/salt*.whl /src/
RUN ls -lah /src \
  && /opt/saltstack/salt/salt-pip install --find-links /src/ salt-analytics.examples[elasticsearch] \
  && rm -f /src/*.whl


FROM base as master-2

RUN apt install -y salt-master
ADD docker/elastic/conf/supervisord.master.conf /etc/supervisor/conf.d/master.conf
ADD docker/elastic/conf/supervisord.loop-jobs.conf /etc/supervisor/conf.d/loop-jobs.conf
ADD docker/elastic/loop-jobs.sh /usr/bin/loop-jobs.sh
ADD docker/elastic/conf/analytics.master.conf /etc/salt/master.d/salt-analytics.conf
ADD docker/elastic/conf/logging.conf /etc/salt/master.d/logging.conf
RUN mkdir -p /etc/salt/master.d \
  && echo 'id: master-2' > /etc/salt/master.d/id.conf \
  && echo 'open_mode: true' > /etc/salt/master.d/open-mode.conf

CMD ["/usr/bin/supervisord","-c","/etc/supervisor/supervisord.conf"]


FROM base as minion-3

RUN apt install -y salt-minion
ADD docker/elastic/conf/supervisord.minion.conf /etc/supervisor/conf.d/minion.conf
ADD docker/elastic/conf/beacons.conf /etc/salt/minion.d/beacons.conf
ADD docker/elastic/conf/analytics.minion.conf /etc/salt/minion.d/salt-analytics.conf
ADD docker/elastic/conf/logging.conf /etc/salt/minion.d/logging.conf
RUN mkdir -p /etc/salt/minion.d \
  && echo 'id: minion-3' > /etc/salt/minion.d/id.conf \
  && echo 'master: master-2' > /etc/salt/minion.d/master.conf

CMD ["/usr/bin/supervisord","-c","/etc/supervisor/supervisord.conf"]
