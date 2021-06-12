import requests
import zipfile
import os
from pathlib import Path, PurePath
import shutil
from collections import defaultdict
import numpy as np
import pandas as pd
import re
import plotly.express as px
from traitlets.config import Config
from nbconvert import HTMLExporter
from urllib.request import urlopen
import nbformat


def convertPGNtoDF(path):
    """"""
    with open(path, 'r') as file:
        data_from_pgn = file.read()

    dct = defaultdict(list)

    moves = False
    for element in data_from_pgn.split("\n\n"):
        tags=['Event', 'Site', 'Date', 'Round', 'White', 'Black', 'Result', 'WhiteElo', 'BlackElo', 'ECO']
        if moves:
            dct["moves"].append(element)
            moves = False

        else:
            for t in re.findall("\[.*\]", element):
                tag = t[1:-1].split('"')[0][:-1]
                val = t[1:-1].split('"')[1]
                dct[tag].append(val)
                tags.remove(tag)

            for t in tags:
                dct[t].append(np.nan)
                #print("nan for ", tag)
            moves = True

    return pd.DataFrame(dct)

def getECOdesc(eco):
    try:
        return ecoDct[eco][0]
    except:
        return np.nan

def getGraph(lastname, top = 30, directory_to_extract_to = 'downloads'):
    """
    """
    #print('Downloading ZIP with PGNs of '+lastname)
    zipFileUrl = "https://www.pgnmentor.com/players/"+lastname+".zip"
    zipFile = requests.get(zipFileUrl)

    if not os.path.exists(directory_to_extract_to):
        os.makedirs(directory_to_extract_to)
    else:
        shutil.rmtree(directory_to_extract_to)           # Removes all the subdirectories!
        os.makedirs(directory_to_extract_to)

    path_to_zip_file = "downloads/"+lastname+'.zip'

    #print("Download successful")
    with open(os.fspath(PurePath(path_to_zip_file)), 'wb') as f:
        f.write(zipFile.content)

    zip_ref = zipfile.ZipFile(os.fspath(PurePath(path_to_zip_file)), 'r')
    zip_ref.extractall(os.fspath(PurePath(directory_to_extract_to)))
    zip_ref.close()

    rawDf = convertPGNtoDF(directory_to_extract_to+'/'+lastname+'.pgn')

    df = rawDf.groupby("ECO").count().sort_values(by="Event", ascending=False).head(top)
    df.reset_index(inplace=True)
    df.drop(df.iloc[:, 2:], axis = 1, inplace = True)
    df.columns=["ECO","Frequency"]

    dr = requests.get("http://www.neerpeltersk.be/palview4/p4sets/P3eco.txt")
    path_to_Eco = 'static/eco.txt'

    with open(path_to_Eco, 'wb') as f:
        f.write(dr.content)

    with open(path_to_Eco, 'r') as file:
        data_from_eco = file.read()

    ecoDct = defaultdict(list)
    for row in data_from_eco.split("\n\n")[4:]:
        code = row[:3]
        desc = row[3:].lstrip()
        ecoDct[code].append(desc)

    df["desc"]=df["ECO"].map(getECOdesc)
    df["perc"]=df["Frequency"]/len(rawDf)
    fig = px.bar(df, x='ECO', y='Frequency',
             hover_data=['desc','perc'],
             height=400,
             title = "Top-"+str(top)+" openings of "+lastname,
             labels={'ECO':'ECO (opening code)',
                     'Frequency':'Frequency',
                    'perc':'Ratio'},
             color='Frequency',
             color_continuous_scale="rdbu_r"
            )
    fig.write_html("static/graph.html")
