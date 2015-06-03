#!/bin/bash
# Date: 3 June 2015
# Version: 1.3.5
# This script file is for use of installing CRITs onto CentOS machines
# it is based on crits/script/bootstrap and crits/script/server by MITRE Corp

#=========================================================================
# List for CRITs Service Files to be moved back into crits_services
LIST=(crits_scripts data_miner_service diffie_service
machoinfo_service meta_checker office_meta_service opendns_service pdfinfo_service peinfo_service pyew ssdeep_service timeline_service totalhash_service unswf_service upx_service whois_service yara_service zip_meta_service taxii_service stix_validator_service shodan_service passivetotal_service anb_service carver_service entropycalc_service cuckoo_service __init__.py README.md UPDATING)
#=========================================================================

#This is the Default Port for the CRITs server, User can change during the script
declare -i PORT=80

# Creates Default Database Files
create_files() 
{
    if [ ! -e /data ];
    then
        echo -e "\e[1;36mCreating CRITs Folders\e[0m"
        sudo mkdir -v -p /data/db
        sudo mkdir -v -p /data/logs
    fi
	# The original script had root remain the owner of these files but
	# that ended up causing some difficulties
	sudo chown -R $USER:$GROUP /data
	chmod -R -v 0755 /data 
}
# Gets python 2.7 while leaving system python intact
get_python()
{
	sudo yum -y update
	sudo yum -y groupinstall "Development tools"
	sudo yum -y install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel php-ldap 
	sudo yum -y install xz-libs
	#Download Tarball and Install Python
	if [[ $(python --version 2>&1) == "Python 2.7.9" ]]; 
	then
		echo -e "\e[1;32mPython 2.7.9 Already Installed\e[0m"
	else
		wget http://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
		tar -xzf Python-2.7.9.tgz
		
		cd Python-2.7.9
		./configure --prefix=/usr/local --enable-unicode=ucs4 --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
		sudo make && sudo make altinstall
		cd ..
		sudo rm -rf Python-2.7.9.tgz
		sudo rm -rf Python-2.7.9
		# Add Python To Path
		cd /usr/local/bin
		sudo ln -s python2 python
		sudo ln -s python2.7 python2
		cd ~
	fi
}
# Install pip, a needed installation tool
get_pip()
{
    echo "Installing Pip"
    #This can be done with sudo /usr/local/bin/easy_install pip
    wget https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py
    sudo /usr/local/bin/python2.7 get-pip.py
    rm -f get-pip.py
    if [ -f /usr/local/bin/pip ];
    then
        echo -e "\e[1;32mPip Successfully Installed!\e[0m"
    else
        echo -e "\e[1;31mPip Could not Be Installed! Exiting\e[0m"
        exit_restart
    fi
}
# Downloads crits and crits_services
get_crits()
{
	cd ~
    if [ ! -f crits ];
        then
            echo -e "\e[1;36mDownloading CRITs in Home Directory\e[0m"
            sudo yum -y install git
            git clone https://github.com/crits/crits_services
            git clone https://github.com/crits/crits
    else
        echo -e "\e[1;32mCRITs Folders Already Exist!\e[0m"
    fi
}
# Installs basic CRITs dependencies
depend_crits()
{
	echo -e "\e[1;36mInstalling CRITs Dependencies\e[0m"
	
	cd ~
	if [ ! -f /etc/yum.repos.d/rpmforge.repo ];
	then
		echo -e "\e[1;36mDownloading rpmforge.repo\e[0m"
		wget http://apt.sw.be/redhat/el6/en/x86_64/rpmforge/RPMS/rpmforge-release-0.5.3-1.el6.rf.x86_64.rpm
		sudo rpm -i rpmforge-release-0.5.3-1.el6.rf.x86_64.rpm
		rm rpmforge-release-0.5.3-1.el6.rf.x86_64.rpm		
	fi
	if [ ! -f /etc/yum.repos.d/epel.repo ];
	then
		echo -e "\e[1;36mInstalling epel.repo\e[0m"
		sudo yum -y install epel-release
	fi

	cd ~/crits

    if [ -f /usr/local/bin/pip ]; then
        echo -e "\e[1;32mPip Already Installed\e[0m"
    else
        get_pip
    fi
    #lxml Dependencies
    sudo env "PATH=$PATH" yum -y install python-devel libxml2-devel libxslt-devel
	sudo /usr/local/bin/pip install lxml python-magic olefile

	sudo env "PATH=$PATH" yum -y install make gcc gcc-c++ kernel-devel pcre pcre-devel curl libpcap-devel  zip unzip gzip bzip2 swig
sudo env "PATH=$PATH" yum -y install p7zip
	sudo env "PATH=$PATH" yum -y install unrar libffi-devel
	sudo env "PATH=$PATH" yum -y install libyaml 
	sudo env "PATH=$PATH" yum -y install upx
	sudo env "PATH=$PATH" yum -y install openldap-devel
	sudo /usr/local/bin/pip install python-ldap
#	sudo env "PATH=$PATH" yum -y install ssdeep
	# Check if Mongo is Installed	
	if [ ! -f /usr/local/bin/mongod ]; 
	then	
		curl http://downloads.mongodb.org/linux/mongodb-linux-x86_64-2.6.4.tgz > mongodb-linux-x86_64-2.6.4.tgz
		tar -zxvf mongodb-linux-x86_64-2.6.4.tgz
		sudo cp ./mongodb-linux-x86_64-2.6.4/bin/* /usr/local/bin/
		rm  mongodb-linux-x86_64-2.6.4.tgz
		rm -r mongodb-linux-x86_64-2.6.4
	else
		echo -e "\e[1;32mMongo Already installed\e[0m"
	fi
	echo -e "\e[1;36mInstalling Python Dependencies\e[0m"
    echo -e "\e[1;31m\t\t\tWarning: Hardcoded crits/requirements\e[0m"
    # crits/requirements.txt was giving some problems with pydeep the original was:
    # sudo /usr/local/bin/pip install -r requirements.txt
    # They are repeats but this section is the hard coded version of crits/requirements.txt except for pydeep
    sudo /usr/local/bin/pip install Django==1.6.11 Pillow amqp anyjson billiard biplist celery cybox==2.1.0.11 defusedxml
    sudo /usr/local/bin/pip install django-celery django-tastypie==0.11.0 django-tastypie-mongoengine==0.4.5
    sudo /usr/local/bin/pip install kombu lxml m2crypto mongoengine==0.8.8 pydot pymongo==2.7.2 pyparsing
    sudo /usr/local/bin/pip install python-dateutil python-ldap python-magic==0.4.6 python-mimeparse pytz pyyaml
    sudo /usr/local/bin/pip install requests setuptools simplejson
    sudo /usr/local/bin/pip install six stix==1.1.1.0 ushlex wsgiref

    #Pydeep Installation-github.com/kblanda/pydeep/blob/master/INSTALL
	# ssdeep installation
    echo -e "\e[1;36mInstalling ssdeep and pydeep\e[0m"
	cd ~
	wget http://sourceforge.net/projects/ssdeep/files/ssdeep-2.13/ssdeep-2.13.tar.gz
	tar -vxzf ssdeep-2.13.tar.gz 
	cd ssdeep-2.13
	./bootstrap
	./configure
	make
	sudo env "PATH=$PATH" make install
	# pydeep installation
	cd ~
	sudo /usr/local/bin/pip install pydeep
	rm ssdeep-2.13.tar.gz
	rm -rf ssdeep-2.13

}
#=====================================================================================
# Installs dependencies for CRITs services located in $LIST
# There will be repeats as to allow the deletion of certain modules without having
# to worry about libraries getting lost.
# NOTE: Delete service name in $LIST if removed otherwise website will fail
#=====================================================================================
depend_services()
{
	cd ~
	echo -e "\e[1;36mInstalling CRITs Services Dependencies\e[0m"
    #Check if Python is Installed
    if [[ $(python --version 2>&1) == "Python 2.7.9" ]];
    then
        echo -e "\e[1;32mPython 2.7.9 Already Installed\e[0m"
    else
        get_python
    fi
    #Check if Pip is installed
    if [ -f /usr/local/bin/pip ]; then
        echo -e "\e[1;32mPip Already Installed\e[0m"
    else
        get_pip
    fi

	#whois_service dependencies
    echo -e "\e[1;36m\t\tInstalling whois_service Dependencies\e[0m"
	sudo /usr/local/bin/pip install whois
	sudo env "PATH=$PATH" yum -y install python-requests.noarch
	#upx_service
    echo -e "\e[1;36m\t\tInstalling upx_service Dependencies\e[0m"
	sudo env "PATH=$PATH" yum -y install upx
	#unswf_service
    echo -e "\e[1;36m\t\tInstalling unswf_service Dependencies\e[0m"
	sudo /usr/local/bin/easy_install pylzma
	#total_hash
    echo -e "\e[1;36m\t\tInstalling total_hash Dependencies\e[0m"
	sudo env "PATH=$PATH" yum -y install python-lxml
	sudo /usr/local/bin/pip install bitstring pefile
	#taxii_service
    echo -e "\e[1;36m\t\tInstalling taxii_service Dependencies\e[0m"
	sudo /usr/local/bin/pip install libtaxii
	sudo env "PATH=$PATH" yum -y install m2crypto
	#stix_validator_service
    echo -e "\e[1;36m\t\tInstalling stix_validator_service Dependencies\e[0m"
	sudo /usr/local/bin/pip install lxml xlrd ordereddict stix-validator
	#shodan_service
    echo -e "\e[1;36m\t\tInstalling shodan_sevice Dependencies\e[0m"
	sudo /usr/local/bin/easy_install shodan
	#pyew
    echo -e "\e[1;36m\t\tInstalling pyew Dependencies\e[0m"
	sudo /usr/local/bin/pip install mod_pywebsocket pexpect==2.4
    wget https://github.com/joxeankoret/pyew/archive/VERSION_3X.zip
    unzip VERSION_3X.zip
    rm VERSION_3X.zip
#chminfo Only Unbnuntu systems can install libchm1, pychm is in the extras
#echo -e "\e[1;36m\t\tCan't Install chminfo_service Dependencies\e[0m"
#sudo apt-get pychm libchm1
	#crits_scripts
    echo -e "\e[1;36m\t\tInstalling crits_scripts Dependencies\e[0m"
	sudo /usr/local/bin/pip install mod_pywebsocket
	#pdfinfo_service
    echo -e "\e[1;36m\t\tInstalling pdfinfo_service Dependencies\e[0m"
	sudo env "PATH=$PATH" yum -y install numpy
	#yara.readthedocs.org
	echo -e "\e[1;36mInstalling yara\e[0m"
	wget https://github.com/plusvic/yara/archive/v3.3.0.tar.gz
	tar -zxf v3.3.0.tar.gz
	cd yara-3.3.0/
	./bootstrap.sh
	./configure
	make 
	sudo env "PATH=$PATH" make install
	echo -e "\e[1;36mInstalling Yara-Python\e[0m"
	cd yara-python
	python setup.py build
	sudo /usr/local/bin/python2.7 setup.py install
	cd ~
	rm v3.3.0.tar.gz
	rm -Rf yara-3.3.0
    #cuckoo_service Note: Doesn't install a cuckoo instance
    echo -e "\e[1;36m\t\tInstalling cuckoo_service Dependencies\e[0m"
    sudo /usr/local/bin/pip install requests
}
# Moves Supported (CentOS Compatible)  services into crits_sevices
move_not_supported()
{
	echo -e "\e[1;36mMoving Supported CRITs Services\e[0m"
	cd ~
	mv ~/crits_services/* ~/
	cd ~
	for file in "${LIST[@]}"
	do
		if [ -e "$file" ];
		then
			mv $file ~/crits_services/
		fi
	done
}
# Creates CRITs username and password for administrator	
server_setup()
{
	cd ~/crits
	touch logs/crits.log
	chmod 0644 logs/crits.log
	cp crits/config/database_example.py crits/config/database.py
	SC="$(python contrib/gen_secret_key.py)"
	sed -i'' -e "s/.*SECRET_KEY.*/SECRET_KEY = \'"$SC"\'/" crits/config/database.py

    pgrep mongod >/dev/null 2>&1
    if [ $? -ne 0 ]
    then
        echo -e "\e[1;36mStarting Mongod\e[0m"
        sh contrib/mongo/mongod_start.sh
    fi

    python manage.py create_default_collections
	if [ $? -eq 0 ] 
	then
		read -p "Username: " USERNAME
		read -p  "First name: " FIRSTNAME
		read -p "Last name: " LASTNAME
		read -p "Email address: " EMAIL
		read -p "Organization name: " ORG
		
		python manage.py users -a -A -e "$EMAIL" -f "$FIRSTNAME" -l "$LASTNAME" -o     "$ORG" -u "$USERNAME"

		echo -e "\e[1;31mThis is Your Temp Password\e[0m"
	fi
}
# Starts up everything needed to run the server
# Checks if mongodb is running, starts it if not and then
# starts the server
run_server()
{
	local IP_LIST=$(ifconfig | awk '/inet addr/{print substr($2,6)}')
	declare -i OPTION=1
	declare -i CHOICE=-1

	echo -e "\e[1;34mStarting Server\e[0m"
	echo -e "\e[1;31mTo Restart Server: sh $0 $STEP"
	echo -e "Warning MongoDB Will Still be Running After Server Ends\e[0m"
	cd ~/crits
	pgrep mongod >/dev/null 2>&1
	if [ $? -ne 0 ]
	then
		sh contrib/mongo/mongod_start.sh
	fi

	read -p "What Port Do You Want to Use: " INPUT
	if [[ $INPUT =~ ^-?[0-9]+$ ]];
	then
		#This checks to see if the firewall is open to that port
		PORT=$INPUT
   		OUT=$(sudo cat /etc/sysconfig/iptables.save)
		if [[ "$OUT" == *"--dport $PORT -m comment --comment"* ]];
   	 	then
    	   		ip_change $PORT
   	 	fi
	else
    		echo "Not a Valid Port Using Port 80"
	fi
	#Fetch IP's to user
	echo -e "\e[1;32mAvailable IP Addresses to use:"
	for IP in $IP_LIST
	do
		echo -e "\t"$OPTION")" $IP
		((OPTION++))
	done
	echo -e -n "\e[0mWhich IP Address: " 
	read CHOICE
	#Turns IP_LIST into an array
	IP_LIST=($IP_LIST)
	
    #Needs to run as Sudo due to being on port 80
	echo -e "\nRunning Server on ${IP_LIST[CHOICE-1]} Port $PORT" || exit
	sudo /usr/local/bin/python2.7 manage.py runserver ${IP_LIST[CHOICE-1]}:$PORT
}
# Error Message
exit_restart()
{
	echo ""
	echo -e "\e[1;34mError: To restart at this step: sh $0 $1\e[0m"
	exit
}
# Verify System Architecture
# This script needs to be CentOS 64 bit
verify()
{
	echo -e "\e[1;36mTesting Computer's Architecture\e[0m"
	ARCH=$(uname -m | sed 's/x86_//;s/i[3-6]86/32/')
	OS=$(cat /etc/redhat-release) || OS="Unknown"
	if [[ "$OS" == *"CentOS"* ]]; then
		echo -e "\e[1;32mCentOS Test Passed\e[0m"
	else
		echo ""
		echo -e "\e[1;31mOS: $OS, need CentOS\e[0m"
		exit
	fi

	if [ "$ARCH" = "64" ]; then
		echo -e "\e[1;32mArchitecure 64 Passed\e[0m"
	else
		echo -e "\e[1;31mArchitecure: $ARCH, need 64\e[0m"
		exit
	fi
}
# Modify IP tables to allow communication
# Checks to see if the port the user selects is in the IP table, if not it will
# insert it in. 
ip_change()
{
	echo -e "\e[1;36mChanging IP Tables for Open Communication\e[0m"

    OUT=$(sudo cat /etc/sysconfig/iptables)
	if [[ "$OUT" == *"--dport $1 -m comment --comment"* ]];
	then
		echo -e "\e[1;32mPort $1 Open\e[0m"
		return
	else
        echo -e "\e1;32mOpening Port $1 now\e[0m"
		sudo iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport $1 -m comment --comment "Web server" -j ACCEPT
		sudo service iptables save
	fi
}

