# PMon-5G
This project intends to develop a monitoring system for virtualized radio functions allocation based on the PlaceRAN solution.

- [Setting up the environment](#setting-up-the-environment)
	- [Prerequisites](#prerequisites)

## Setting up the environment
To set up our environment we need to follow some initial steps.

### Prerequisites
In order for us to run everything accordingly it is necessary that the kernel of your physical machine (dom0) be **linux-image-5.4.0-81-lowlatency**
If your kernel is not this one, install it using this command:

```
sudo apt install linux-headers-5.4.0-81-lowlatency linux-image-unsigned-5.4.0-81-lowlatency
```

Reboot your machine and, on the GRUB page, choose that you want to boot the system using the newly installed kernel.

