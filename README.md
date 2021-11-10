# PMon-5G
This project intends to develop a monitoring system for virtualized radio functions allocation based on the PlaceRAN solution.

- [Setting up the environment](#setting-up-the-environment)
 	- [Operational System](#operational-system)
	- [Kernel Prerequisites](#kernel-prerequisites)
	- [Xen Configuration](#xen-configuration)
	- [Another requirements](#another-requirements)
- [Downloading the VM's images](#downloading-the-vm's-images)
- [Putting up the infrastructure](#putting-up-the-infrastructure)
- [Configuring Kubernetes](#configuring-kubernetes)
	- [Generate an SSH key](#generate-an-ssh-key)
	- [Cloning and Configuring Kubespray](#cloning-and-configuring-kubespray)
- [MongoDB Deploy](#mongodb-deploy)
- [Chain Deploy](#chain-deploy)
	- [Starting the Core](#starting-the-core)
	- [Starting the Operator](#starting-the-operator)
	- [Installing Dependencies](#installing-dependencies)
	- [Starting the CU, DU and RU](#starting-cu-du-and-ru)

## Setting up the environment
To set up our environment we need to follow some initial steps. 

### Operational System

You will need an **Ubuntu 18.04 LTS (Bionic Beaver)**.

### Kernel Prerequisites
In order for us to run everything accordingly it is necessary that the kernel of your physical machine (dom0) be **linux-image-5.4.0-81-lowlatency**.
If your kernel is not this one, install it using this command:

```
sudo apt install linux-headers-5.4.0-81-lowlatency linux-image-unsigned-5.4.0-81-lowlatency
```

Reboot your machine and, on the GRUB page, choose that you want to boot the system using the newly installed kernel. Check kernel version with ```uname -r```

### Xen Configuration
In this work we use the Xen hypervisor. To install it do:

```
sudo apt update
```

```
sudo apt install xen-hypervisor-4.6-amd64 xen-tools
```

Then, reboot your machine to load the hypervisor. For more specific details visit the [Xen documentation page](https://wiki.xenproject.org/wiki/Xen_Project_Best_Practices).

### Another Requirements

Install the following dependencies to finish setting up the environment

```
sudo apt update
```

```
sudo apt install python net-tools unzip python-pip iproute2 openvswitch-switch openssh-server curl git
```
```
sudo pip install paramiko networkx
```

## Cloning this repository
Clone this repository on your machine using:

```
git clone https://github.com/LABORA-INF-UFG/PMon-5G.git
```

## Downloading the VM's images
Before starting the experiment, we must download the main image that serves as the source for the creation of the virtual machines that will be used.
To do this, get inside the repository you've just cloned and inside [XenVM](XenVM/) directory give the following command:

```
sh VMDownloader.sh
```
## Putting up the infrastructure
Let's take a broader view of what happens in this part of the experiment.
For the desired topology to be raised, there must be a file with information about the virtual machines and the links. This file is [simple_vran_infra.json](DescriptionFiles/simple_vran_infra.json). It is a customizable file that is passed as a parameter to start the experiment.
Inside [Scripts/Experiments](Scripts/Experiments) use the following command:

```
sudo python emulation.py -e vran -i ../../DescriptionFiles/simple_vran_infra.json 
```

The ```-e``` parameter tells you what type of experiment, in this case a vRAN, and the ```-i``` tells you which file contains the topology information.
This part will take at least 25 minutes to complete and at the end four virtual machines will be up with the desired configurations.
To verify that your VM's exist, use the command:

```
sudo xl list
```

## Configuring Kubernetes

### Generate an SSH key
The first step to start a cluster is to generate an SSH key and copy it to all machines that will be used in the experiment.

```
ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1
```
```
ssh-copy-id <ip_for_your_machine>
```
In our case we use four VM's we have the following commands, as an example:

```
ssh-copy-id 172.16.1.1
```
```
ssh-copy-id 172.16.2.2
```
```
ssh-copy-id 172.16.3.3
```
```
ssh-copy-id 172.16.4.4
```

### Cloning and Configuring Kubespray
The second step is to clone and configure kubespray, a tool that helps deploy a kubernetes cluster.
```
git clone https://github.com/kubernetes-sigs/kubespray.git
```
* After cloning, go into the kubespray directory and install all necessary dependencies with:

```
sudo pip3 install -r requirements.txt
```
* Copy the sample file to create your own cluster:

```
cp -rfp inventory/sample inventory/mycluster
```
* With the nano, change the version in kubernetes that will be used. In the ```kube_version``` parameter change from v1.22.2 to **v1.21.5**

```
nano inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml
```
* Now we declare the IP addresses and update the ansible inventory file with the inventory builder:

```
declare -a IPS=(172.16.1.1 172.16.2.2 172.16.3.3 172.16.4.4)
```
```
CONFIG_FILE=inventory/mycluster/hosts.yaml python3 contrib/inventory_builder/inventory.py ${IPS[@]}
```
* Finally, with ansible, we start the cluster installation:

```
ansible-playbook -i inventory/mycluster/hosts.yaml  --become --become-user=root cluster.yml
```

This installation will take around 30 minutes. After installation, check the nodes using:

```
kubectl get nodes
```

## MongoDB Deploy

Now let's deploy MongoDB so that we can store our data. Choose one of the nodes that have just been instantiated and install the database inside it. In this experiment we chose node 1.

Use the following commands:

```
wget -qO - https://www.mongodb.org/static/pgp/server-3.6.asc | sudo apt-key add -
```

```
echo "deb http://repo.mongodb.org/apt/debian stretch/mongodb-org/3.6 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list
```

```
sudo apt update
```

```
sudo apt-get install -y mongodb-org
```

```
sudo systemctl start mongod
``` 

After that modify the Mongo configuration file. In the parameter bindIp add, separating with a comma, the address of the node where you are installing MongoDB.

```
nano /etc/mongod.conf 
```
Restart the service with:

```
sudo sytemctl restart mongod
```

## Chain Deploy

### Starting the Core

Within the same node where MongoDB was installed, we will raise the RAN Core. To do this we will clone the OPlaceRAN project directory:

```
git clone https://github.com/my5G/OPlaceRAN.git
```
* Let's get into ```OPlaceRAN/images/core``` and tell the Core configuration file which address the database is running on. So we changed the **value** parameter to the IP where Mongo is:

```
nano core-deployment.yaml
```
* We then tag the node with the Core label:

```
kubectl label nodes node1 core=true
```

* And finally we start a Core:

```
kubectl apply -f core-deployment.yaml
```

### Starting the Operator

The operator is responsible for placing our Virtualized Network Functions (VNF's). To start it, let's go into ```OPlaceRAN/scheduler-manager/k8s``` and proceed with:

```
kubectl apply -f deployment.yaml
```
That simple :)

### Installing Dependecies

To upload the other components of the RAN we need to install some dependencies. The first one is the **go**. Go back to the root directory and follow the steps below to install it:

```
wget https://golang.org/dl/go1.14.15.linux-amd64.tar.gz
```
```
rm -rf /usr/local/go && tar -C /usr/local -xzf go1.14.15.linux-amd64.tar.gz
```
```
export PATH=$PATH:/usr/local/go/bin
```
```
source $HOME/.profile
```

The next dependency is **kustomize**. Install it with:

```
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh"  | bash
```
```
mv kustomize /usr/bin/
```

Go inside ```OPlaceRAN/k8s-operator/``` and:

```
make install
```



### Starting the CU, DU and RU
