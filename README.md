# GNS3 Lab Building Automation Tool

## Overview
This tool allows network engineers to automate the creation of GNS3 labs, including node deployment, linking, and project management. It eliminates manual errors such as incorrect port connections, especially when multiple links exist between the same devices. I use it daily in my personal labs, demonstrating its reliability and practical applicability.

## How to Use
In the YAML file, there is a `gns3_token` section. This is where authentication to the GNS3 server is provided. The IP address and port correspond to the values used when logging into the UI.

Here is how you can find your token:  
![GNS3 Token Example](https://github.com/fatihroot/GNS3-lab-builder/blob/main/gns3-token.png)

After entering your token (you can also add a `gns3_name` and enter the password via CLI when starting the script), you need to specify the nodes, their count, and the links (source, target, and link count).  

### Example YAML Configuration
```yaml
project_name: readme
nodes:
  - appliance_name: Alpine Linux Virt
    count: 1
  - appliance_name: Arista vEOS
    count: 4
  - appliance_name: VyOS Universal Router
    count: 2
  - appliance_name: PA-VM
    count: 1

links:
  - source: AristavEOS-1
    target: AlpineLinuxVirt-1
    count: 1
  - source: AristavEOS-2
    target: AlpineLinuxVirt-1
    count: 1
  - source: AristavEOS-3
    target: AlpineLinuxVirt-1
    count: 1
  - source: AristavEOS-4
    target: AlpineLinuxVirt-1
    count: 1
  - source: AristavEOS-1
    target: AristavEOS-2
    count: 2
  - source: AristavEOS-2
    target: AristavEOS-3
    count: 2
  - source: AristavEOS-1
    target: AristavEOS-3
    count: 2
  - source: AristavEOS-2
    target: AristavEOS-4
    count: 2
  - source: AristavEOS-1
    target: AristavEOS-4
    count: 2
  - source: AristavEOS-3
    target: VyOSUniversalRouter-1
    count: 2
  - source: AristavEOS-3
    target: VyOSUniversalRouter-2
    count: 2
  - source: AristavEOS-4
    target: VyOSUniversalRouter-1
    count: 2
  - source: AristavEOS-4
    target: VyOSUniversalRouter-2
    count: 2
  - source: VyOSUniversalRouter-1
    target: PA-VM-1
    count: 2
  - source: VyOSUniversalRouter-2
    target: PA-VM-1
    count: 2
```
Note: In the first lines, one link from every Arista to Alpine is used for management. This is not a high-scale lab, but manual configuration can be time-consuming, and it's easy to forget which port is connected to which target port. Make sure to enter the node names as defined in the GNS3 template preferences, not the names displayed after deploying the appliance.

If you have any questions or need help, feel free to open an issue or contact me!
