FROM ghcr.io/saltstack/salt-ci-containers/centos-stream:9 as base

ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
RUN ln -sf /etc/localtime /usr/share/zoneinfo/America/Denver

RUN dnf update -y \
    && dnf upgrade -y \
    && dnf install -y sed vim tmux sudo tree net-tools bind-utils lsof nmap which binutils iputils epel-release procps \
    && dnf install -y --allowerasing curl \
    && dnf install -y multitail supervisor

RUN mkdir -p /etc/supervisor/conf.d/
ADD docker/elastic/conf/supervisord.conf /etc/supervisord.conf

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


FROM base as master-1

RUN dnf install -y salt-master
ADD docker/elastic/conf/supervisord.master.conf /etc/supervisor/conf.d/master.conf
ADD docker/elastic/conf/supervisord.loop-jobs.conf /etc/supervisor/conf.d/loop-jobs.conf
ADD docker/elastic/loop-jobs.sh /usr/bin/loop-jobs.sh
ADD docker/elastic/conf/analytics.master.conf /etc/salt/master.d/salt-analytics.conf
ADD docker/elastic/conf/master-1.conf /etc/salt/master.d/master-1.conf

CMD ["/usr/bin/supervisord","-c","/etc/supervisord.conf"]


FROM base as minion-1

RUN dnf install -y salt-minion
ADD docker/elastic/conf/supervisord.minion.conf /etc/supervisor/conf.d/minion.conf
ADD docker/elastic/conf/beacons.conf /etc/salt/minion.d/beacons.conf
ADD docker/elastic/conf/analytics.minion.conf /etc/salt/minion.d/salt-analytics.conf
ADD docker/elastic/conf/minion-1.conf /etc/salt/minion.d/minion-1.conf

CMD ["/usr/bin/supervisord","-c","/etc/supervisord.conf"]
