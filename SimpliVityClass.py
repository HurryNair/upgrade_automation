import requests
import datetime

DEBUG = False

class SimpliVity:

    def __init__(self, url):
        self.url = url
        self.access_token = ''
        self.headers = {}
        self.jsonversion = "application/vnd.simplivity.v1.9+json"
        requests.urllib3.disable_warnings()

    def doGet(self, url):
        response = requests.get(url, verify = False, headers = self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            pass # Implement svterror class & raise an svterror here

    def doPost(self, url, body=None):
        if body:
            headers = self.headers
            headers['Content-Type'] = "application/vnd.simplivity.v1.9+json"
            response = requests.post(url, data = body, verify = False, headers = headers)
        else:
            response = requests.post(url, verify = False, headers = self.headers)
            if ((response.status_code == 200) or (response.status_code == 201) or (response.status_code == 202)):
                return response.json()
            else:
              pass # Implement svterror class & raise an svterror here  

    def doDelete(self, url):
        response = requests.delete(url, verify = False, headers = self.headers)
        if ((response.status_code == 200) or (response.status_code == 201) or (response.status_code == 202)):
            return response.json()
        else:
            pass # Implement svterror class & raise an svterror here
    
    def Connect(self, hms_username, hms_password):
        response = requests.post(self.url+'oauth/token', auth=('simplivity', ''), verify=False, data={
            'grant_type': 'password',
            'username': hms_username,
            'password': hms_password})
        if(response.status_code == 200):
            self.access_token = response.json['access_token']
            self.headers = {'Authorization': 'Bearer ' + self.access_token,
                            'Accept': self.jsonversion}
            return response
        else:
            pass # Implement svterror class & raise an svterror here
        pass

    def GetHost(self, name=None):
        if name:
            url = self.url+'hosts?show_optional_fields=true&name='+name
        else:
            url = self.url+'hosts'
        return self.doGet(url) #use state in this return item to check if host is powered on

    def GetHostId(self, name=None):
        for x in self.GetHost(name)['hosts']:
            if x['state'] == 'ALIVE':
                return x['id']
        
    def GetHostCapacity(self, name, timerange='43200', resolution='Minute', timeOffset='0'):
        url = self.url + 'hosts/' + self.GetHostId(name) + '/capacity?range=' + timerange + \
            '&resolution=' + '&offset=' + timeOffset + '&show_optional_fields=true'
        return self.doGet(url)

    def GetVM(self, vmname=None):
        if vmname:
            url = self.url+'virtual_machines?show_optional_fields=true&name='+vmname
        else:
            url = self.url+'virtual_machines?show_optional_field=true'
        return self.doGet(url)

    def GetVMHA(self):
        vms = self.GetVM()['virtual_machines']
        for vm in vms:
            if vm['state'] == 'ALIVE':
                if vm['ha_status'] == 'SAFE' and vm['ha_resynchronization_progress'] == 100 and len(vm['replica_set'] == 2):
                    return True
                else:
                    return False

    def ShutdownOVC(self, host_id, ha_wait=True):
        return self.doPost(self.url+'hosts/'+host_id+'/shutdown_virtual_controller')

    def CancelShutdownOVC(self, host_id):
        return self.doPost(self.url+'hosts/'+host_id+'/cancel_virtual_controller_shutdown')

    def GetOVCShutdownStatus(self, host_id):
        return self.doGet(self.url+'hosts/'+host_id+'/virtual_controller_shutdown_status')





