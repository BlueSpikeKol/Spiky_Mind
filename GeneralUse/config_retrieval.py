import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def get_openai_key():
    return config['openai']['api_key']


def get_mysql_config():
    mysql_config = {}
    mysql_section = config['mysql']
    for key in mysql_section:
        mysql_config[key] = mysql_section[key]
    return mysql_config


def get_pinecone_config():
    pinecone_config = {}
    pinecone_section = config['pinecone']
    for key in pinecone_section:
        pinecone_config[key] = pinecone_section[key]
    return pinecone_config
