from django.shortcuts import render
from . import pgn, charwords, googleCreds, instaSeer
from .miluogo import score, models, updateMap
from .reviewlyzer import reviewlyzer, charwords
import pandas as pd
def home(request):
    return render(request, 'index.html')

def aboutit(request):
    return render(request, 'aboutit2.html')

lastLastName = 'Adams'
def cell1(request):
    global lastLastName
    input_lastname = request.GET.get('lastname', lastLastName)
    if (input_lastname!=lastLastName):
        pgn.getGraph(input_lastname)
        lastLastName = input_lastname
    return render(request, 'pgn.html', {'given_lastname':input_lastname})

def cell6(request):
    return render(request, 'moviePosters.html')
def cell7(request):
    return render(request, 'instaSeer.html')
def cell8(request):
    return render(request, 'airfoils.html')
def cell9(request):
    return render(request, 'about.html')

def cell4(request):
    return render(request, 'fakeNews.html')

def cell5(request):
    return render(request, 'sales.html')

lastJobName = 'Data Scientist'
last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance = 2.5, 2.5, 2.5, 2.5, 2.5
lastMinRent, lastMaxRent = 800, 1500
def cell2(request):
    global lastJobName, lastMinRent, lastMaxRent
    global last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance
    input_jobName = request.GET.get('jobName', 'Data Scientist')
    price_importance = request.GET.get('price_importance', 2.5)
    work_importance = request.GET.get('work_importance', 2.5)
    danger_importance = request.GET.get('danger_importance', 2.5)
    air_importance = request.GET.get('air_importance', 2.5)
    green_importance = request.GET.get('green_importance', 2.5)
    minRent = request.GET.get('minRent', 800)
    maxRent = request.GET.get('maxRent', 1500)
    if (minRent!=lastMinRent) or (maxRent!=lastMaxRent) or (input_jobName!=lastJobName) or ([last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance]!=[price_importance, work_importance, danger_importance, air_importance, green_importance]):
        #price_importance, work_importance, danger_importance, air_importance, green_importance = 5,5,5,5,5
        score.score(input_jobName,price_importance, work_importance, danger_importance, air_importance, green_importance, minRent = minRent, maxRent = maxRent)
        updateMap.updateMap()
        lastJobName = input_jobName
        lastMinRent = minRent
        lastMaxRent = maxRent
        last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance = price_importance, work_importance, danger_importance, air_importance, green_importance
    #getCompaniesDataframe(googleCreds.GOOGLE_API_KEY, jobName=job_name, dfPath="static/miluogo/1_dfCompanies.csv")
    #miluogo.updateMap(job_name, price_importance, work_importance, danger_importance, air_importance, green_importance)
    return render(request, 'miluogo.html',{'given_jobName':input_jobName, 'given_price_importance':price_importance,
    'given_work_importance':work_importance, 'given_danger_importance':danger_importance,
    'given_air_importance':air_importance,'given_green_importance':green_importance, 'given_minRent':minRent, 'given_maxRent':maxRent})



lastProductNames = 'iPhone 11 Pro\niPhone 12 Pro\nGoogle Pixel 5\nGoogle Pixel 4A'
lastProductKeyWords = 'screen\ncamera\nstabilization\nbattery\nmaterials\nprice'



def cell3(request):
    global lastProductNames
    global lastProductKeyWords
    input_productNames = request.GET.get('productNames', 'iPhone 11 Pro\niPhone 12 Pro\nGoogle Pixel 5\nGoogle Pixel 4A')
    input_productKeyWords = request.GET.get('productKeyWords', 'screen\ncamera\nstabilization\nbattery\nmaterials\nprice')

    if (input_productNames!=lastProductNames) or (input_productKeyWords!=lastProductKeyWords):
        reviewlyzer.getSetScoresText(input_productNames, input_productKeyWords, maxNumber=5, plot = True, api_key=googleCreds.GOOGLE_API_KEY2, cx = googleCreds.GOOGLE_CX)
        lastProductNames= input_productNames
        lastProductKeyWords = input_productKeyWords
    plotHeight0 = str(int(30+50*len(pd.read_html('static/reviewlyzer/reviewlyzerPvalues.html')[0])))+'px'
    plotHeight1 = str(200*len(input_productNames.split('\n')))+'px'
    plotHeight2 = str(200*len(input_productKeyWords.split('\n')))+'px'
    return render(request, 'reviewlyzer.html', {'given_productNames':input_productNames,'given_productKeyWords':input_productKeyWords,'plotHeight0':plotHeight0,'plotHeight1':plotHeight1,'plotHeight2':plotHeight2})




lastImageUrls = 'https://www.spica.com/sites/5d683cbd24d35f11477fed0f/content_entry5d8b217524d35f11477ff600/5f8d3fbb24d35f5015ebe319/files/netherlands.jpeg\nhttps://timelapsenetwork.com/wp-content/uploads/TL-foto-Milano-City-5.jpg\nhttps://www.kanoa.it/wp-content/uploads/2019/04/Valletta-Malta.jpg'
lastCaptionTexts = 'This is a beautiful picture of Netherlands #amsterdam @user1 @user2\nThis is Milano. Vibrant and marvelous city #milano #italy @user3\nBoats in Valletta, Malta #malta #valletta'
def cell7(request):
    global lastImageUrls
    global lastCaptionTexts
    input_ImageUrls = request.GET.get('ImageUrls', 'https://www.spica.com/sites/5d683cbd24d35f11477fed0f/content_entry5d8b217524d35f11477ff600/5f8d3fbb24d35f5015ebe319/files/netherlands.jpeg\nhttps://timelapsenetwork.com/wp-content/uploads/TL-foto-Milano-City-5.jpg\nhttps://www.kanoa.it/wp-content/uploads/2019/04/Valletta-Malta.jpg')
    input_CaptionTexts = request.GET.get('CaptionTexts', 'This is a beautiful picture of Netherlands #amsterdam @user1 @user2\nThis is Milano. Vibrant and marvelous city #milano #italy @user3\nBoats in Valletta, Malta #malta #valletta')
    if (input_ImageUrls!=lastImageUrls) or (input_CaptionTexts!=lastCaptionTexts):
        instaSeer.getScores(input_ImageUrls, input_CaptionTexts)
        lastImageUrls = input_ImageUrls
        lastCaptionTexts = input_CaptionTexts
    # plotHeight1 = str(200*len(input_productNames.split('\n')))+'px'
    # plotHeight2 = str(200*len(input_productKeyWords.split('\n')))+'px'
    return render(request, 'instaSeer.html', {'given_ImageUrls':input_ImageUrls,'given_CaptionTexts':input_CaptionTexts})
