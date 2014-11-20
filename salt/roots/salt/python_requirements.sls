include:
  - system_requirements

anyjson:
  pip.installed:
    - name: anyjson==0.3.3
    - requires:
      - cmd: python-pip

cybox:
  pip.installed:
    - name: cybox==2.1.0.5
    - requires:
      - cmd: python-pip

python-dateutil:
  pip.installed:
    - name: python-dateutil==2.2
    - requires:
      - cmd: python-pip

defusedxml:
  pip.installed:
    - name: defusedxml==0.4.1
    - requires:
      - cmd: python-pip

django:
  pip.installed:
    - name: Django==1.6.5
    - requires:
        - cmd: python-pip

django-tastypie:
  pip.installed:
    - name: django-tastypie==0.11.0
    - requires:
        - cmd: python-pip

django-tastypie-mongoengine:
  pip.installed:
    - name: django-tastypie-mongoengine==0.4.5
    - requires:
        - cmd: python-pip

importlib:
  pip.installed:
    - name: importlib==1.0.3
    - requires:
        - cmd: python-pip

mongoengine:
  pip.installed:
    - name: mongoengine==0.8.7
    - requires:
        - cmd: python-pip

pillow:
  pip.installed:
    - name: pillow==2.4.0
    - requires:
        - cmd: python-pip

pydeep:
  pip.installed:
    - name: pydeep==0.2
    - requires:
        - cmd: python-pip

python-ldap:
  pip.installed:
    - name: python-ldap==2.4.15
    - requires:
        - cmd: python-pip

python-magic:
  pip.installed:
    - name: python-magic==0.4.6
    - requires:
        - cmd: python-pip

simplejson:
  pip.installed:
    - name: simplejson==3.5.2
    - requires:
        - cmd: python-pip

stix:
  pip.installed:
    - name: stix==1.1.1.0
    - requires:
        - cmd: python-pip

requests:
  pip.installed:
    - name: requests==1.1.0
    - requires:
      - cmd: python-pip

celery:
  pip.installed:
    - name: celery==3.0.12
    - requires:
      - cmd: python-pip

ushlex:
  pip.installed:
    - name: ushlex==0.99
    - requires:
      - cmd: python-pip
