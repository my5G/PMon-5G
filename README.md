# PMon-5G
This project intends to develop a monitoring system for virtualized radio functions allocation based on the PlaceRAN solution.

- [Setting up the environment](#setting-up-the-environment)
 	- [Operational System](#operational-system)
	- [Kernel Prerequisites](#kernel-prerequisites)
	- [Xen Configuration](#xen-configuration)
	- [Another requirements](#another-requirements)
- [Downloading the VM's images](#downloading-the-vm's-images)
- [Putting up the infrastructure](#putting-up-the-infrastructure)

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

