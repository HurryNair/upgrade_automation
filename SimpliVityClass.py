import requests
import datetime

DEBUG = False

class Simplivity:

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





