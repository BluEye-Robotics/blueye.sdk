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

## Understanding the file name formats
An example output from listing available files could be.

``` shell
'video_BYEDP000105_2019-08-13_103035.jpg'
'video_BYEDP000105_2019-08-13_103035.mp4'
'picture_BYEDP000105_2019-09-27_074152.431.jpg',
```
The format of the file names are described below.

### Video files
For each video recorded on the drone two files will be created, a `.mp4` file with the actual video, and
a `.jpg` file with a thumbnail image from the video file. Other then the file extension the file names will be identical.
An example of a video + thumbnail pair could be:
``` shell
'video_BYEDP000105_2019-08-13_103035.jpg'
'video_BYEDP000105_2019-08-13_103035.mp4'
```
The file names break down to:


| File Type Prefix | Drone Serial Number | Timestamp( yyyy-MM-dd_hhmmss) | File Extension |
| -------------    | :-------------:     | -----:                        | -----:         |
| video            | BYEDP000105         | 2019-08-13_103035             | .mp4           |
| video            | BYEDP000105         | 2019-08-13_103035             | .jpg           |


### Image files
Image files are images captured with the still image function. The file name for image files follow the same format
as the video files, but the time stamp is extended with milliseconds to differentiate still images captured within
the same second.

An example still image file could be:

``` shell
'picture_BYEDP000105_2019-09-27_074152.431.jpg',
```
The file name breaks down to:

| File Type Prefix | Drone Serial Number | Timestamp( yyyy-MM-dd_hhmmss.SSS) | File Extension |
| -------------    | :-------------:     | -----:                            | -----:         |
| picture          | BYEDP000105         | 2019-09-27_074152.431             | .jpg           |
