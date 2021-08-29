from SimpliVityClass import *
from datetime import datetime
from jinja2 import Template

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
    f.write(str(datetime.today())+": Session start \n")
    return f


def logclose(f):
    f.write(str(datetime.today())+": Session End \n")
    f.close()


if __name__ == "__main__":

    svtuser = 'administrator@vsphere.local'
    svtpassword = 'Password@123'
    ovc = "10.54.106.96"

    url = "https://"+ovc+"/api/"
    svt = SimpliVity(url)

    log = logopen('logfile3.txt')

    logwriter(log, "Open Connection to SimpliVity")
    svt.Connect(svtuser, svtpassword)
    logwriter(log, "Connection to SimpliVity is open. Connected to OVC " + ovc)

    hosts = svt.GetHost()['hosts']

    host_list = []
    space_list = []
    space_list_int = []
    host_version = []

    mgmt_ip_list = []
    fed_ip_list = []
    stor_ip_list = []

    mgmt_ip_mtu = []
    fed_ip_mtu =[]
    stor_ip_mtu =[]

    vc_ip_list = []

    federation_health = True # Given that every host is alive and every cluster is arbiter connected

    host_hardware_list = []

    map = {}

    for host in hosts:
        logwriter(log, "Evaluating host " + host['name'])
        host_list.append(host['name'])
        host_version = host['version']

        host_hardware_list.append(svt.GetHostHardware(host['name']))
        
        mgmt_ip_list.append(host['management_ip'])
        fed_ip_list.append(host['federation_ip'])
        stor_ip_list.append(host['storage_ip'])

        mgmt_ip_mtu.append(host['management_mtu'])
        fed_ip_mtu.append(host['federation_mtu'])
        stor_ip_mtu.append(host['storage_mtu'])

        vc_ip_list.append(host['hypervisor_management_system'])

        freeSpace = getNodeCapacity(svt.GetHostCapacity(
            host['name'])['metrics'])['free_space']
        space_list.append(str(freeSpace) + " GB")
        space_list_int.append(freeSpace)
        map[host['id']] = [host['name']]
        map[host['id']].append(host['version'])
        map[host['id']].append(host['state'])
        if host['state'] != "ALIVE":
           federation_health  = False
        if freeSpace < 100:
            logwriter(log, "Hostname : " +
                      host['name'] + " free space : " + str(freeSpace) + " GB")
            logwriter(log, "Inufficient space for the upgrade")
        elif freeSpace >= 100:
            logwriter(log, "Hostname : " +
                      host['name'] + " free space : " + str(freeSpace) + " GB")
            logwriter(log, "Sufficient space for the upgrade")

    # host_hardware_health = True
    
    host_name_list = []
    host_status_list = []
    raid_card_name_list = []
    raid_card_firmware_list = []
    raid_card_status_list = []
    battery_manufacturer_list = [] #manufacturer changed to percent charged
    battery_health_list = []
    accelerator_card_firmware_list = []
    accelerator_card_health_list = []
    ld_name_list = []
    ld_health = []
    cache_health_list = []
    for host in host_hardware_list:
       host_name_list.append(host['host']['name'])
       host_status_list.append(host['host']['status'])
       raid_card_name_list.append(host['host']['raid_card']['product_name'])
       raid_card_firmware_list.append(host['host']['raid_card']['firmware_revision'])
       raid_card_status_list.append(host['host']['raid_card']['status'])
       battery_manufacturer_list.append(host['host']['battery']['percent_charged']) #manufacturer changed to percent charged
       battery_health_list.append(host['host']['battery']['health'])
       accelerator_card_firmware_list.append(host['host']['accelerator_card']['firmware_revision'])
       accelerator_card_health_list.append(host['host']['accelerator_card']['status'])
       for ld in (host['host']['logical_drives']):
          ld_name_list.append(ld['name'])
          ld_health.append(ld['status'])
          cache_health_list.append(ld['health'])

    clusters = svt.GetCluster()['omnistack_clusters']

    for cluster in clusters:
        arbiter_ip = cluster['arbiter_address'] # stores only last evaluated cluster arbiter IP
        logwriter(log, "Evaluating cluster " +
                  cluster['hypervisor_object_parent_name'])
        logwriter(log, "Evaluating cluster members")
        if cluster['arbiter_connected']:
            arbiter_connected = "CONNECTED"
        if not cluster['arbiter_connected']:
            federation_health = False
            arbiter_connected = "DISCONNECTED"
        for member in cluster['members']:
            logwriter(log, "Node " + map[member][0] +
                      " software version : " + map[member][1])
            logwriter(log, "Node " + map[member]
                      [0] + " status : " + map[member][2])
            logwriter(log, "Node " + map[member][0] +
                      " arbiter connectivity : " + arbiter_connected)
        logwriter(log, "Arbiter IP address : " + arbiter_ip)
        logwriter(log, "vCenter : " + cluster['hypervisor_management_system'])

    vms = svt.GetVM()['virtual_machines']

    for vm in vms:
        if vm['state'] == 'ALIVE':
            logwriter(log, "Evaluating VM " + vm['name'])
            vm_id = vm['id']
            vmha = svt.GetVMbyID(vm_id)['virtual_machine']['ha_status']
            if vmha == 'SAFE':
                logwriter(
                    log, "VM storage high availability is safe for VM" + vm['name'])
            else:
                logwriter(log, "VM storage high availability is not safe for VM" +
                          vm['name'] + ". VM could go offline. Do not proceed.")

    logclose(log)

    report = open('report.html', 'w')

    html_template = r"""
<!doctype html>
<html lang="en">

   <head>
      <!-- Required meta tags -->
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
      <!-- Bootstrap CSS -->
      <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css" integrity="sha384-9aIt2nRpC12Uk9gS9baDl411NQApFmC26EwAOH8WgZl5MYYxFfc+NcPb1dKGj7Sk" crossorigin="anonymous">
      <title>Simplivity Pre-Upgrage Checklist Report</title>
   </head>

   <body>
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
         
         <a class="navbar-brand" href="#"><img classs="img-responsive" width="50px" height="" src="C:\Users\patenikh\Downloads\6.1-Ruby-Python\pythoncode\hpe.JPG">&nbsp; HPE Simplivity</a>
         
         <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
         <span class="navbar-toggler-icon"></span>
         </button>
         
         <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav mr-auto">
            </ul>
            
            <form class="form-inline my-2 my-lg-0">
               <ul class="navbar-nav mr-auto">
                  <li class="nav-item active">
                     <a class="nav-link">Date: 23.07.2021 <span class="sr-only">(current)</span></a>
                  </li>
               </ul>
            </form>
         </div>
      
      </nav>
      <div class="message" id="message"></div>
      <div class="container my-3">
         <h2>
            <center>
            Simplivity Pre-Upgrade Check List
         </h2>
         <hr>
         <h4>
            <center>
            Summary Report
         </h4>
         <div class="table">
            <table class="table table-sm">
               <thead>
                  <tr>
                     <th scope="col">Checklist</th>
                     <th scope="col">Status</th>
                  </tr>
               </thead>
               <tbody id="tablebody">
                  <tr>
                     <td>
                        <b>Space usage on Individual nodes</b>
                        <table class="table mb-0">
                           <thead>
                              <tr>
                                 <td> &nbsp; Hostname-1</td>
                                 <td>{{ hostname_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Free space</td>
                                 <td>{{ freespace_1 }} GB</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-2</td>
                                 <td>{{ hostname_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Free space</td>
                                 <td>{{ freespace_2 }} GB</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-3</td>
                                 <td>{{ hostname_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Free space</td>
                                 <td>{{ freespace_3 }} GB</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-4</td>
                                 <td>{{ hostname_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Free space</td>
                                 <td>{{ freespace_4 }} GB</td>
                              </tr>
                           </thead>
                        </table>
                     </td>
                     {% if freespace_1 >= 100 and freespace_2 >= 100 and freespace_3 >= 100 and freespace_4 >= 100 %}
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                     {% else %}
                     <td><button type="button" class="btn btn-danger btn-sm"><b>FAILED</button></td>
                     {% endif %}
                  </tr>
                  <tr>
                     <td><b>Federation health<b></td>
                     {{ federation_health }}
                     {% if federation_health %}
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                     {% else %}
                     <td><button type="button" class="btn btn-danger btn-sm"><b>FAILED</button></td>
                     {% endif %}
                  </tr>
                  <tr>
                     <td><b>Storage High Availability<b></td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td>
                     <b>IP captures</b>
                        <table class="table mb-0">
                           <thead>
                              <tr>
                                 <td> &nbsp; Arbiter</td>
                                 <td>{{ arbiter_ip }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-1</td>
                                 <td>{{ hostname_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; vCenter IP</td>
                                 <td>{{ vc_ip_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Management IP</td>
                                 <td>{{ mgmt_ip_1 }}</td>
                                 <td>{{ mgmt_ip_mtu_1 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Storage IP</td>
                                 <td>{{ stor_ip_1 }}</td>
                                 <td>{{ stor_ip_mtu_1 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Federation IP</td>
                                 <td>{{ fed_ip_1 }}</td>
                                 <td>{{ fed_ip_mtu_1 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-2</td>
                                 <td>{{ hostname_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; vCenter IP</td>
                                 <td>{{ vc_ip_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Management IP</td>
                                 <td>{{ mgmt_ip_2 }}</td>
                                 <td>{{ mgmt_ip_mtu_2 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Storage IP</td>
                                 <td>{{ stor_ip_2 }}</td>
                                 <td>{{ stor_ip_mtu_2 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Federation IP</td>
                                 <td>{{ fed_ip_2 }}</td>
                                 <td>{{ fed_ip_mtu_2 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-3</td>
                                 <td>{{ hostname_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; vCenter IP</td>
                                 <td>{{ vc_ip_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Management IP</td>
                                 <td>{{ mgmt_ip_3 }}</td>
                                 <td>{{ mgmt_ip_mtu_3 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Storage IP</td>
                                 <td>{{ stor_ip_3 }}</td>
                                 <td>{{ stor_ip_mtu_3 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Federation IP</td>
                                 <td>{{ fed_ip_3 }}</td>
                                 <td>{{ fed_ip_mtu_3 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-4</td>
                                 <td>{{ hostname_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; vCenter IP</td>
                                 <td>{{ vc_ip_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Management IP</td>
                                 <td>{{ mgmt_ip_4 }}</td>
                                 <td>{{ mgmt_ip_mtu_4 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Storage IP</td>
                                 <td>{{ stor_ip_4 }}</td>
                                 <td>{{ stor_ip_mtu_4 }} mtu</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Federation IP</td>
                                 <td>{{ fed_ip_4 }}</td>
                                 <td>{{ fed_ip_mtu_4 }} mtu</td>
                              </tr>
                           </thead>
                        </table>
                     </td>
                  </tr>
                  <tr>
                     <td><b>OVC Version</b></td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td>{{ ovc_version }}</td>
                  </tr>
                  <tr>
                     <td>
                        <b>Hardware status</b>
                        <table class="table mb-0">
                           <thead>



                              <tr>
                                 <td> &nbsp; <b>Hostname<b></td>
                                 <td><b>{{ hostname_1 }}<b></td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Host Status</td>
                                 <td>{{ host_status_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card name</td>
                                 <td>{{ raid_card_name_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card firmware</td>
                                 <td>{{ raid_card_fw_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card status</td>
                                 <td>{{ raid_card_status_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Percent</td>
                                 <td>{{ battery_manufacturer_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Health</td>
                                 <td>{{ battery_health_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card firmware</td>
                                 <td>{{ acc_fw_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card status</td>
                                 <td>{{ acc_st_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical drive name</td>
                                 <td>{{ ld_name_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical health</td>
                                 <td>{{ ld_health_1 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Cache health</td>
                                 <td>{{ cache_health_1 }}</td>
                              </tr>



                              <tr>
                                 <td> &nbsp; <b>Hostname<b></td>
                                 <td><b>{{ hostname_1 }}<b></td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Host Status</td>
                                 <td>{{ host_status_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card name</td>
                                 <td>{{ raid_card_name_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card firmware</td>
                                 <td>{{ raid_card_fw_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card status</td>
                                 <td>{{ raid_card_status_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Percent</td>
                                 <td>{{ battery_manufacturer_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Health</td>
                                 <td>{{ battery_health_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card firmware</td>
                                 <td>{{ acc_fw_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card status</td>
                                 <td>{{ acc_st_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical drive name</td>
                                 <td>{{ ld_name_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical health</td>
                                 <td>{{ ld_health_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Cache health</td>
                                 <td>{{ cache_health_2 }}</td>
                              </tr>





                              <tr>
                                 <td> &nbsp; <b>Hostname<b></td>
                                 <td><b>{{ hostname_3 }}<b></td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Host Status</td>
                                 <td>{{ host_status_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card name</td>
                                 <td>{{ raid_card_name_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card firmware</td>
                                 <td>{{ raid_card_fw_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card status</td>
                                 <td>{{ raid_card_status_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Percent</td>
                                 <td>{{ battery_manufacturer_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Health</td>
                                 <td>{{ battery_health_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card firmware</td>
                                 <td>{{ acc_fw_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card status</td>
                                 <td>{{ acc_st_3 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical drive name</td>
                                 <td>{{ ld_name_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical health</td>
                                 <td>{{ ld_health_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Cache health</td>
                                 <td>{{ cache_health_2 }}</td>
                              </tr>






                              <tr>
                                 <td> &nbsp; <b>Hostname<b></td>
                                 <td><b>{{ hostname_4 }}<b></td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Host Status</td>
                                 <td>{{ host_status_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card name</td>
                                 <td>{{ raid_card_name_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card firmware</td>
                                 <td>{{ raid_card_fw_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; RAID card status</td>
                                 <td>{{ raid_card_status_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Percent</td>
                                 <td>{{ battery_manufacturer_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Battery Health</td>
                                 <td>{{ battery_health_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card firmware</td>
                                 <td>{{ acc_fw_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Accelerator card status</td>
                                 <td>{{ acc_st_4 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical drive name</td>
                                 <td>{{ ld_name_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Logical health</td>
                                 <td>{{ ld_health_2 }}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Cache health</td>
                                 <td>{{ cache_health_2 }}</td>
                              </tr>


                           </thead>
                        </table>
                     </td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
               </tbody>
            </table>
         </div>
      </div>
      <!-- Optional JavaScript -->
      <!-- jQuery first, then Popper.js, then Bootstrap JS -->
      <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
      <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
      <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js" integrity="sha384-OgVRvuATP1z7JjHLkuOU7Xw704+h835Lr+6QL9UvYjZE3Ipu6Tp75j7Bh/kR0JKI" crossorigin="anonymous"></script>
      <script type="text/javascript" src="app.js"></script>
   </body>
</html>"""

    data = {
        "arbiter_ip" : arbiter_ip,
        "hostname_1": host_list[0],
        "freespace_1": space_list_int[0],
        "hostname_2": host_list[1],
        "freespace_2": space_list_int[1],
        "hostname_3": host_list[2],
        "freespace_3": space_list_int[2],
        "hostname_4": host_list[3],
        "freespace_4": space_list_int[3],
        "federation_health": federation_health,
        "hostname_1": host_list[0],
        "vc_ip_1" : vc_ip_list[0],
        "mgmt_ip_1" : mgmt_ip_list[0],
        "mgmt_ip_mtu_1" : mgmt_ip_mtu[0],
        "stor_ip_1" : stor_ip_list[0],
        "stor_ip_mtu_1" : stor_ip_mtu[0],
        "fed_ip_1" : fed_ip_list[0],
        "fed_ip_mtu_1" : fed_ip_mtu[0],
        "hostname_2": host_list[1],
        "vc_ip_2" : vc_ip_list[1],
        "mgmt_ip_2" : mgmt_ip_list[1],
        "mgmt_ip_mtu_2" : mgmt_ip_mtu[1],
        "stor_ip_2" : stor_ip_list[1],
        "stor_ip_mtu_2" : stor_ip_mtu[1],
        "fed_ip_2" : fed_ip_list[1],
        "fed_ip_mtu_2" : fed_ip_mtu[1],
        "hostname_3": host_list[2],
        "vc_ip_3" : vc_ip_list[2],
        "mgmt_ip_3" : mgmt_ip_list[2],
        "mgmt_ip_mtu_3" : mgmt_ip_mtu[2],
        "stor_ip_3" : stor_ip_list[2],
        "stor_ip_mtu_3" : stor_ip_mtu[2],
        "fed_ip_3" : fed_ip_list[2],
        "fed_ip_mtu_3" : fed_ip_mtu[2],
        "hostname_4": host_list[3],
        "vc_ip_4" : vc_ip_list[3],
        "mgmt_ip_4" : mgmt_ip_list[3],
        "mgmt_ip_mtu_4" : mgmt_ip_mtu[3],
        "stor_ip_4" : stor_ip_list[3],
        "stor_ip_mtu_4" : stor_ip_mtu[3],
        "fed_ip_4" : fed_ip_list[3],
        "fed_ip_mtu_4" : fed_ip_mtu[3],
        "ovc_version" : host_version,


        "hostname_1" : host_name_list[0],
        "host_status_1" : host_status_list[0],
        "raid_card_name_1" : raid_card_name_list[0],
        "raid_card_fw_1" : raid_card_firmware_list[0],
        "raid_card_status_1" : raid_card_status_list[0],
        "battery_manufacturer_1" : battery_manufacturer_list[0],
        "battery_health_1" : battery_health_list[0],
        "acc_fw_1" : accelerator_card_firmware_list[0],
        "acc_st_1" : accelerator_card_health_list[0],
        "ld_name_1" : ld_name_list[0],
        "ld_health_1" : ld_health[0],
        "cache_health_1" : cache_health_list[0],

        "hostname_2" : host_name_list[1],
        "host_status_2" : host_status_list[1],
        "raid_card_name_2" : raid_card_name_list[1],
        "raid_card_fw_2" : raid_card_firmware_list[1],
        "raid_card_status_2" : raid_card_status_list[1],
        "battery_manufacturer_2" : battery_manufacturer_list[1],
        "battery_health_2" : battery_health_list[1],
        "acc_fw_2" : accelerator_card_firmware_list[1],
        "acc_st_2" : accelerator_card_health_list[1],
        "ld_name_2" : ld_name_list[1],
        "ld_health_2" : ld_health[1],
        "cache_health_2" : cache_health_list[1],

        "hostname_3" : host_name_list[2],
        "host_status_3" : host_status_list[2],
        "raid_card_name_3" : raid_card_name_list[2],
        "raid_card_fw_3" : raid_card_firmware_list[2],
        "raid_card_status_3" : raid_card_status_list[2],
        "battery_manufacturer_3" : battery_manufacturer_list[2],
        "battery_health_3" : battery_health_list[2],
        "acc_fw_3" : accelerator_card_firmware_list[2],
        "acc_st_3" : accelerator_card_health_list[2],
        "ld_name_3" : ld_name_list[2],
        "ld_health_3" : ld_health[2],
        "cache_health_3" : cache_health_list[2],

        "hostname_4" : host_name_list[3],
        "host_status_4" : host_status_list[3],
        "raid_card_name_4" : raid_card_name_list[3],
        "raid_card_fw_4" : raid_card_firmware_list[3],
        "raid_card_status_4" : raid_card_status_list[3],
        "battery_manufacturer_4" : battery_manufacturer_list[3],
        "battery_health_4" : battery_health_list[3],
        "acc_fw_4" : accelerator_card_firmware_list[3],
        "acc_st_4" : accelerator_card_health_list[3],
        "ld_name_4" : ld_name_list[3],
        "ld_health_4" : ld_health[3],
        "cache_health_4" : cache_health_list[3],
    }

    j2_template = Template(html_template)

    report.write(j2_template.render(data))
    report.close()    


    # if ready:
    #    for host in hosts:
    #        svt.ShutdownOVC(host['id'])

    # Add logic to pick a particular host and power it off
    # Add logic to move check if OVC shutdown has completed & then let the user know
    # Add logic to then move the ESXi host into maintenance mode
    # DRS enabled in cluster?



    # To do
    # Pass or fail VM Storage High availability health
    # Pass OVC version test if all OVC versions match
    # Pass hardware status if all health and status items are green/healthy
    # IP captures is not a test
    # Final logic to pass or fail setup for upgrade
