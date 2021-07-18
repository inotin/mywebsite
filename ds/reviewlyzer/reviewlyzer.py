#!/usr/bin/env python
# coding: utf-8
import os
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.request
import numpy as np
from . import charwords, googleCreds
from tqdm import tqdm
import nltk
from nltk.corpus import wordnet
from nltk.corpus import opinion_lexicon
#nltk.download('opinion_lexicon')
from nltk.sentiment import vader
#nltk.download('vader_lexicon')
from nltk.tokenize import treebank
from nltk.corpus import stopwords
from deepsegment import DeepSegment
from scipy.stats import hmean
import pandas as pd
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')
from youtubesearchpython import VideosSearch
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from IPython.core.display import display,HTML
from google_images_search import GoogleImagesSearch
from scipy.stats import ttest_ind
from plotly.subplots import make_subplots
# In[218]:


def getYouTubeLinksFromSearch(query, maxNumber = 5):
    """
    The function returns a list of youtube urls from the query results

    Input:
    query:      str
                a string for searching youtube videos

    maxNumber:  int, default: 5
                number of urls for output,

    Output:
    list(str): list of urls

    """
    videosSearch = VideosSearch(query, limit = maxNumber, region='US')
    ids = []
    for i in videosSearch.result()['result']:
        ids.append('https://www.youtube.com/watch?v='+i['id'])
        #(i['title'])
    return ids

#Test
# getYouTubeIDsFromSearch('iphone 11 pro')


# ## Fetching textual data

# In[210]:


