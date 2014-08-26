# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # Global Configs
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  config.vm.define :dev do |dev|
    dev.vm.hostname = "dev"
    dev.vm.network :private_network, ip: "10.10.6.100"

    # sync aptitude cache to make provision quicker
    dev.vm.synced_folder ".apt_cache/", "/var/cache/apt/archives"

    # sync salt directories in standard locations
    dev.vm.synced_folder "salt/roots/salt/", "/srv/salt/"
    # don't map pillar since it's not currently being used
    # dev.vm.synced_folder "salt/roots/pillar/", "/srv/pillar/"

    dev.vm.provider :virtualbox do |vb|
      vb.customize ["modifyvm", :id, "--usb", "off"]
      vb.customize ["modifyvm", :id, "--memory", "2048"]
    end

    # Install curl. Salt will use curl during initial bootstrap
    # and operate properly behind HTTP proxies.
    dev.vm.provision :shell do |shell|
      shell.inline = "apt-get install -y curl"
    end

    # Add salt repository key via http, using curl, in order to properly
    # fetch the key behind HTTP proxies.
    dev.vm.provision :shell do |shell|
      shell.inline = "curl 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x4759FA960E27C0A6' | apt-key add -"
    end


    dev.vm.provision :salt do |config|
      config.run_highstate = true
      config.minion_config = "salt/roots/salt/minion.conf"
      config.verbose = true
      config.bootstrap_options = "-D"
      config.temp_config_dir = "/tmp"
    end
  end
end # Vagrant.configure
