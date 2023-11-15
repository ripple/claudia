import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from sys import platform

import boto3
import paramiko
from requests import get

IPS = []
PUBLIC_KEYS = []
custom_ec2_instances = []
data_dir = "aws/tmp"
ip_file = f"{data_dir}/ips/network.txt"
validator_port = "2459"
cidr_block = '192.168.1.0/24'
subnet_cidr = '192.168.1.0/24'
destination_cidr_block = '0.0.0.0/0'
vpc_name = 'claudia-new-vpc'
ig_name = 'claudia-new-ig'
rt_name = 'claudia-new-rt'
sn_name = 'claudia-new-sn'
sg_name = 'claudia-new-sg'
instance_type = 't2.micro'
ec2_name = 'claudia-new-infra-instance'
zone = 'a'
key_name = ''
max_rety_attempt = 30


def run_ssh_command(ip_address, command, retry_count=0, print_details=False):
    try:
        if retry_count > max_rety_attempt:
            raise Exception(f"Could not execute command within {max_rety_attempt} attempts.\n"
                            f"Command: {command}\n"
                            f"IP: {ip_address}")
        retry_count += 1
        ssh_client = connect_ssh_client(ip_address)
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = str(stdout.read())
        error = str(stderr.read())
        if print_details:
            print(f'\nCOMMAND: {command}\n\n')
            print(f'\nSTDOUT:\n{output}\n\n')
            print(f'\nSTDERR:\n{error}\n\n')
        return stdin, output, error
    except Exception as e:
        print(f"SSH connection failed, so we will retry. Error details: {str(e)}\n")
        time.sleep(5)
        return run_ssh_command(ip_address, command, retry_count, print_details)


def sftp_upload_files(ip_address, local_path, remote_path, retry_count=0):
    try:
        if retry_count > max_rety_attempt:
            raise Exception(f"Could not upload files within {max_rety_attempt} attempts.\n"
                            f"Local Path: {local_path}\n"
                            f"Remote Path: {remote_path}\n"
                            f"IP: {ip_address}")
        retry_count += 1
        sftp_client = connect_sftp_client(ip_address)
        sftp_client.put(local_path, remote_path)
        sftp_client.close()
    except Exception as e:
        print(f"SFTP connection failed, so we will retry. Error details: {str(e)}\n")
        time.sleep(5)
        return sftp_upload_files(ip_address, local_path, remote_path, retry_count)


def are_keys_valid(aws_access_key_id, aws_secret_access_key, region_name):
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    ec2_client = session.client('ec2')

    try:
        ec2_client.describe_instance_status()
        return True
    except Exception as e:
        return False


def get_image_id(region_name):
    if region_name == 'us-east-1':
        image_id = "ami-053b0d53c279acc90"
    elif region_name == 'us-east-2':
        image_id = "ami-024e6efaf93d85776"
    elif region_name == 'us-west-1':
        image_id = "ami-0f8e81a3da6e2510a"
    elif region_name == 'us-west-2':
        image_id = "ami-03f65b8614a860c29"
    elif region_name == 'ca-central-1':
        image_id = "ami-0ea18256de20ecdfc"
    elif region_name == 'eu-central-1':
        image_id = "ami-04e601abe3e1a910f"
    elif region_name == 'ap-south-1':
        image_id = "ami-0f5ee92e2d63afc18"
    else:
        raise Exception(f'{region_name} is not supported')

    return image_id


def get_rippled_branch_list(master_node_count, release_node_count, develop_node_count):
    branches = []
    for _ in range(master_node_count):
        branches.append("master")
    for _ in range(release_node_count):
        branches.append("release")
    for _ in range(develop_node_count):
        branches.append("develop")
    return branches


