# Downloading videos and images
Videos and images can easiest be downloaded through the mobile app, or by using the
[`Blueye file transfer`](https://www.blueyerobotics.com/Software/FileTransfer) desktop application
for Windows, Mac OS and Linux.

If one wants a more control over the download process, all files are listable through any client
that supports [WebDAV](https://en.wikipedia.org/wiki/WebDAV). The server is available on the drone
(default ip: `192.168.1.101`) and port `5050`.

For example using a
[Python WebDAV client](https://github.com/CloudPolis/webdav-client-python) we could do the following
to list the files on drone:

```python
import webdav3.client as wc

# Define the options for connecting
options = {
    'webdav_hostname': "http://192.168.1.101:5050"
}

# Instantiate the connection
client = wc.Client(options)

# List the avaiable files
client.list()
```
