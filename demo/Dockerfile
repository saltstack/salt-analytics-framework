FROM quay.io/centos/centos:stream8

RUN yum update -y
RUN rpm --import https://repo.saltproject.io/py3/redhat/8/x86_64/latest/SALTSTACK-GPG-KEY.pub
RUN curl -fsSL https://repo.saltproject.io/py3/redhat/8/x86_64/latest.repo | tee /etc/yum.repos.d/salt.repo
RUN yum install -y salt-master salt-minion tmux vim bash-completion openssh-server tree python36

# Set Locale
ENV LANG=en_US.UTF-8

# workdir for ssh
RUN mkdir -p /run/sshd

# generate server keys
RUN ssh-keygen -A

# allow root to login
RUN sed -i 's/#PermitRootLogin .*/PermitRootLogin yes/g' /etc/ssh/sshd_config

# Change root password to 'salt'
RUN echo 'root:salt' | chpasswd

EXPOSE 22

RUN python3 -m pip install tmuxp
RUN touch /var/cache/salt/events-dumped.txt /var/cache/salt/events-dumped.2.txt
COPY demo/drain3.ini /etc/drain3.ini
COPY demo/tmux-salt.yml /root/tmux-salt.yml
COPY demo/master-base.conf /etc/salt/master.d/master.conf
COPY demo/minion-base.conf /etc/salt/minion.d/minion.conf
COPY demo/analytics-*.conf /etc/salt/
COPY demo/radio/*.conf /etc/salt/radio/
COPY demo/data-remove-extension/src/saltext/ /etc/data-remove-extension/src/saltext/
COPY demo/data-remove-extension/setup.cfg /etc/data-remove-extension/
RUN mkdir /src
COPY dist/*.whl /src
RUN python3 -m pip install /src/*.whl
RUN rm -rf /src
RUN mkdir /extension
COPY demo/data-remove-extension/dist/*.whl /extension

CMD ["/usr/local/bin/tmuxp", "load", "/root/tmux-salt.yml"]
