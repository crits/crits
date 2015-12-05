# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.network "forwarded_port", guest: 8080, host: 8080

  # Assumes that, if present, the "crits_services" repository is checked out
  # beside the "crits" repository.
  if File.exists?("../crits_services")
    # We use this destination because it's what the other CRITs documentation
    # refers to.
    config.vm.synced_folder "../crits_services", "/data/crits_services"
  end

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  config.vm.provision "shell", inline: <<-SHELL
    export IS_VAGRANT=1
    cd /vagrant
    script/bootstrap
  SHELL
end
