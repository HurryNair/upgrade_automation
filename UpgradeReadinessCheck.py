from cryptography.fernet import *
from lxml import etree
from SimpliVityClass import *
from datetime import datetime

BtoGB = pow(1024, 3)
BtoMB = pow(1024, 2)
    
capacitymetric = [
    'allocated_capacity',
    'free_space',
    'capacity_savings',
    'used_capacity',
    'used_logical_capacity',
    'local_backup_capacity',
    'remote_backup_capacity',
    'stored_compressed_data',
    'stored_uncompressed_data',
    'stored_virtual_machine_data'
]

def getNodeCapacity(data):
        ndata = {
            'allocated_capacity': 0,
            'free_space': 0,
            'capacity_savings': 0,
            'used_capacity': 0,
            'used_logical_capacity': 0,
            'local_backup_capacity': 0,
            'remote_backup_capacity': 0,
            'stored_compressed_data': 0,
            'stored_uncompressed_data': 0,
            'stored_virtual_machine_data': 0,
            'compression_ratio': 0,
            'deduplication_ratio': 0,
            'efficiency_ratio': 0
        }
        for y in data:
            if 'ratio' in y['name']:
                ndata[y['name']] = y['data_points'][-1]['value']
            else:
                ndata[y['name']] = y['data_points'][-1]['value']/BtoGB
        return ndata

def logwriter(f, text):
        output = str(datetime.today()) + ": "+text+" \n"
        f.write(output)

def logopen(filename):
        f = open(filename, 'a+')
        f.write(str(datetime.today())+": Logfile opened \n")
        return f

def logclose(f):
        f.write(str(datetime.today())+": Logfile closed \n")
        f.close()        

if __name__ == "__main__":

    svtuser = 'administrator@vsphere.local'
    svtpassword = 'Password@123'
    ovc = "10.54.106.96"

    url = "https://"+ovc+"/api/"
    svt = SimpliVity(url)

    log = logopen('logfile')

    logwriter(log, "Open Connection to SimpliVity")
    svt.Connect(svtuser, svtpassword)
    logwriter(log, "Connection to SimpliVity is open")

    ready = True

    hosts = svt.GetHost()['hosts']

    for host in hosts:
        freeSpace = getNodeCapacity(svt.GetHostCapacity(host['name'])['metrics'])['free_space']
        if freeSpace > 80:
            ready = False
    
    if ready:
        logwriter(log, "Host capacity below threshold")
    else:
        logwriter(log, "Host capacity above threshold")

    ready = ready & svt.GetVMHA()

    if ready:
        logwriter(log, "VM storage high availability is safe")
    else:
        logwriter(log, "VM storage high availability is not safe")

    # if ready:
    #    for host in hosts:
    #        svt.ShutdownOVC(host['id'])

    # Add logic to pick a particular host and power it off
    # Add logic to move check if OVC shutdown has completed & then let the user know
    # Add logic to then move the ESXi host into maintenance mode
    # DRS enabled in cluster?
    
    # logfile ==> HTML
    # main heading
    # Space usage on individual nodes
    # Table
    # Cluster details
    # Represent nodes & all of its details



    

    