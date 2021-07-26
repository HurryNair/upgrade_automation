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

    clusters = svt.GetCluster()['omnistack_clusters']

    for cluster in clusters:
        logwriter(log, "Evaluating cluster " + cluster['hypervisor_object_parent_name'])
        logwriter(log, "Evaluating cluster members")
        if cluster['arbiter_connected']:
            arbiter_connected = "CONNECTED"
        if not cluster['arbiter_connected']:
            arbiter_connected = "DISCONNECTED"
        for member in cluster['members']:
            hosts = svt.GetHost()['hosts']
            for host in hosts:
                if host['id'] == member:
                    logwriter(log, "Node " + host['name'] + " software version : " + host['version'])
                    logwriter(log, "Node " + host['name'] + " status : " + host['state'])
                    logwriter(log, "Node " + host['name'] + " arbiter connectivity : " + arbiter_connected)

        logwriter(log, "Arbiter IP address : " + cluster['arbiter_address'])
        logwriter(log, "vCenter : " + cluster['hypervisor_management_system'])

    hosts = svt.GetHost()['hosts']
    host_list = []
    space_list = []

    for host in hosts:
        logwriter(log, "Evaluating host " + host['name'])
        host_list.append(host)
        freeSpace = getNodeCapacity(svt.GetHostCapacity(host['name'])['metrics'])['free_space']
        space_list.append(str(freeSpace) + " GB")
        if freeSpace < 100:
            logwriter(log, "Hostname : " + host['name'] + " free space : " + str(freeSpace) + " GB")
            logwriter(log, "Inufficient space for the upgrade")
        elif freeSpace >= 100:
            logwriter(log, "Hostname : " + host['name'] + " free space : " + str(freeSpace) + " GB")
            logwriter(log, "Sufficient space for the upgrade")
            
    vms = svt.GetVM()['virtual_machines']
    
    for vm in vms:
        if vm['state'] == 'ALIVE':
            logwriter(log, "Evaluating VM " + vm['name'])
            vm_id = vm['id']
            vmha = svt.GetVMbyID(vm_id)['virtual_machine']['ha_status']
            if vmha == 'SAFE' and vm['ha_resynchronization_progress'] == 100 and len(vm['replica_set'] == 2):
                logwriter(log, "VM storage high availability is safe for VM" + vm['name'])
            else:
                logwriter(log, "VM storage high availability is not safe for VM" + vm['name'] + ". VM could go offline. Do not proceed.")
                    
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
                                 <td>{}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Free space</td>
                                 <td>{}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Hostname-2</td>
                                 <td>{}</td>
                              </tr>
                              <tr>
                                 <td> &nbsp; Free space</td>
                                 <td>{}</td>
                              </tr>
                           </thead>
                        </table>
                     </td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td><b>Federation status & IP captures</b></td>
                     <td><button type="button" class="btn btn-danger btn-sm"><b>FAILED</button></td>
                  </tr>
                  <tr>
                     <td><b>ESXi Version</b></td>
                     <td><button type="button" class="btn btn-danger btn-sm"><b>FAILED</button></td>
                  </tr>
                  <tr>
                     <td><b>OVC Version</b></td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td>
                        <b>VCenter configuration & IP address</b>
                        <table class="table mb-0">
                           <thead>
                              <tr>
                                 <td> &nbsp; vCenter IP</td>
                                 <td>10.54.110.150</td>
                              </tr>
                           </thead>
                        </table>
                     </td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td>
                        <b>Arbiter IP configuration</b>
                        <table class="table mb-0">
                           <thead>
                              <tr>
                                 <td> &nbsp; IP Address</td>
                                 <td>10.54.110.220 </td>
                              </tr>
                           </thead>
                        </table>
                     </td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td><b>Vswitch Configuration</b></td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td><b>Plugin Status</b></td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td><b>Local and Remote Backup Status</b></td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td><b>Complete Physical Network topology</b></td>
                     <td><button type="button" class="btn btn-danger btn-sm"><b>FAILED</button></td>
                  </tr>
                  <tr>
                     <td><b>Hardware status</b></td>
                     <td><button type="button" class="btn btn-success btn-sm"><b>PASSED</button></td>
                  </tr>
                  <tr>
                     <td><b>ILO Information/Access</b></td>
                     <td><button type="button" class="btn btn-danger btn-sm"><b>FAILED</button></td>
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
</html>""".format(host_list[0], space_list[0], host_list[1], space_list[1])
    report.write(html_template)
    report.close()
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