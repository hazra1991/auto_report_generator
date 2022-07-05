import os
from configparser import ConfigParser


def foldersearch(val,f_path,root='root'):
    for i in os.listdir(f_path):
        if os.path.isfile(f_path/i):
            val[i] = str(f_path/i)
        else:
            val[i] = {}
            foldersearch(val[i],f_path/i,root=i)


def createFolderLayout(folder_path):
    result_dict = {}
    foldersearch(result_dict,folder_path)
    return result_dict


def getConfig(filename_path='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename_path)

    # get section, default to postgresql
    conf = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            conf[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename_path))

    return conf