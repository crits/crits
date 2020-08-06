# Apache 2.4 Config for Debian and Ubuntu

Provided configuration was tested on Ubuntu 16.04 LTS with Apache 2.4.19.

## Installation
```
sudo apt-get install apache2 libapache2-mod-wsgi
```

## Create Symlink to CRITs under /var/www folder
```
ln -s /data/crits/extras/www/ /var/www/crits
```

## Replace config files
Enable wsgi module on Apache2
```
sudo a2enmod wsgi
```

Load config files into /etc/apache2 folder
```
sudo cp -f /data/crits/extras/apache2.4/apache2.conf /etc/apache2/apache2.conf
sudo cp -f /data/crits/extras/apache2.4/sites-available/crits-vhost.conf /etc/apache2/sites-available/crits-vhost.conf
```

Enable your CRITs virtualhost
```
sudo a2ensite crits-vhost.conf
```

Try reloading apache2 and check for any errors
```
sudo service apache2 reload
```
