# Welcome to CRITs

![Image](https://github.com/crits/crits/raw/master/extras/www/new_images/crits_logo.png)

## What Is CRITs?

CRITs is a web-based tool which combines an analytic engine with a cyber threat database that not only serves as a repository for attack data and malware, but also provides analysts with a powerful platform for conducting malware analyses, correlating malware, and for targeting data. These analyses and correlations can also be saved and exploited within CRITs. CRITs employs a simple but very useful hierarchy to structure cyber threat information. This structure gives analyst the power to 'pivot' on metadata to discover previously unknown related content.

Visit our [website](https://crits.github.io) for more information, documentation, and links to community content such as our mailing lists and IRC channel.

# Installation

CRITs is designed to work on a 64-bit architecture of Ubuntu or RHEL6 using Python 2.7. Installation has beta support for OSX using Homebrew. It is also possible to install CRITs on CentOS.

If you require the use of a 32-bit OS, you will need to download 32-bit versions of the pre-compiled dependencies.

The following instructions assume you are running Ubuntu or RHEL6 64-bit with Python 2.7. If you are on RHEL which does not come with Python 2.7, you will need to install it. If you do, ensure all python library dependencies are installed using Python 2.7. Also, make sure you install mod_wsgi against the Python 2.7 install. More information on this can be found in the Github wiki at https://github.com/crits/crits/wiki/Common-Questions.

## Installing Dependencies

CRITs has a decent amount of dependencies due to the extensive amount of functionality provided throughout the system. To install, run:

```bash

    sh script/bootstrap
```

### Adjust TCP Server Parameters:

During heavy volumes of data input or usage, the system can create a lot of network traffic. We recommend doing some server tuning to improve performance. Execute the following to decrease the amount of TCP connections piling up during batch operations:

```bash

    echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse
    echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle
```

Ensure these values are set on reboot by adding the above commands to /etc/rc.local or whatever comparable config in your Linux distro.

## (Optional) Adding Services to CRITs:

If you would like to extend the functionality of CRITs by adding services, you will have to follow these steps:

### Acquire services:

You can find some readily available community-developed services [here](https://github.com/crits/crits_services).

Put the services anywhere you would like on your server (you can even have multiple directories). With the repository above you could use something like **/data/crits_services** as your directory.

You can configure CRITs with the location(s) of the directory or directories later on using the **setconfig** management command (explained below) or in the CRITs Control Panel UI (explained below).

## Setting up MongoDB for CRITs

CRITs uses MongoDB to store authentication, session, metadata and binary information. MongoDB is a non-relational database. If you would like to read more about MongoDB and how to administer it, here are some links:

* [Starting and Stopping Mongo](http://www.mongodb.org/display/DOCS/Starting+and+Stopping+Mongo)
* [Replica Sets](http://www.mongodb.org/display/DOCS/Replica+Sets)
* [NUMA](http://www.mongodb.org/display/DOCS/NUMA)
* [Sharding](http://www.mongodb.org/display/DOCS/Sharding)

Most people starting out will run a single-server MongoDB instance. If you are unsure as to whether or not you should run a single instance or a cluster, here is some information:

#### Single server instance:

* Can run with a couple CPUs, and lots of RAM/Disk.
  *  minimum of 8-16G of RAM.
  * 10G of disk dedicated to MongoDB.
* Good for 10's of thousands of binaries, emails, indicators, and PCAPs

#### Clustered instance:

* Long term horizontal and vertical scaling.
* Recommend using 1U servers.
  * RAM and disk take priority over CPU.
  * Recommend maxing RAM per box (64G+).
  * Local storage is by far the preference here (500G+).
* Good for millions of binaries, emails, indicators, and PCAPs
  * As you need more space, you can quickly and easily add servers.

If you are looking to setup a cluster, please read and follow the information in the 'mongo_cluster.txt' file which can be found in the 'documentation' directory.

### Setting up your single server instance of MongoDB:

* Create the database directory:

```bash

    sudo mkdir -p /data/db
```

* In the 'contrib' directory that came with CRITs, you will find a mongo directory with two directories in it: one for Ubuntu, and one for RHEL. They contain start scripts for your mongo processes.  These scripts properly configure reclaim_mode on your server and start the mongod process. `cd` to the directory for your OS and run the mongod_start.sh script:

```bash

        sudo ./mongod_start.sh
```

* Verify this is working by connecting to it with the following command:

```bash

    mongo
```

This should bring up the mongo shell on localhost

## Installing CRITs using Apache

Apache is generally the preferred web server for production instances of CRITs.  If you are running a development instance, skip down to the section below titled **Installing CRITs using the Django runserver**.

### Installing the codebase:

* Create a crits user on your system:

```bash

    adduser crits
```

* Modify the crits group to contain your webserver user, any users running CRITs cronjobs, and any users running CRITs scripts.
* Create the CRITs directory structure:

```bash

    sudo mkdir -p /data/crits
```

* Put CRITs code in **/data/crits** then **cd** to it
* Change the group owner of the **logs** directory and the **logs/crits.log** file to 'crits'.

```bash

    chgrp -R crits logs
```

* The 'logs/crits.log' file needs permissions of 664.

```bash

    touch logs/crits.log
    chmod 664 logs/crits.log
```

### Edit the database file for your environment:

In the **crits/config** directory that came with the CRITs codebase, copy **database_example.py** to **database.py**:

```bash

    cp database_example.py database.py
```

Edit **database.py** and use the comments to configure your MongoDB connection information and your SECRET_KEY. If you are unsure what S3 is or if you are using it, leave **FILE_DB** alone.

### Create the default collections in MongoDB:

**NOTE**: at this point you should have MongoDB running!

Run the `create_default_collections` management command to setup your database:

```bash

    python manage.py create_default_collections
```

If you have issues running this command, it is usually because of a few things:

* There is a missing dependency. Go back through the dependency installation and
  make sure everything was installed properly.
* You did not set your SECRET_KEY in the previous step.

### Add your first user:

Take a look at the options for the **users** management command:

```bash

    python manage.py users -h
```

Use that command to setup your first admin user for CRITs. Be sure to use **-A** to set them as an admin. **Make note of the temporary password provided in the output!!**

### Set your allowed hosts:

Django needs to know the host(s) or domain name(s) that you will be serving your CRITs instance from for security purposes. To set this, run the following command:

```bash

    python manage.py setconfig allowed_hosts "foo"
```

Where "foo" is the host/domain name, or a comma separated list of names that will be serving CRITs. For more information on this, please see the [Django Reference](https://docs.djangoproject.com/en/1.5/ref/settings/#std%3asetting-ALLOWED_HOSTS).

### (Optional) Configure CRITs via management command:

If you'd like to configure CRITs prior to starting the webserver, check out the `setconfig` management command:

```bash

    python manage.py setconfig -h
```

If you'd rather the system start with sane defaults that you can modify via the web interface, you can proceed to Starting the UI. **NOTE**: Some config option changes might require a web server restart!

### Starting the UI:

We have instructions for setting up Apache on Ubuntu and RHEL. Each provides instructions for generating a temporary SSL certificate if you do not have an official one (yet!).

#### Using Apache on Ubuntu:

For installs on a new Apache instance you can follow the steps below. For existing Apache installations, use the files mentioned as a guideline.

* Stop Apache:

```bash

    sudo /etc/init.d/apache2 stop
```

* In **/etc/apache2/**, remove sites-available:

```bash

    sudo rm -rf /etc/apache2/sites-available
```

* From the **extras** folder that came with the CRITs codebase:

```bash

    sudo cp *.conf /etc/apache2
    sudo cp -r sites-available /etc/apache2
```

* In **/etc/apache2/sites-enabled**, remove the default, and link to **/etc/apache2/sites-availble/default-ssl** instead:

```bash

    sudo rm /etc/apache2/sites-enabled/*
    sudo ln -s /etc/apache2/sites-available/default-ssl /etc/apache2/sites-enabled/default-ssl
```

* Generate self-signed cert (can and **should** be replaced by an official cert from a trusted source):

```bash

    cd /tmp
    sudo openssl req -new > new.cert.csr
    sudo openssl rsa -in privkey.pem -out new.cert.key
    sudo openssl x509 -in new.cert.csr -out new.cert.cert -req -signkey new.cert.key -days 1825
    sudo cp new.cert.cert /etc/ssl/certs/crits.crt
    sudo cp new.cert.key /etc/ssl/private/crits.plain.key
```

* Enable SSL support in Apache2

```bash

    sudo a2enmod ssl
```

* Ensure that LANG environment variable is set to en_US-UTF.8 in /etc/apache2/envvars:

```
export LANG=en_US.UTF-8
```

* Start apache2

```bash

    sudo /etc/init.d/apache2 start
```

#### Using Apache on RHEL:

For installs on a new Apache instance you can follow the steps below. For existing Apache installations, use the files mentioned as a guideline. Depending on the version of Apache you may need to adjust some config values. See documentation about Django, mod_wsgi, and Apache on the Django website.

* Stop Apache:

```bash

    /etc/init.d/httpd stop
```

* From the **extras** folder of the CRITs codebase, copy the **rhel_httpd.conf** file
  to /etc/httpd/conf folder:

```bash

    sudo cp rhel_httpd.conf /etc/httpd/conf/httpd.conf
```

* From the **extras** folder of the CRITs codebase, copy the **rhel_ssl.conf** file
  to /etc/httpd/conf.d folder:

```bash

    sudo cp rhel_ssl.conf /etc/httpd/conf.d/ssl.conf
```

* Generate self-signed cert (can and **should** be replaced by an official cert
  from a trusted source):

```bash

    cd /tmp
    sudo openssl req -new > new.cert.csr
    sudo openssl rsa -in privkey.pem -out new.cert.key
    sudo openssl x509 -in new.cert.csr -out new.cert.cert -req -signkey new.cert.key -days 1825
    sudo cp new.cert.cert /etc/pki/tls/certs/crits.crt
    sudo cp new.cert.key /etc/pki/tls/private/crits.plain.key
```

* Start apache2

```bash

    sudo /etc/init.d/httpd start
```


Make sure you can only get to https://your-site.com/ and not http://your-site.com/

Proceed to the **Final Steps** section for more information on cronjobs and other useful things.

## Installing CRITs using the Django runserver

The Django runserver is our recommended web server for development or test instances of CRITs. It is quick, light, and provides a way for developers and administrators to look at the web server requests/responses in real time. It is also useful for debugging and viewing print statements.

**NOTE**: This configuration does not use SSL. If you would like to use runserver over SSL you can read about it [here](http://www.ianlewis.org/en/testing-https-djangos-development-server)

### Installing the codebase:

If you are a developer cloning a git repository, we generally recommend you clone to **~/git/crits**. If you are using a release tarball, explode the tarball in the place of your choosing.

### Edit the database file for your environment:

In the **crits/config** directory that came with the CRITs codebase, copy **database_example.py** to **database.py**:

```bash

    cp database_example.py database.py
```

Edit **database.py** using the comments to configure your MongoDB connection information and your SECRET_KEY. If you are unsure what S3 is or if you are using it, leave **FILE_DB** alone.

### Create the default collections in MongoDB:

**NOTE**: at this point you should have MongoDB running!

Run the `create_default_collections` management command to setup your database:

```bash

    python manage.py create_default_collections
```

If you have issues running this command, it is usually because of a few things:

* There is a missing dependency. Go back through the dependency installation and
  make sure everything was installed properly.
* You did not set your SECRET_KEY in the previous step.

### Add your first user:

Take a look at the options for the **users** management command:

```bash

    python manage.py users -h
```

Use that command to setup your first admin user for CRITs. Be sure to use **-A** to set them as an admin. **Make note of the temporary password provided in the output!!**

### Set your allowed hosts:

Django needs to know the host(s) or domain name(s) that you will be serving your CRITs instance from for security purposes. To set this, run the following command:

```bash

    python manage.py setconfig allowed_hosts "foo"
```

Where "foo" is the host/domain name, or a comma separated list of names that will be serving CRITs. For more information on this, please see the [Django Reference](https://docs.djangoproject.com/en/1.5/ref/settings/#std%3asetting-ALLOWED_HOSTS).

### (Optional) Configure CRITs via management command:

If you'd like to configure CRITs prior to starting the webserver, check out the `setconfig` management command:

```bash

    python manage.py setconfig -h
```

If you'd rather the system start with sane defaults that you can modify via the web interface, you can proceed to Starting the UI. **NOTE**: Some config option changes might require a web server restart!

### Starting the UI using Django runserver:

Run the following (change IP and port appropriately) to start the Django runserver:

```bash

    python manage.py runserver 1.2.3.4:8080
```

At this point you should be able to point your browser to that location and see the CRITs login screen. Proceed to the 'Final Steps' section for more information on cronjobs and other useful things.

## Final Steps

### CRITs cronjobs:

The main cronjob we recommend is for the script which executes common mapreduce jobs. These jobs do things like collect database statistics, generate Campaign information, and other useful bits of information. If you would like the Counts and stats updated on your Dashboard, you will need to add this.

We also support sending batch email notifications to users of your system. The email provided a non-detailed overview of how many changes have happened to items they are subscribed to. This cronjob also updates the notifications users will see in the interface.

#### Setup cronjobs:

As a user who has access to the codebase and to execute python code, edit their crontab:

```bash

    crontab -e
```

Add the following entries, making adjustments for the folder path and the frequency you want them to run:

```bash

    0 * * * *       cd /data/crits/ && /usr/bin/python manage.py mapreduces
    0 * * * *       cd /data/crits/ && /usr/bin/python manage.py generate_notifications
```

### (Optional) Customizing Django environment with local overrides

In most cases this step is not neccessary, but if you do have any custom django settings that you need to change for your local environment, In the **crits/config** directory you can copy **overrides_example.py** to **overrides.py**.  You can look at the example for some ideas on what you can do with this.  This file gets included at the end of the settings.py, so you can do pretty much anything you would like there, but this allows you to isolate your changes from the settings.py distributed in the package.

### CRITs Control Panel:

If you opted to configure CRITs after the web server is up, or want to change and values after it is up, you can go to the CRITs Control Panel in the navigation menu as an admin. From there, you can make your changes.

For more information, check the FAQ in the **documentation** directory and the Github wiki page. If you’d like to generate Sphinx documentation for the code, you can run **make html** in the **documentation/src** directory. There is also a Help guide in the UI.

**Thanks for using CRITs!**
