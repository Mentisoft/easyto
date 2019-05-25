##import logging
##import os
##import cloudstorage as gcs
##import webapp2
##
##from google.appengine.api import app_identity
##
##def get(self):
##  bucket_name = os.environ.get('BUCKET_NAME',
##                               app_identity.get_default_gcs_bucket_name())
##
##  self.response.headers['Content-Type'] = 'text/plain'
##  self.response.write('Demo GCS Application running from Version: '
##                      + os.environ['CURRENT_VERSION_ID'] + '\n')
##  self.response.write('Using bucket name: ' + bucket_name + '\n\n')
##
##def read_file(self, filename):
##  self.response.write('Reading the full file contents:\n')
##
##  gcs_file = gcs.open(filename)
##  contents = gcs_file.read()
##  gcs_file.close()
##  self.response.write(contents)

##from google.cloud import storage
### create storage client
##storage_client = storage.Client.from_service_account_json('/Users/ey/testpk.json')
### get bucket with name
##bucket = storage_client.get_bucket('testdatabucket00123')
### get bucket data as blob
##blob = bucket.get_blob('testdata.xml')
### convert to string
##json_data = blob.download_as_string()

##import pickle
##from gcloud import storage
##from oauth2client.service_account import ServiceAccountCredentials
##import os
##
##creds = pickle.load(token)
##
####credentials_dict = {
####    'type': 'service_account',
####    'client_id': os.environ['BACKUP_CLIENT_ID'],
####    'client_email': os.environ['BACKUP_CLIENT_EMAIL'],
####    'private_key_id': os.environ['BACKUP_PRIVATE_KEY_ID'],
####    'private_key': os.environ['BACKUP_PRIVATE_KEY'],
####}
####credentials = ServiceAccountCredentials.from_json_keyfile_dict(
####    credentials_dict
####)
##client = storage.Client(credentials=creds, project='myproject')
##bucket = client.get_bucket('mybucket')
##blob = bucket.blob('myfile')
##blob.upload_from_filename('myfile')



from gcloud import storage

# Explicitly use service account credentials by specifying the private key
# file.
client = storage.Client.from_service_account_json(
    'EasyTO-3820332f5fba.json')

# Make an authenticated API request
buckets = list(client.list_buckets())
print(buckets)

bucket = client.get_bucket('easy-to-reester-tz')
print(bucket)


blob = storage.Blob('tz_opendata_z01012018_po01012019.csv', bucket)
content = blob.download_as_string(start=1, end=100)

for row in content:
    print (row)



blob = bucket.get_blob('temp_files_folder/test.txt')
##print(blob.download_as_string())

##f = open('gs://python_test_hm/train.csv' , 'rb')