def create_ec2_instance(aws_access_key_id, aws_secret_access_key, region, master_node_count, release_node_count,
                        develop_node_count):
    rippled_branch_list = get_rippled_branch_list(master_node_count, release_node_count, develop_node_count)
    count = len(rippled_branch_list)

    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)

    global key_name
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region
    )

    client = session.client('ec2', region)
    resource = session.resource('ec2', region)
    ip = get('https://api.ipify.org').text
    vpc = new_create_vpc(client, resource, cidr_block, vpc_name)
    internet_gateway_id = new_create_internet_gateway(client, vpc, ig_name)
    route_table = new_create_route_table(client, vpc, internet_gateway_id, destination_cidr_block, rt_name)
    subnet_id = new_create_subnet(client, vpc, region, zone, route_table, subnet_cidr, sn_name)
    security_group_id = new_create_security_group(client, resource, vpc, ip, sg_name)
    ami = get_image_id(region)
    date_time_stamp = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
    key_name = f"claudia-key-pair_{date_time_stamp}.pem"
    new_create_key_pair(client, key_name)
    ec2_instances = new_create_ec2_instance(resource, subnet_id, security_group_id, key_name, ami, instance_type, count)
    print("Waiting for the instances to get ready...")
    time.sleep(60)
    os.makedirs(os.path.dirname(ip_file), exist_ok=True)
    f = open(ip_file, "a")

    for index, ec2Instance in enumerate(ec2_instances):
        instance_name = f"{ec2_name}_{str(index + 1)}"
        ec2Instance.create_tags(Tags=[{"Key": "Name", "Value": instance_name}])
        ec2Instance.wait_until_running()
        ec2Instance.reload()
        ip = ec2Instance.public_ip_address
        print(f"Preparing Instance {str(index + 1)}")
        setup_claudia_and_install_rippled(ip, rippled_branch_list[index])
        public_key, validator_token = get_validator_tool_data(ip)
        IPS.append(ec2Instance.public_ip_address)
        PUBLIC_KEYS.append(public_key)
        f.write(ec2Instance.public_ip_address + "\n")
        new_instance = EC2Instance(
            index=index,
            region=region,
            id=str(ec2Instance.id),
            name=instance_name,
            type=ec2Instance.instance_type,
            private_ip=ec2Instance.private_ip_address,
            public_ip=ec2Instance.public_ip_address,
            public_dns=ec2Instance.public_dns_name,
            public_key=public_key,
            validator_token=validator_token,
            key_name=key_name,
            rippled_branch=rippled_branch_list[index]
        )
        custom_ec2_instances.append(new_instance)
    f.close()

    for ec2_instance in custom_ec2_instances:
        print(f"Configuring rippled on Instance # {str(ec2_instance.index)}")
        create_local_rippled_config_file(str(ec2_instance.index), IPS, validator_port, ec2_instance.validator_token)
        create_local_validator_file(str(ec2_instance.index), PUBLIC_KEYS)
        configure_rippled(str(ec2_instance.index), ec2_instance.public_ip)

    for ec2_instance in custom_ec2_instances:
        print(f"Starting rippled on Instance # {str(ec2_instance.index)}")
        kill_running_container = 'sudo docker ps -q --filter "name=rippled_server_instance" | ' \
                                 'xargs -r docker stop && docker ps -q --filter "name=rippled_server_instance" | ' \
                                 'xargs -r docker rm'
        start_rippled_command = f"sudo docker run --name rippled_server_instance -d " \
                                f"-p 51234:51234 -p 2459:2459 -p 6006:6006 -p 50051:50051 " \
                                f"-v ./:/opt/ripple/etc rippled_node /opt/ripple/bin/rippled"
        server_info_command = f"sudo docker exec rippled_server_instance /opt/ripple/bin/rippled server_info"
        run_ssh_command(ec2_instance.public_ip, kill_running_container, print_details=False)
        run_ssh_command(ec2_instance.public_ip, start_rippled_command, print_details=False)
        run_ssh_command(ec2_instance.public_ip, server_info_command, print_details=True)

    print(f"Config and validator files are now available at: {os.getcwd()}/aws/tmp/")
    for ec2_instance in custom_ec2_instances:
        ec2_instance.print_info()
        print("Network URLs:")
        print(f" - WebSocket (WS): ws://{ec2_instance.public_ip}:6006")
        print(f" - JSON-RPC (HTTP): http://{ec2_instance.public_ip}:51234")
        print("===")