def getTextFromYoutubeCaptions(vidId):
    """
    The function gets text from captions in the YouTube video, ID of which is given as an input.

    Input:
    vidId: str
           YouTube Video ID

    Output:
    str: list of words from the captions
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(vidId)
        captions = ["NoText"]
        try:
            captions = YouTubeTranscriptApi.get_transcript(vidId, languages=['en'])
        except:
            #print("!Translating captions to English")
            transcript = transcript_list.find_transcript(['ru','it'])
            captions = transcript.translate('en').fetch()
            #print(captions)
            #input()
        text = ""

        for element in captions:
            text+=element['text']+" "
        text = text.replace("\n"," ")
        # print(text)
        return text
    except:
        print('Captions are not available')
        return 'Captions are not available'

#Testing function
# getTextFromYoutubeCaptions("eOW9jgCahnk")[:100]


# In[174]:


def tag_visible(element):
    """
    The function defines if element is visible

    Input:
    html element

    Output:
    bool: True if visible, False otherwise
    """

    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def getTextFromUrl(url):
    """
    The function returns visible text from html

    Input:
    html

    Output:
    str: text
    """
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)
#Testing
# getTextFromUrl('https://www.ilpost.it/2021/03/19/cina-stati-uniti-alaska-blinken/')[:1000]


# ## Scoring functions
# In this sections scoring functions are defined. They return score for a given piece of text. The higher the score the more positive text is. Further these functions will be used to assess pieces of text around keywords.

# In[175]:
import nltk
nltk.download('opinion_lexicon')
nltk.download('vader_lexicon')
def assessPolarity(text):
    """
    Polarity assessment based on Liu and Hu opinion lexicon
    """
    stop_words = set(stopwords.words('english'))
    tokenizer = treebank.TreebankWordTokenizer()
    wordsList = [word.lower() for word in tokenizer.tokenize(text)]
    wordsList = [word for word in wordsList if not word in stop_words]
    scores = []

    for word in wordsList:
        if word in set(opinion_lexicon.positive()):
            score = 1
        elif word in set(opinion_lexicon.negative()):
            score=-1
        else:
            score=0
        scores.append(score)
#     print(words)
#     print(scores)
    return np.sum(scores)

#Testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# assessPolarity(text)


# In[176]:


def assessPolarityVader(text, split_sentences = False):
    """
    Polarity assessment based on Vader
    """
    sia = vader.SentimentIntensityAnalyzer()
    #it's better to feed vader with phrases or sentences
    #but as soon as caption text does not contain punctuation i used deepsegment library
    #to split the caption text into sentences
    score = 0
    if split_sentences:
        segmenter = DeepSegment('en')
        sentenceList = segmenter.segment_long(text)

        for sentence in sentenceList:
            s = sia.polarity_scores(sentence)['compound']
#             print(sentence)
#             print('Score:', s)
#             print('-'*20)
            score+=s
    else:
        score+=sia.polarity_scores(text)['compound']
    return score

#testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# assessPolarityVader(text, split_sentences = True)


# In[177]:


def antiScore(score):
    """
    A function that returns a penalyzing score for word "not" according to the function

    Input:
    score (float): input score

    Output:
    float: a penalty to be added to the initial score if word "not" is present in the word list

    """

    return 0.58 - 1.15*score


def assessPolarityCustom(text, dictScores=None):
    """
    The function returns score for the piece of text given as input list of words according to dictScores

    Input:
    pieceOfText (list(str)): keywords to search for
    dictScores (dict): a dictionary of words and corresponding scores in form:
             {"A":[5,["very", "extremely", "surprisingly","great", "much", "incredibly"]],
              "B":[4,["pretty","good", "nice"]],
              "C":[3, ["enough","inexpensive", "cheap", "affordable","low","decent", "quite"]],
              "D":[-2,["weak","minimum","little"]]}

    Output:
    float: score
    """
    if dictScores == None:
        dictScores = {"A":[5,["very", "extremely", "surprisingly","great", "much", "plenty","incredibly"]+charwords.veryWords],
              "B":[4,["pretty","good", "nice"]+charwords.prettyWords],
              "C":[3, ["enough", "affordable","low","decent", "quite"]+charwords.enoughWords],
              "D":[-2,["weak","minimum","little"]+charwords.weakWords]}

    stop_words = set(stopwords.words('english'))
    tokenizer = treebank.TreebankWordTokenizer()
    wordsList = [word.lower() for word in tokenizer.tokenize(text)]
    wordsList = [word for word in wordsList if not word in stop_words]

    score = 0
    lastScore = 0
    wordsList = list(set(wordsList))
    #print(wordsList)
    for word in wordsList:
        for key in dictScores:
            if word in dictScores[key][1]:
                lastScore = dictScores[key][0]
                #print(word,":",lastScore)
        if word == "not":
            lastScore = lastScore + antiScore(lastScore)
        score += lastScore
        lastScore=0
    return score

#Testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# assessPolarityCustom(text)


# ## Working with keywords
# In this section the function is defined which allows to extract a set amount of words around a key word.

# In[178]:
# import nltk
# nltk.download('stopwords')

def getPieceByKeyWords(text, keyWords, backward=5, forward=5):
    """
    The function returns a piece of caption text in a form of list with a given range.

    Input:
    text (str): input list of the caption text
    keyWords (list(str)): keywords to search for
    backward (int): number of words to include before found keyword
    forward (int): number of words to include before found keyword

    Output:
    list(str): list of words close to a given keyword
    """

    #stop_words = set(stopwords.words('english'))
    tokenizer = treebank.TreebankWordTokenizer()
    wordsList = [word.lower() for word in tokenizer.tokenize(text)]

    lst = []
    i = 0

    for word in wordsList:
        if word in set(keyWords):
            rear = max(0, i - backward)
            front = min(len(wordsList)-1, i+forward)
            lst.append(" ".join(wordsList[rear:front]))
        i+=1
    return lst

#Testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# getPieceByKeyWords(text, ['engine'])


# In[207]:



def getScores(dct, keyWords):
    scoresDict = defaultdict()
    dctForHist = {'product':[],'keyword':[], 'aP':[], 'aPV':[],'aPC':[]}

    for url in dct['urls']:
        try:
            if 'youtube' in url:
                text = getTextFromYoutubeCaptions(url.split('=')[1])
            else:
                text = getTextFromUrl(url)

            for keyWord in keyWords:
                textList = getPieceByKeyWords(text,[keyWord])
                aP, aPV, aPC = 0, 0, 0
                for t in textList:
                    aP+=assessPolarity(t)
                    aPV+=assessPolarityVader(t)
                    aPC+=assessPolarityCustom(t)
                scoresDict[keyWord] = [aP,aPV,aPC]
                dctForHist['product'].append(dct['product'])
                dctForHist['keyword'].append(keyWord)
                dctForHist['aP'].append(aP)
                dctForHist['aPV'].append(aPV)
                dctForHist['aPC'].append(aPC)
        except:
            pass
    dfAllScores = pd.DataFrame(dctForHist)
    dfAllScores['mean']=np.mean(dfAllScores[['aP', 'aPV', 'aPC']],axis=1)

    dfMeanScores = dfAllScores.groupby(by='keyword').mean()[['mean']].reset_index().T.reset_index()
    dfMeanScores.columns = dfMeanScores.iloc[0,:].values
    dfMeanScores=dfMeanScores.drop(columns=['keyword'])
    dfMeanScores['product']=dct['product']
    dfMeanScores = dfMeanScores[['product']+list(dfMeanScores.columns[:-1])].iloc[1:,:]

    return dfMeanScores, dfAllScores

#Testing
# dct = {'name':"Honda CB650R",'urls':["https://www.youtube.com/watch?v=PO2uFDS1P3A",
#            "https://www.youtube.com/watch?v=GQK79vCohC4",
#            "https://www.youtube.com/watch?v=5AR5PwffLzI",
#            "https://www.youtube.com/watch?v=c0SL4pBJP4Y",
#            "https://ridermagazine.com/2020/06/05/2020-husqvarna-vitpilen-701-road-test-review/"]}

# print(getScores(dct, ['comfort','engine', 'design', 'handling']))


# In[179]:


def getSynonimList(word):
    """
    The function returns list of synonims base on wordnet.synsets of nltk library
    for the text provide by urlList based on key words and dictScores

    Input:
    word (str): input word

    Output:
    list(str)
    """

    synonyms = []

    for syn in wordnet.synsets(word):
        for l in syn.lemmas():
            synonyms.append(l.name().lower())
    print(synonyms)
    return (list(set(synonyms)))
#Testing
#getSynonimList('cost')


# In[214]:


def getSetScores(productNames, productKeyWords, plot = False):
    """
    The function returns a dataframe with scores for products according to key words.

    Input:
    productNames    (list): input list of strings with product names
    productKeyWords (list): input list of strings with key words
    plot            (bool): default=False, if true plots barplots with scores and saves them to HTML ("result.html")

    Output:
    pandas dataframe with scores
    """
    productSet = []
    for product in productNames:
        dct = defaultdict()
        dct['product']=product
        dct['urls']=getYouTubeLinksFromSearch(product)
        productSet.append(dct)

    df = pd.DataFrame()
    for m in productSet:
        df = pd.concat([df, getScores(m,productKeyWords)])

    df['total']=np.mean(df.iloc[:,1:], axis = 1)
    if plot:
        numOfPlots = int(np.sum([np.sum(df[x].sum()!=0)>0 for x in df.columns[1:]]))

        fig = make_subplots(rows=numOfPlots, cols=1,
                    vertical_spacing=0.04)

        r=1
        for n in df.columns[1:]:
            if np.sum(df[n].sum()!=0)>0:
                fig.add_trace(go.Bar(x=df['product'], y=df[n], name = n),
                              row=r, col=1,)
                r+=1
        fig.update_layout(height=200*numOfPlots)
        fig.show()
        fig.write_html("static/reviewlyzer/result.html")

    df.to_html('static/reviewlyzer/df.html')
    return df


# In[223]:


def getSetScoresText(productNames, productKeyWords, plot = False, maxNumber = 15, api_key=googleCreds.GOOGLE_API_KEY2, cx = googleCreds.GOOGLE_CX,
pathForOutput = "static/reviewlyzer/"):

    """
    The function returns a dataframe with scores for products according to key words.

    Input:
    productNames    (str): input string with product names separated by \n
    productKeyWords (str): input string with key words separated by \n
    plot            (bool): default=False, if true plots barplots with scores and saves them to HTML ("result.html")

    Output:
    pandas dataframe with scores
    """
    #global fig
    fig = None

    if not os.path.exists(pathForOutput):
        os.makedirs(pathForOutput)

    productNames = productNames.replace('\r','')
    productKeyWords = productKeyWords.replace('\r','')

    productNames = productNames.split('\n')
    productKeyWords = productKeyWords.lower().split('\n')
    print(productNames)
    print(productKeyWords)
    # input()
    productDictSet = []
    for product in productNames:
        dct = defaultdict()
        dct['product']=product
        dct['urls']=getYouTubeLinksFromSearch(product, maxNumber)
        productDictSet.append(dct)


    dfAllScores = pd.DataFrame()

    for m in productDictSet:
        dfTemp = getScores(m, productKeyWords)
#         dfMeanScores = pd.concat([dfMeanScores, dfTemp[0]])
        dfAllScores = pd.concat([dfAllScores, dfTemp[1]])



    # df = pd.DataFrame()
    # for m in productSet:
    #     dfT = getScores(m,productKeyWords)
    #     print(dfT)
    #     df = pd.concat([df, dfT])
    dfAllScores.iloc[:,2:] = dfAllScores.iloc[:,2:]/np.max(dfAllScores.iloc[:,2:])
    dfAllScores['mean']=np.mean(dfAllScores.iloc[:,2:], axis=1)
    print(dfAllScores.head(10))

    dfMeanScores = pd.DataFrame()
    for product in productNames:
        dfTemp = dfAllScores[dfAllScores['product']==product]
        dfTemp = dfTemp.groupby(by='keyword').mean()[['mean']].reset_index().T.reset_index()
        dfTemp.columns = dfTemp.iloc[0,:].values
        dfTemp=dfTemp.drop(columns=['keyword'])
        dfTemp['product']=product
        dfTemp = dfTemp[['product']+list(dfTemp.columns[:-1])].iloc[1:,:]
        dfMeanScores = pd.concat([dfMeanScores, dfTemp])
    dfMeanScores['mean']=np.mean(dfMeanScores.iloc[:,1:], axis=1)
    print(dfMeanScores.head(10))

    #dfAllScores['total']=np.mean(df.iloc[:,1:], axis = 1)
    if plot:
        numOfPlots = int(np.sum([np.sum(dfMeanScores[x].sum()!=0)>0 for x in dfMeanScores.columns[1:]]))
        if numOfPlots!=0:
            fig = make_subplots(rows=numOfPlots, cols=1,
                        vertical_spacing=0.06)

            r=1
            for n in dfMeanScores.columns[1:]:
                if np.sum(dfMeanScores[n].sum()!=0)>0:
                    fig.add_trace(go.Bar(x=dfMeanScores['product'], y=dfMeanScores[n], name = n),
                                  row=r, col=1,)
                    r+=1

            fig.update_layout(height=200*numOfPlots)
            fig.write_html(pathForOutput+"reviewlyzerResult.html")
            with open(pathForOutput+"reviewlyzerResult.html", 'r') as file:
                data = file.read()
            data = data.replace('<table border="1" class="dataframe">', '<meta http-Equiv="Cache-Control" Content="no-cache" /> <meta http-Equiv="Pragma" Content="no-cache" /> <meta http-Equiv="Expires" Content="0" /> <table class="table">')
            data = data.replace("style=\"text-align: right;\"", "style=\"text-align: left;\"")
            data = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">\n' + data
            # with open("InstaSeerDf2.html", "w") as file:
            #      file.write("<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css\" rel=\"stylesheet\" integrity=\"sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl\" crossorigin=\"anonymous\">")
            with open(pathForOutput+"reviewlyzerResult.html", "w") as file:
                file.write(data)


        #Histograms
        px.histogram(dfAllScores[dfAllScores['mean']!=0],x='mean', facet_col='keyword', facet_row='product', labels={'mean':'mean score'}).write_html(pathForOutput+"reviewlyzerHistograms.html")


        thresholdPvalue = 0.1
#df5 = pd.DataFrame()
        # c = 0

        for n1 in dfAllScores['product'].unique():
            print("-"*10)
            print(n1)
            print(dfAllScores[dfAllScores['product']==n1].groupby(by='keyword').mean())
            #input()


        dctPvalues = {'name_pair':[],
        'keyword':[],
        'result':[],
        'pvalue':[],
        'score1':[],
        'score2':[]}
        for k in dfAllScores['keyword'].unique():
        #     c+=1
            pvalues = []
            for n1 in dfAllScores['product'].unique():
                pv = []
                for n2 in dfAllScores['product'].unique():
                    a = dfAllScores[(dfAllScores['product']==n1) & (dfAllScores['keyword']==k)]['mean']
                    b = dfAllScores[(dfAllScores['product']==n2) & (dfAllScores['keyword']==k)]['mean']
                    pv.append(ttest_ind(a,b,equal_var=False).pvalue)
                    if n1!=n2:
                        dctPvalues['name_pair'].append(tuple(np.sort([n1,n2])))
                        dctPvalues['pvalue'].append(ttest_ind(a,b, equal_var=False).pvalue)
                        dctPvalues['keyword'].append(k)
                        score1 = np.mean(dfAllScores[(dfAllScores['product']==n1) & (dfAllScores['keyword']==k)]['mean'])
                        score2 = np.mean(dfAllScores[(dfAllScores['product']==n2) & (dfAllScores['keyword']==k)]['mean'])
                        dctPvalues['score1'].append(score1)
                        dctPvalues['score2'].append(score2)
                        if score1>score2:
                            dctPvalues['result'].append(f'{n1} is better than {n2}')
                        else:
                            dctPvalues['result'].append(f'{n2} is better than {n1}')
                pvalues.append(pv)
        # print(df7)
        # input()
        dfPvalues=pd.DataFrame(dctPvalues)
        df8 = pd.DataFrame()
        for k in dfPvalues['keyword'].unique():
            df8 = pd.concat([df8,dfPvalues[dfPvalues['keyword']==k].drop_duplicates(subset='name_pair')])
        df8 = df8.sort_values(by='pvalue')
        df8 = df8[df8['pvalue']<0.3]
        df8 = df8.iloc[:,1:]
        df8.to_html(pathForOutput+"reviewlyzerPvalues.html", index=False)

        with open(pathForOutput+"reviewlyzerPvalues.html", 'r') as file:
            data = file.read()
        data = data.replace('<table border="1" class="dataframe">', '<meta http-Equiv="Cache-Control" Content="no-cache" /> <meta http-Equiv="Pragma" Content="no-cache" /> <meta http-Equiv="Expires" Content="0" /> <table class="table">')
        data = data.replace("style=\"text-align: right;\"", "style=\"text-align: left;\"")
        data = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">\n' + data
        # with open("InstaSeerDf2.html", "w") as file:
        #      file.write("<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css\" rel=\"stylesheet\" integrity=\"sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl\" crossorigin=\"anonymous\">")
        with open(pathForOutput+"reviewlyzerPvalues.html", "w") as file:
            file.write(data)



    #pd.set_option('display.max_colwidth', 60)
        f = px.box(dfAllScores, y='mean', facet_row='keyword', x='product', color='keyword')
        f.update_layout(height=150*len(dfAllScores['keyword'].unique()))
        f.write_html(pathForOutput+"reviewlyzerBoxPlots.html")

    dfIm2 = dfMeanScores.copy()
    images = []
    for i in dfIm2['product']:
        gis = GoogleImagesSearch(api_key, cx)
        _search_params = {
            'q': i,
            'num': 1
        }
        try:
            gis.search(search_params=_search_params)
            images.append(gis.results()[0].url)
        except:
            images.append("https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg")
    dfIm2 = dfIm2.reset_index()
    dfIm2 = dfIm2.drop(columns='index')
    # your images
    colOrder = ['image']+list(dfIm2.columns)
    dfIm2['image'] = images

    # convert your links to html tags
    def path_to_image_html(path):
        return '<img src="'+ path + '" width="200" >'

    pd.set_option('display.max_colwidth', None)
    dfIm2 = dfIm2[colOrder]
    #HTML(dfIm2.style.hide_index().set_properties(**{'font-size': '11pt','background-color': '#edeeef','border-color': 'black','border-style' :'solid' ,'border-width': '0px','border-collapse':'collapse'}).render())
    dfIm2.to_html(pathForOutput+"reviewlyzerDf.html", escape=False ,formatters=dict(image=path_to_image_html))
    #df.to_html('static/reviewlyzerDf.html', index=False, border = 0)
    with open(pathForOutput+"reviewlyzerDf.html", 'r') as file:
        data = file.read()
    data = data.replace('<table border="1" class="dataframe">', '<head>\n<meta http-equiv="cache-control" content="max-age=0" />\n<meta http-equiv="cache-control" content="no-cache" />\n<meta http-equiv="expires" content="0" />\n<meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />\n<meta http-equiv="pragma" content="no-cache" />\n</head>\n<table class="table">')
    data = data.replace("style=\"text-align: right;\"", "style=\"text-align: left;\"")
    data = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">\n' + data
    # with open("InstaSeerDf2.html", "w") as file:
    #      file.write("<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css\" rel=\"stylesheet\" integrity=\"sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl\" crossorigin=\"anonymous\">")
    with open(pathForOutput+"reviewlyzerDf.html", "w") as file:
        file.write(data)
    return dfMeanScores