#==============================================================================
# This is the Beginning of the Script, due to previous problems installing
# CRITs, it's better to not have the script run as root.
#==============================================================================
# Verify Script is not being run as root
if [ $EUID == 0 ] 
then
	echo -e "\e[1;31mDo Not Run This Script As Root!\e[0m"
	exit
fi
# Sees if there is an argument
if [[ $1 == "" ]]; then
	STEP=1
	echo -e "\e[1;34mThis Script Will Automatically Install CRITS on CentOS in the Users Home Directory\e[0m"
	echo -e "\e[1;34mIt assumes that the user can use sudo\e[0m"
else
	STEP=$1
fi

cd ~
while [ $STEP -lt 10 ]; do
	case $STEP in 
		1)
			verify ||exit_restart $STEP ;;
		2)
			create_files ||exit_restart $STEP ;;
		3)
			get_python ||exit_restart $STEP ;;
		4)
			get_crits ||exit_restart $STEP ;;
		5)	
			depend_crits ||exit_restart $STEP ;;
		6)
			depend_services ||exit_restart $STEP ;;
		7)
			move_not_supported ||exit_restart $STEP ;;
		8)
			server_setup ||exit_restart $STEP ;;
		9)	
			run_server ||exit_restart $STEP ;;
		*)
			exit
			;;
	esac
	((STEP++)) 
done