def setup_claudia_and_install_rippled(ip, rippled_branch):
    commands = [
        'sudo apt-get clean && sudo apt-get update && '
        'sudo apt-get install ca-certificates curl gnupg python3.6 python3-pip -y',

        'sudo curl -fsSL https://deb.nodesource.com/setup_18.x | '
        'sudo -E bash - && sudo apt-get install nodejs npm -y',

        'sudo install -m 0755 -d /etc/apt/keyrings && '
        'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | '
        'sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg && sudo chmod a+r /etc/apt/keyrings/docker.gpg',

        'echo \
                "deb [arch="$(dpkg --print-architecture)" '
        'signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',

        'sudo apt-get update',

        'sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin '
        'docker-compose-plugin docker-compose -y',

        'sudo chmod 666 /var/run/docker.sock',

        'sudo docker run hello-world',

        'sudo pip3 install claudia',

        'sudo claudia --version',

        f'claudia rippled install --rippled_branch {rippled_branch}'
    ]

    for command in commands:
        run_ssh_command(ip, command, print_details=False)


def get_validator_tool_data(ip, print_sensitive_data=False):
    command = 'sudo docker run rippled_node /bin/bash -c "/opt/ripple/bin/validator-keys create_keys ' \
              '--keyfile keys.json > /dev/null && /opt/ripple/bin/validator-keys create_token --keyfile keys.json"'
    stdin, output, error = run_ssh_command(ip, command)
    validator_token = output.split('[validator_token]')[1].replace("\\n", "").replace("'", "")
    public_key = output.split('validator public key: ')[1].split('[validator_token]')[0] \
        .replace("\\n", "").replace("'", "")
    if print_sensitive_data:
        print("\n\n\nGETTING GET_VALIDATOR_TOOL_DATA")
        print(f"validator_token: {validator_token}")
        print(f"public_key: {public_key}")
    return public_key, validator_token


def create_local_rippled_config_file(instance_index, ips, port, token):
    src = "aws/rippled-example.cfg"
    dst = f"aws/tmp/configs/rippled_{instance_index}/rippled.cfg"
    if os.path.exists(dst):
        os.remove(dst)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)
    f = open(dst, "a")
    f.write("\n[ips_fixed]\n")
    for ip in ips:
        f.write(f"{ip} {port}\n")

    f.write(f"\n[validator_token]\n{token}\n\n")
    f.close()


def create_local_validator_file(instance_index, keys):
    dst = f"aws/tmp/configs/rippled_{instance_index}/validators.txt"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    f = open(dst, "w")
    f.write("[validators]\n")
    for key in keys:
        f.write(f"{key}\n")

    f.close()


def get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def connect_ssh_client(ip, username='ubuntu'):
    ssh_client = get_ssh_client()
    privkey = paramiko.RSAKey.from_private_key_file(key_name)
    ssh_client.connect(hostname=ip, username=username, pkey=privkey, timeout=10)
    return ssh_client


def connect_sftp_client(ip, username='ubuntu'):
    ssh_client = connect_ssh_client(ip, username)
    sftp_client = ssh_client.open_sftp()
    return sftp_client


def configure_rippled(instance_index, ip):
    local_rippled_config_file_path = f"{os.getcwd()}/aws/tmp/configs/rippled_{instance_index}/rippled.cfg"
    local_validator_file_path = f"{os.getcwd()}/aws/tmp/configs/rippled_{instance_index}/validators.txt"
    remote_rippled_config_file_path = 'rippled.cfg'
    remote_validator_file_path = 'validators.txt'
    sftp_upload_files(ip, local_rippled_config_file_path, remote_rippled_config_file_path)
    sftp_upload_files(ip, local_validator_file_path, remote_validator_file_path)


def new_create_vpc(client, resource, cidr_block, vpc_name):
    existing_vpcs = client.describe_vpcs(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    vpc_name,
                ]
            }
        ]
    )['Vpcs']
    vpc_count = len(existing_vpcs)
    if vpc_count == 0:
        vpcInit = client.create_vpc(CidrBlock=cidr_block)
        vpc = resource.Vpc(vpcInit["Vpc"]["VpcId"])
        vpc.create_tags(Tags=[{"Key": "Name", "Value": vpc_name}])
        vpc.wait_until_available()
        return vpc
    elif vpc_count == 1:
        existing_vpc = resource.Vpc(existing_vpcs[0]["VpcId"])
        return existing_vpc
    else:
        raise Exception(
            f"Multiple VPCs with name: {vpc_name} found. Please delete these before proceeding.")


