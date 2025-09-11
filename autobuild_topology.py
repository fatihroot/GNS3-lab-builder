import sys
import time
import yaml
import requests
import json
import random
import getpass
from requests.auth import HTTPBasicAuth

def get_gns3_session(config):
    session = requests.Session()
    if 'gns3_token' in config:
        session.headers.update({'Authorization': f'Bearer {config["gns3_token"]}'})
    else:
        session.auth = HTTPBasicAuth(config['gns3_user'], getpass.getpass("Enter your gns3 password: "))
    return session

def get_gns3_url(config):
    return f"http://{config['gns3_server']}:{config['gns3_port']}/v3"

def find_available_ports(session, base_url, project_id, node_id, count=1, used_ports=None):
    try:
        response = session.get(f"{base_url}/projects/{project_id}/nodes/{node_id}")
        response.raise_for_status()
        node_data = response.json()
        
        available_ports = []
        for port in node_data.get('ports', []):
            if port.get('link_type') == 'ethernet' and not port.get('links'):
                if used_ports and (port['adapter_number'], port['port_number']) in used_ports.get(node_id, []):
                    continue
                available_ports.append({
                    "adapter_number": port['adapter_number'],
                    "port_number": port['port_number']
                })
                if len(available_ports) == count:
                    return available_ports
        return available_ports
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to get port info of device {node_id}. {e}")
        return []

def find_node_id_by_name(session, base_url, project_id, node_name):
    try:
        response = session.get(f"{base_url}/projects/{project_id}/nodes")
        response.raise_for_status()
        nodes = response.json()
        for node in nodes:
            if node['name'] == node_name:
                return node['node_id']
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error: Can't find ID of '{node_name}'  {e}")
        return None

def create_project(session, base_url, project_name):
    try:
        response = session.get(f"{base_url}/projects")
        response.raise_for_status()
        projects = response.json()
        
        for project in projects:
            if project['name'] == project_name:
                print(f"'{project_name}' already exists. Deleting...")
                project_id_to_delete = project['project_id']
                delete_response = session.delete(f"{base_url}/projects/{project_id_to_delete}")
                delete_response.raise_for_status()
                time.sleep(2)
                break
        
        print(f"Creating project: '{project_name}'")
        project_data = json.dumps({"name": project_name})
        response = session.post(f"{base_url}/projects", data=project_data, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        
        new_project = response.json()
        print(f"Successfully created project. ID: {new_project['project_id']}")
        return new_project['project_id']
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Can't create project {e}")
        sys.exit(1)

def add_nodes(session, base_url, project_id, node_definitions):
    created_nodes = []
    current_x = -700 
    y = 0        
    x_increment = 150 
    
    try:
        response = session.get(f"{base_url}/templates")
        response.raise_for_status()
        templates = {tpl['name']: tpl['template_id'] for tpl in response.json()}
        
        print("\n Adding appliances")
        for node_def in node_definitions:
            appliance_name = node_def['appliance_name']
            count = node_def['count']
            
            if appliance_name not in templates:
                print(f"Can't find: {appliance_name}, skipping..")
                continue
            
            template_id = templates[appliance_name]
            
            for i in range(1, count + 1):
                node_name = f"{appliance_name.replace(' ', '-')}-{i}"
                node_data = json.dumps({"name": node_name, "x": current_x, "y": y})
                
                response = session.post(f"{base_url}/projects/{project_id}/templates/{template_id}", 
                                        data=node_data, 
                                        headers={'Content-Type': 'application/json'})
                response.raise_for_status()
                new_node = response.json()
                created_nodes.append(new_node)
                print(f"  - Added: {new_node['name']} (ID: {new_node['node_id']}) - location: ({current_x}, {y})")

                current_x += x_increment
        
        print("\nAll appliances added")
        time.sleep(2)
        return created_nodes
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Can't add appliances {e}")
        sys.exit(1)

def link_nodes_from_config(session, base_url, project_id, link_definitions):
    print("\nCreating links based on configuration file...")
    
    used_ports = {}

    for link_def in link_definitions:
        source_name = link_def['source']
        target_name = link_def['target']
        cable_count = link_def.get('count', 1)
        
        print(f" - Trying to connect {cable_count} cable(s) between {source_name} and {target_name}...")

        source_id = find_node_id_by_name(session, base_url, project_id, source_name)
        target_id = find_node_id_by_name(session, base_url, project_id, target_name)
        
        if not source_id or not target_id:
            print(f"  Warning: '{source_name}' or '{target_name}' not found in project. Skipping.")
            continue
            
        ports_a = find_available_ports(session, base_url, project_id, source_id, count=cable_count, used_ports=used_ports)
        ports_b = find_available_ports(session, base_url, project_id, target_id, count=cable_count, used_ports=used_ports)

        if len(ports_a) < cable_count or len(ports_b) < cable_count:
            print(f"  Warning: Not enough free ports (need {cable_count}) on '{source_name}' or '{target_name}'. Skipping.")
            continue
            
        for i in range(cable_count):
            link_data = {
                "nodes": [
                    {"node_id": source_id, **ports_a[i]},
                    {"node_id": target_id, **ports_b[i]}
                ]
            }
            
            try:
                response = session.post(f"{base_url}/projects/{project_id}/links", 
                                        data=json.dumps(link_data), 
                                        headers={'Content-Type': 'application/json'})
                response.raise_for_status()
                print(f"  Success: {source_name} [port {ports_a[i]['port_number']}] <--> {target_name} [port {ports_b[i]['port_number']}]")
                
                used_ports.setdefault(source_id, []).append((ports_a[i]['adapter_number'], ports_a[i]['port_number']))
                used_ports.setdefault(target_id, []).append((ports_b[i]['adapter_number'], ports_b[i]['port_number']))

            except requests.exceptions.RequestException as e:
                print(f"  Error: Failed to connect {source_name} and {target_name}. {e}")

if __name__ == "__main__":
    try:
        with open("config.yml", 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: Can't find 'config.yml' ")
        sys.exit(1)

    gns3_session = get_gns3_session(config)
    base_url = get_gns3_url(config)
    
    project_id = create_project(gns3_session, base_url, config['project_name'])
    
    if project_id:
        added_nodes = add_nodes(gns3_session, base_url, project_id, config['nodes'])
        
        if 'links' in config and config['links']:
            link_nodes_from_config(gns3_session, base_url, project_id, config['links'])
        else:
            print("\nError: Can't find links in configuration file, or it's empty")
            
        print("\n\n*** Completed! ***")
