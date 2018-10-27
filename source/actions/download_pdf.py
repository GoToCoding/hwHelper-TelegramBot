import urllib.request


def download_file(download_url, filename):
    urllib.request.urlretrieve(download_url, '/home/ruzal/Workspace/projects/pythonProj1/homeWorkHelperBot'
                                             '/homeWorkHelperBot/files/' + filename)
    return 'OK'
