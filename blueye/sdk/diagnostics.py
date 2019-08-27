import json
import urllib
import urllib.error
import urllib.request
import json
import http.client


def get_diagnostic_data(ip, name, port=80, post_data=None, method=None):
    data = get_website_json("http://%s:%d/diagnostics/%s" %
                            (ip, port, name), post_data, method=method)
    return data


def get_website_json(url, post_data=None, method=None):
    retries = 0
    while retries < 3:
        data_json = get_website(url, post_data, method=method)
        if data_json is not None:
            break
        retries += 1
        print("No data, retriying")
    if data_json is None:
        return None
    try:
        data = json.loads(data_json)
    except json.decoder.JSONDecodeError:
        print("Could not decode json")
        return None
    return data


def get_website(url, post_data=None, method=None, decode_utf8=True):
    try:
        if method is not None:
            url = urllib.request.Request(url, method=method)
        if post_data is not None:
            post_data = urllib.parse.urlencode(post_data).encode('utf-8')
            data = urllib.request.urlopen(url, post_data).read()
        else:
            data = urllib.request.urlopen(url).read()
        if decode_utf8:
            data = data.decode("utf-8")
    except ConnectionRefusedError:
        print("Could not connect to server")
        return None
    except urllib.error.URLError:
        print("Could not connect to server")
        return None
    except http.client.RemoteDisconnected:
        print("RemoteDisconnect")
        return None
    return data
