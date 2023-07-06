FROM ghcr.io/saltstack/salt-ci-containers/centos-stream:8 as base

ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
RUN ln -sf /etc/localtime /usr/share/zoneinfo/America/Denver

RUN dnf update -y \
    && dnf upgrade -y \
    && dnf install -y sed vim tmux sudo tree net-tools bind-utils lsof nmap which binutils iputils epel-release procps \
    && dnf install -y --allowerasing curl \
    && dnf install -y multitail supervisor

RUN mkdir -p /etc/supervisor/conf.d/
ADD docker/elastic/conf/supervisord.conf /etc/supervisor/supervisord.conf

RUN rpm --import https://repo.saltproject.io/salt/py3/redhat/9/x86_64/SALT-PROJECT-GPG-PUBKEY-2023.pub \
  && curl -fsSL https://repo.saltproject.io/salt/py3/redhat/9/x86_64/3006.repo | tee /etc/yum.repos.d/salt.repo \
  && dnf install -y salt

COPY ../../dist/salt*.whl /src/
RUN ls -lah /src \
  && /opt/saltstack/salt/salt-pip install /src/salt_analytics_framework*.whl \
  && rm -f /src/*.whl

COPY ../../examples/dist/salt*.whl /src/
RUN ls -lah /src \
  && /opt/saltstack/salt/salt-pip install --find-links /src/ salt-analytics.examples[elasticsearch] \
  && rm -f /src/*.whl


FROM base as minion-2

RUN dnf install -y salt-minion
ADD docker/elastic/conf/supervisord.minion.conf /etc/supervisor/conf.d/minion.conf
ADD docker/elastic/conf/beacons.conf /etc/salt/minion.d/beacons.conf
ADD docker/elastic/conf/analytics.minion.conf /etc/salt/minion.d/salt-analytics.conf
ADD docker/elastic/conf/logging.conf /etc/salt/minion.d/logging.conf
RUN mkdir -p /etc/salt/minion.d \
  && echo 'id: minion-2' > /etc/salt/minion.d/id.conf \
  && echo 'master: master-1' > /etc/salt/minion.d/master.conf

CMD ["/usr/bin/supervisord","-c","/etc/supervisor/supervisord.conf"]
