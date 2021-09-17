# -*- coding: utf-8 -*-
import os
import sys
import json
import math
import time
import random
import paramiko
import net_model

if __name__ == '__main__':
	pass

def serialize (obj):
	return obj.__dict__
	

def deploy_infrastructure(emul_type, fileADir):

	print ("Applying first network rule")

	os.system('sysctl -w net.ipv6.conf.all.disable_ipv6=1')
	os.system('sysctl -w net.ipv6.conf.default.disable_ipv6=1')

	with open(fileADir, "r") as json_file:
		data = json.load(json_file)
		nodes = data["nodes"]
		links = data["links"]
		user = data["user"]

		dir_path = os.path.dirname(os.path.realpath(__file__))
		dir_path = dir_path[:-20]

		os.system ("mkdir {}/{}".format(dir_path, user))

		resultsdir = '/home/expran/results'

		if(os.path.isdir(resultsdir)!= 1):
			os.system ("mkdir -m 777 {}".format(resultsdir))

		if(emul_type == "video"):

			expdir = '/home/expran/expran_temp'

			if(os.path.isdir(expdir)!= 1):
				os.system ("mkdir -m 777 {}".format(expdir))
				os.system ("cp interface_default.txt {}".format(expdir))
				os.system ("cp find_interface.py {}".format(expdir))

		directory = "{}/{}/".format(dir_path, user)

		print ("Creating RAN Network")

		os.system("ovs-vsctl add-br br-exp-ran && ifconfig br-exp-ran 0 && ifconfig br-exp-ran 169.254.0.1/16")

		#Creating bridge and enabling internet access.
		#os.system("ovs-vsctl add-br br-pmon && ifconfig br-pmon up && ovs-vsctl add-port br-pmon br-pmon && ifconfig br-pmon 0 && dhclient br-pmon")
		
		

		for node in nodes:

			#Creating Node switch for each Node
			os.system("ovs-vsctl add-br sw{}".format(node["nodeNumber"]))
			os.system("ifconfig sw{} up".format(node["nodeNumber"]))
			print ("Bridge sw{} is up for NODE {}!".format(node["nodeNumber"], node["nodeNumber"]))

			if(node["nodeType"] == "Core" or node["nodeType"] == "CU" or node["nodeType"] == "DU" or node["nodeType"] == "RU"):

				#Creating a ToR switch for each Node
				os.system("ovs-vsctl add-br tor{}".format(node["nodeNumber"]))
				os.system("ifconfig tor{} up".format(node["nodeNumber"]))
				print ("Bridge tor{} is up for NODE {}!".format(node["nodeNumber"], node["nodeNumber"]))

				os.system("ip link add sw-pt{} type veth peer name tor-pt{}".format(node["nodeNumber"], node["nodeNumber"]))
			
				os.system("ifconfig sw-pt{} up".format(node["nodeNumber"]))
				os.system("ifconfig tor-pt{} up".format(node["nodeNumber"]))

				#Connecting each Node switch to each ToR switch
				os.system("ovs-vsctl add-port sw{} tor-pt{}".format(node["nodeNumber"], node["nodeNumber"]))
				os.system("ovs-vsctl add-port tor{} sw-pt{}".format(node["nodeNumber"], node["nodeNumber"]))

				print("NODE {} network configuration finished.".format(node["nodeNumber"]))
				
				s_name = 'sw{}'.format(node["nodeNumber"])
				i_name = 'tor-pt{}'.format(node["nodeNumber"])
				n_number = int(node["nodeNumber"])
				
				switch = net_model.network.get_switch(s_name, n_number)
				switch.add_interface(net_model.Interface(i_name, n_number))
				net_model.network.set_switch(s_name, switch)

				vms = node["vms"]

				for vm in vms:
					print("Cloning original disk image for NODE {} (this may take while)...".format(node["nodeNumber"]))
					#getting VM VCPUs amount
					vcpus = vm["cpu"]
					#getting VM RAM amount
					memory = vm["ram"]

					#cloning standard disk to new VM
					os.system("cp {}/XenVM/pmon-disk {}{}-pmondisk{}".format(dir_path, directory, user, vm["vmNumber"]))
					
					#cloning standard swap disk to new VM
					os.system("cp {}/XenVM/pmon-swap {}{}-pmonswap{}".format(dir_path, directory, user, vm["vmNumber"]))
					
					#editing the cfg file for the new VM
					CPU_string = "vcpus = '1'"
					RAM_string = "memory = '1024'"
					disk_string = "disk = ['file:/home/karlla/PMon-5G/XenVM/pmon-disk,xvda2,w','file:/home/karlla/PMon-5G/XenVM/pmon-swap,xvda1,w',]"
					hostname_string = "name = 'pmon'"
					bridge_string = "vif = ['script=vif-openvswitch, bridge=br-exp-ran', 'bridge=br_internet']"


					file = "{}/XenVM/pmon.cfg".format(dir_path)

					with open(file, "r") as old_cfg:

						with open("{}/pmon{}_{}.cfg".format(directory, node["nodeNumber"], vm["vmNumber"]), "w+") as new_cfg:
							
							for line in old_cfg:

								if(line.rstrip() == CPU_string):
									new_cfg.write(line.replace(CPU_string, "vcpus = '{}'".format(vcpus)))

								elif(line.rstrip() == RAM_string):
									new_cfg.write(line.replace(RAM_string, "memory = '{}'".format(memory)))

								elif(line.rstrip() == disk_string):
									new_cfg.write(line.replace(disk_string, "disk = ['phy:{}{}-pmondisk{},xvda2,w','phy:{}{}-pmonswap{},xvda1,w',]".format(directory, user, vm["vmNumber"], directory, user, vm["vmNumber"])))

								elif(line.rstrip() == hostname_string):
									new_cfg.write(line.replace(hostname_string, "name = '{}-pmon{}'".format(user, vm["vmNumber"])))

								elif(line.rstrip() == bridge_string):
									#new_cfg.write(line.replace(bridge_string, "vif = ['script=vif-openvswitch, bridge=br-exp-ran', 'script=vif-openvswitch,bridge=tor{}' ]".format(node["nodeNumber"])))
									new_cfg.write(line.replace(bridge_string, "vif = ['script=vif-openvswitch, bridge=br-exp-ran', 'script=vif-openvswitch,bridge=tor{}', 'bridge=br_internet']".format(node["nodeNumber"])))#the br-pmon bridge needs to be in the last position, so it can be attached to the eth2 inside the VM's
								else:
									new_cfg.write(line)

					old_cfg.close()
					new_cfg.close()
					print("........................... DONE! ..............................")

		print ("Setting Network Rules")

		#Creating the links between the nodes
		for link in links:

			if(link["linkType"] == "Nodes"):

				connections = link["Connections"]

				for connection in connections:

					os.system("ip link add veth{}_{} type veth peer name veth{}_{}".format(connection["fromNode"], connection["toNode"], connection["toNode"], connection["fromNode"]))
			
					os.system("ifconfig veth{}_{} up".format(connection["fromNode"], connection["toNode"]))
					os.system("ifconfig veth{}_{} up".format(connection["toNode"], connection["fromNode"]))

					os.system("ifconfig veth{}_{} mtu 1600".format(connection["fromNode"], connection["toNode"]))
					os.system("ifconfig veth{}_{} mtu 1600".format(connection["toNode"], connection["fromNode"]))

					os.system("ovs-vsctl add-port sw{} veth{}_{}".format(connection["fromNode"], connection["fromNode"], connection["toNode"]))
					os.system("ovs-vsctl add-port sw{} veth{}_{}".format(connection["toNode"], connection["toNode"], connection["fromNode"]))
					
					# Adding iface info to switch on source node
					s_name = 'sw{}'.format(connection["fromNode"])
					i_name = 'veth{}_{}'.format(connection["fromNode"], connection["toNode"])
					target = int(connection["toNode"])
					
					switch = net_model.network.get_switch(s_name, int(connection["fromNode"]))
					switch.add_interface(net_model.Interface(i_name, target))
					net_model.network.set_switch(s_name, switch)

					# Adding iface info to switch on target node
					s_name = 'sw{}'.format(connection["toNode"])
					i_name = 'veth{}_{}'.format(connection["toNode"], connection["fromNode"])
					target = int(connection["fromNode"])
					
					switch = net_model.network.get_switch(s_name, int(connection["toNode"]))
					switch.add_interface(net_model.Interface(i_name, target))
					net_model.network.set_switch(s_name, switch)
					
					capacity = connection["capacity"] * 1.01

					# 1mbps -> 1 kbyte
					burst = capacity

					os.system("tc qdisc add dev veth{}_{} root handle 1: netem delay {}ms && tc qdisc add dev veth{}_{} parent 1: handle 2: tbf rate {}mbit burst {}KB latency 0.01ms".format(connection["fromNode"], connection["toNode"], connection["delay"], connection["fromNode"], connection["toNode"], capacity, burst))
					os.system("tc qdisc add dev veth{}_{} root handle 1: netem delay {}ms && tc qdisc add dev veth{}_{} parent 1: handle 2: tbf rate {}mbit burst {}KB latency 0.01ms".format(connection["toNode"], connection["fromNode"], connection["delay"], connection["toNode"], connection["fromNode"], capacity, burst))

		print ("Creating VMs")
		cont = 0
		for node in nodes:

			if(node["nodeType"] == "Core" or node["nodeType"] == "CU" or node["nodeType"] == "DU" or node["nodeType"] == "RU"):

				vms = node["vms"]

				for vm in vms:

					os.system("xl create {}pmon{}_{}.cfg".format(directory, node["nodeNumber"], vm["vmNumber"]))
					time.sleep(15)

					print ("VM_{}_{} created".format(node["nodeNumber"], vm["vmNumber"]))

					VMip = '169.254.0.2'
					Node_VM = "_" + str(node["nodeNumber"]) + "_" + str(vm["vmNumber"]) + "_"
					Num_Final_IP = [60, cont]
					Node_IP = str(sum(Num_Final_IP))
					print("I AM NODE {}".format(node["nodeNumber"]))

					ssh = paramiko.SSHClient()
					ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					ssh.connect(VMip, username='root', password='necos')
					stdin, stdout, stderr = ssh.exec_command('ovs-vsctl add-br VM{}SWC && ovs-vsctl add-br VM{}SWD && ifconfig VM{}SWC 0 && ifconfig VM{}SWD 0 && python net_config.py {} {} && ifconfig VM{}SWC 169.254.{}.{}/16 && ifconfig VM{}SWD 172.16.{}.{}/16 && ovs-vsctl add-port VM{}SWC eth0 && ifconfig eth0 0 && ovs-vsctl add-port VM{}SWD eth1 && ifconfig eth1 0 && systemctl restart networking'.format(Node_VM, Node_VM, Node_VM, Node_VM, node["nodeNumber"], vm["vmNumber"], Node_VM, node["nodeNumber"], vm["vmNumber"], Node_VM, node["nodeNumber"], vm["vmNumber"], Node_VM, Node_VM))
					#stdin, stdout, stderr = ssh.exec_command('ifconfig eth2 200.137.197.{} netmask 255.255.255.0 && route add default gw 200.137.197.1 && dhclient eth2'.format(Node_IP)) #commands to bring up the interface that talks to the internet from the br-pmon bridge
					
					stdin, stdout, stdrr = ssh.exec_command('sysctl -w net.ipv6.conf.all.disable_ipv6=1')
					stdin, stdout, stdrr = ssh.exec_command('sysctl -w net.ipv6.conf.default.disable_ipv6=1')
					stdin, stdout, stdrr = ssh.exec_command('ssh-keygen -R 169.254.0.1')
					ssh.close()
					print("I CREATED THE VM {}".format(node["nodeNumber"]))

					#Opening another SSH session to bring down the control plane.
					#VMip = '169.254.{}.{}'.format(node["nodeNumber"], vm["vmNumber"])
					#ssh = paramiko.SSHClient()
					#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					#ssh.connect(VMip, username='root', password='necos')
					#stdin, stdout, stderr = ssh.exec_command('ifconfig VM{}SWC down && ovs-vsctl del-br VM{}SWC'.format(Node_VM, Node_VM))
					#ssh.close()
					#print("I TOOK DOWN THE CONTROL LINE".format(node["nodeNumber"]))
					
			cont += 1


