# PMon-5G
This project intends to develop a monitoring system for virtualized radio functions allocation based on the PlaceRAN solution.

- [Setting up the environment](#setting-up-the-environment)
 	- [Operational System](#operational-system)
	- [Kernel Prerequisites](#kernel-prerequisites)
	- [Xen Configuration](#xen-configuration)
	- [Another requirements](#another-requirements)

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