def new_create_internet_gateway(client, vpc, ig_name):
    existing_internet_gateways = client.describe_internet_gateways(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    ig_name,
                ]
            }
        ]
    )['InternetGateways']
    ig_count = len(existing_internet_gateways)

    if ig_count == 0:
        ig_init = client.create_internet_gateway(
            TagSpecifications=[
                {'ResourceType': 'internet-gateway',
                 'Tags': [{"Key": "Name", "Value": ig_name}]}, ]
        )
        ig_id = ig_init["InternetGateway"]["InternetGatewayId"]
        vpc.attach_internet_gateway(InternetGatewayId=ig_id)
        return ig_id
    elif ig_count == 1:
        existing_ig_id = existing_internet_gateways[0]['InternetGatewayId']
        return existing_ig_id
    else:
        raise Exception(
            f"Multiple internet gateways with name: {ig_name} found. Please delete these before proceeding.")


def new_create_route_table(client, vpc, ig_id, destination_cidr_block, rt_name):
    existing_route_tables = client.describe_route_tables(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    rt_name,
                ]
            }
        ]
    )['RouteTables']
    route_table_count = len(existing_route_tables)

    if route_table_count == 0:
        routeTable = vpc.create_route_table()
        routeTable.create_route(
            DestinationCidrBlock=destination_cidr_block,
            GatewayId=ig_id
        )
        routeTable.create_tags(Tags=[{"Key": "Name", "Value": rt_name}])
        return routeTable
    elif route_table_count == 1:

        existing_route_table = existing_route_tables[0]
        return existing_route_table
    else:
        raise Exception(f"Multiple route tables with name: {rt_name} found. Please delete these before proceeding.")


def new_create_subnet(client, vpc, region, zone, route_table, subnet_cidr, sn_name):
    existing_subnets = client.describe_subnets(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    sn_name,
                ]
            }
        ]
    )['Subnets']
    subnet_count = len(existing_subnets)

    if subnet_count == 0:
        subnet = vpc.create_subnet(
            CidrBlock=subnet_cidr, AvailabilityZone="{}{}".format(region, zone))
        subnet.create_tags(Tags=[{"Key": "Name", "Value": sn_name}])
        route_table.associate_with_subnet(SubnetId=subnet.id)
        return subnet.id
    elif subnet_count == 1:
        existing_subnet_id = existing_subnets[0]['SubnetId']
        return existing_subnet_id
    else:
        raise Exception(f"Multiple subnets with name: {sn_name} found. Please delete these before proceeding.")


def new_create_security_group(client, resource, vpc, ip, sg_name):
    existing_security_groups = client.describe_security_groups(
        Filters=[
            {
                'Name': 'group-name',
                'Values': [
                    sg_name,
                ]
            }
        ]
    )['SecurityGroups']
    sg_count = len(existing_security_groups)
    if sg_count == 0:
        secGroup = resource.create_security_group(
            GroupName=sg_name, Description='Claudia Security Group', VpcId=vpc.id)

        secGroup.authorize_ingress(
            IpPermissions=[
                {
                    'FromPort': 22,
                    'IpProtocol': 'tcp',
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': 'SSH Access'
                        },
                    ],
                    'ToPort': 22,
                },
                {
                    "FromPort": -1,
                    "ToPort": -1,
                    "IpProtocol": "icmp",
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': 'Ping Access'
                        }
                    ]
                },
                {
                    "FromPort": 80,
                    "IpProtocol": "tcp",
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': 'HTTP Access'
                        }
                    ],
                    'ToPort': 80,
                },
                {
                    "FromPort": 443,
                    "IpProtocol": "tcp",
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': 'HTTPS Access'
                        }
                    ],
                    'ToPort': 443,
                },
                {
                    "FromPort": 51234,
                    "IpProtocol": "tcp",
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': '51234 Access'
                        }
                    ],
                    'ToPort': 51234,
                },
                {
                    "FromPort": 2459,
                    "IpProtocol": "tcp",
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': '2459 Access'
                        }
                    ],
                    'ToPort': 2459,
                },
                {
                    "FromPort": 6006,
                    "IpProtocol": "tcp",
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': '6006 Access'
                        }
                    ],
                    'ToPort': 6006,
                },
                {
                    "FromPort": 50051,
                    "IpProtocol": "tcp",
                    'IpRanges': [
                        {
                            'CidrIp': '{}/0'.format(ip),
                            'Description': '50051 Access'
                        }
                    ],
                    'ToPort': 50051,
                }
            ]
        )

        secGroup.create_tags(Tags=[{"Key": "Name", "Value": sg_name}])
        return secGroup.group_id
    elif sg_count == 1:
        existing_sg_id = existing_security_groups[0]['GroupId']
        return existing_sg_id
    else:
        raise Exception(f"Multiple security groups with name: {sg_name} found. Please delete these before proceeding.")


