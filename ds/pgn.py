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
from bs4 import BeautifulSoup
import requests
import re


def convertPGNtoDF(path):
    """"""
    try:
        with open(path, 'r') as file:
            data_from_pgn = file.read()
    except:
        with open(path, 'r', encoding='windows-1252') as file:
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
    #filtering only ECO
    dct = {key: dct[key] for key in ["ECO", "Event"] }
    return pd.DataFrame(dct)

def getECOdesc(eco):
    try:
        ecoDf = pd.read_html('https://www.chessgames.com/chessecohelp.html')
        ecoDf=ecoDf[0]
        ecoDf.columns = ['ECO','desc']
        return ecoDf[ecoDf['ECO']==eco]['desc'].values[0]
    except:
        return np.nan

def getEcoDescription(eco, ecoUrl = 'https://www.chessgames.com/chessecohelp.html'):
    """
    The function returns a description of an opening based on its ECO code

    Input:
    eco (str): ECO code, e.g. 'A08'
    ecoUrl(str): source of the table with descriptions,
                 default: 'https://www.chessgames.com/chessecohelp.html'

    Output (str): string with a description or 'Description was not found' in case of abscence
    """

    pathToEco = './pgn/downloads/eco.pkl'
    if os.path.isfile(pathToEco):
        ecoDf = pd.read_pickle(pathToEco)
    else:
        ecoDf = pd.read_html(ecoUrl)[0]
        ecoDf.to_pickle(pathToEco)
    try:
        result = ecoDf[ecoDf[0]==eco].iloc[0][1]
    except:
        result = 'Description was not found'
    return result


def playerExists(playerName, url="https://www.pgnmentor.com/files.html"):
    session = requests.session()
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    lst = []
    for element in soup.find_all('a', href=re.compile('^players')):
        el = element['href'].split('/')[1]
        if '.zip' not in el:
            lst.append(el.lower())
    return playerName.lower() in set(lst)

def getGraph(lastname, top = 30, directory_to_extract_to = 'pgn/downloads'):
    """
    """
    if len(lastname)>1:
        lastname=lastname[0].upper()+lastname[1:].lower()

    if playerExists(lastname):
        #print('Downloading ZIP with PGNs of '+lastname)
        zipFileUrl = "https://www.pgnmentor.com/players/"+lastname+".zip"
        zipFile = requests.get(zipFileUrl)

        if not os.path.exists(directory_to_extract_to):
            os.makedirs(directory_to_extract_to)
        else:
            shutil.rmtree(directory_to_extract_to)           # Removes all the subdirectories!
            os.makedirs(directory_to_extract_to)

        path_to_zip_file = "pgn/downloads/"+lastname+'.zip'

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
        path_to_Eco = 'static/pgn/eco.txt'

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
        pathForGraph = "static/pgn/graph.html"
        fig.write_html(pathForGraph)
        with open(pathForGraph, 'r') as file:
            data = file.read()
        data = data.replace('</head>', '<meta http-Equiv="Cache-Control" Content="no-cache" /> <meta http-Equiv="Pragma" Content="no-cache" /> <meta http-Equiv="Expires" Content="0" /> </head>')
        
        # with open("InstaSeerDf2.html", "w") as file:
        #      file.write("<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css\" rel=\"stylesheet\" integrity=\"sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl\" crossorigin=\"anonymous\">")
        with open(pathForGraph, "w") as file:
            file.write(data)
    else:
        with open("static/pgn/graph.html", "w") as file:
            file.write(f"<h4 style='margin-left:30px; margin-top:15px'> Player {lastname} was not found in <a target='_blank' href='https://www.pgnmentor.com/files.html'>the database</a></h4>")
