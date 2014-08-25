git:
  pkg:
    - installed

build-essential:
  pkg:
    - installed

libpcre3-dev:
  pkg:
    - installed

numactl:
  pkg:
    - installed

curl:
  pkg:
    - installed

zip:
  pkg:
    - installed

p7zip-full:
  pkg:
    - installed

unrar:
  pkg:
    - installed

libpcap-dev:
  pkg:
    - installed

upx:
  pkg:
    - installed

libxml2-dev:
  pkg:
    - installed

libxslt1-dev:
  pkg:
    - installed

libldap2-dev:
  pkg:
    - installed

libevent-dev:
  pkg:
    - installed

libsasl2-dev:
  pkg:
    - installed

python:
  pkg:
    - installed

python-dev:
  pkg:
    - installed

python-setuptools:
  pkg:
    - installed

python-pip:
  cmd:
    - run
    - cwd: /
    - name: easy_install --script-dir=/usr/bin -U pip
    - reload_modules: true

python-pip-upgrade:
  cmd:
    - run
    - cwd: /
    - name: pip install setuptools --no-use-wheel --upgrade
    - reload_modules: true

/root/.pip:
  file.directory:
    - user: root
    - group: root
    - mode: 0700

/root/.pip/pip.conf:
  file.managed:
    - source: salt://pip.conf
    - user: root
    - group: root
    - mode: 0700

m2crypto:
  pkg:
    - installed

python-m2crypto:
  pkg:
    - installed

ssdeep:
  pkg:
    - installed

libfuzzy-dev:
  pkg:
    - installed