#       #The container infraestructure created by eXP-RAN it is not necessary for us in PMon.
#		for node in nodes:
#
#			if(node["nodeType"] == "Core" or node["nodeType"] == "CU" or node["nodeType"] == "DU" or node["nodeType"] == "RU"):
#
#				vms = node["vms"]
#
#				for vm in vms:
#
#					containers = vm["containers"]
#					Node_VM = "_" + str(node["nodeNumber"]) + "_" + str(vm["vmNumber"]) + "_"
#
#					VMip = '169.254.{}.{}'.format(node["nodeNumber"], vm["vmNumber"])
#					ssh = paramiko.SSHClient()
#					ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#					ssh.connect(VMip, username='root', password='necos')
#
#					if(emul_type == "video"):
#
#						ctnNumbers = []
#					
#						for ctn in containers:
#
#							ctnNumbers.append(ctn["ctnNumber"])
#
#							stdin, stdout, stderr = ssh.exec_command('docker run -d -t -v /root:/mnt --name=ctn{} --net=none --cpus={} --memory={}m videostream'.format(ctn["ctnNumber"], ctn["cpu"], ctn["ram"]))
#							time.sleep(5)
#							print ("CTN_{} created inside VM_{}_{}".format(ctn["ctnNumber"], node["nodeNumber"], vm["vmNumber"]))
#							stdin, stdout, stderr = ssh.exec_command('ovs-docker add-port VM_{}_{}_SWD eth0 ctn{} --ipaddress=192.168.{}.{}/16 --gateway=192.168.0.{}'.format(node["nodeNumber"], vm["vmNumber"], ctn["ctnNumber"], vm["vmNumber"], ctn["ctnNumber"], vm["vmNumber"]))
#							time.sleep(5)
#							stdin, stdout, stderr = ssh.exec_command('ovs-vsctl list-ports VM_{}_{}_SWD > interface_at_ctn{}.txt'.format(node["nodeNumber"], vm["vmNumber"], ctn["ctnNumber"]))
#
#						stdin, stdout, stderr = ssh.exec_command('python file_copier.py {}'.format(expdir))
#						time.sleep(5)
#						stdin, stdout, stderr = ssh.exec_command('rm *.txt')
#
#						length = len(ctnNumbers)
#
#						for index in range (length):
#
#							if(index == 0):
#								os.system('diff {}/interface_default.txt {}/interface_at_ctn{}.txt > {}/diff_default_{}.txt'.format(expdir, expdir, ctnNumbers[index], expdir, ctnNumbers[index]))
#								time.sleep(3)
#								os.system('python {}/find_interface.py {}/diff_default_{}.txt {}'.format(expdir, expdir, ctnNumbers[index], ctnNumbers[index]))
#								time.sleep(3)
#
#							else:
#								os.system('diff {}/interface_at_ctn{}.txt {}/interface_at_ctn{}.txt > {}/diff_{}_{}.txt'.format(expdir, ctnNumbers[index - 1], expdir, ctnNumbers[index], expdir, ctnNumbers[index - 1], ctnNumbers[index]))
#								time.sleep(3)
#								os.system('python {}/find_interface.py {}/diff_{}_{}.txt {}'.format(expdir, expdir, ctnNumbers[index - 1], ctnNumbers[index], ctnNumbers[index]))
#								time.sleep(3)
#
#					elif(emul_type == "vran"):
#					
#						for ctn in containers:
#
#							stdin, stdout, stderr = ssh.exec_command('docker run -d -t --name=ctn{} --net=none --cpus={} --memory={}m vran'.format(ctn["ctnNumber"], ctn["cpu"], ctn["ram"]))
#							time.sleep(5)
#							print ("CTN_{} created inside VM_{}_{}".format(ctn["ctnNumber"], node["nodeNumber"], vm["vmNumber"]))
#							stdin, stdout, stderr = ssh.exec_command('ovs-docker add-port VM_{}_{}_SWD eth0 ctn{} --ipaddress=192.168.{}.{}/16 --gateway=192.168.0.{}'.format(node["nodeNumber"], vm["vmNumber"], ctn["ctnNumber"], vm["vmNumber"], ctn["ctnNumber"], vm["vmNumber"]))
#
#				ssh.close()