def new_create_key_pair(client, key_file_name):
    keyPair = client.create_key_pair(KeyName=key_file_name)
    if os.path.exists(key_file_name):
        os.remove(key_file_name)
    privateKeyFile = open(key_file_name, "w")
    privateKeyFile.write(dict(keyPair)['KeyMaterial'])
    privateKeyFile.close()
    if platform == "linux" or platform == "linux2" or platform == "darwin":
        os.chmod(key_file_name, 0o400)


def new_create_ec2_instance(resource, subnet_id, security_group_id, key_file_name, ami, instance_type, count):
    ec2_instances = resource.create_instances(
        ImageId=ami, InstanceType=instance_type, MaxCount=count, MinCount=count,
        NetworkInterfaces=[{'SubnetId': subnet_id, 'DeviceIndex': 0,
                            'AssociatePublicIpAddress': True, 'Groups': [security_group_id]}],
        KeyName=key_file_name)

    print(f"Created {count} EC2 instances successfully.")
    return ec2_instances


if __name__ == '__main__':
    aws_access_key_id = str(sys.argv[1])
    aws_secret_access_key = str(sys.argv[2])
    region = str(sys.argv[3])
    master_node_count = int(sys.argv[4])
    release_node_count = int(sys.argv[5])
    develop_node_count = int(sys.argv[6])
    print(f"Using these settings to deploy the network:\n"
          f"\taws_access_key_id: {aws_access_key_id}\n"
          f"\taws_secret_access_key: {aws_secret_access_key}\n"
          f"\tregion: {region}\n"
          f"\tmaster_node_count: {master_node_count}\n"
          f"\trelease_node_count: {release_node_count}\n"
          f"\tdevelop_node_count: {develop_node_count}\n")

    create_ec2_instance(
        aws_access_key_id,
        aws_secret_access_key,
        region,
        master_node_count,
        release_node_count,
        develop_node_count)


@dataclass
class EC2Instance:
    index: int
    region: str
    id: str
    name: str
    type: str
    private_ip: str
    public_ip: str
    public_dns: str
    public_key: str
    validator_token: str
    key_name: str
    rippled_branch: str

    def print_info(self):
        print(f'##########################')
        print(f'### Instance {self.index + 1} Details:###')
        print(f'##########################')
        print(f"\t- Instance Id: {self.id}")
        print(f"\t- Instance Name: {self.name}")
        print(f"\t- Private IP Address: {self.private_ip}")
        print(f"\t- Public DNS Name: {self.public_dns}")
        print(f"\t- Public IP Address: {self.public_ip}")
        print(f"\t- Public Key: {self.public_key}")
        print(f"\t- Public Validator Token: {self.validator_token}")
        print(f"\t- Rippled Source Branch: {self.rippled_branch}")
        print(f"\t- SSH connection command: \"cd {os.getcwd()};"
              f"ssh -i '{self.key_name}' ubuntu@{self.public_ip}\"\n")
