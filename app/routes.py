from app import app
from app import db
from flask import Flask, render_template, redirect, url_for
#import pika, sys
import folium
import geemap.foliumap as geemap
import geemap.colormaps as cm
import ee
import pandas as pd
#import geopandas as gpd
import numpy as np
import sqlite3
from sqlalchemy import select


from app.models import Fires, Regions, Firms
from app.forms import MapForm
#from app.models import Regions


def sendmsg(task):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='powerImport', durable=True)


    channel.basic_publish(exchange='',
                          routing_key='powerImport',
                          body=str(task),
                          properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE))

    print(" [x] Sent ", task)

    connection.close()

@app.route("/")
@app.route("/index")
def index():
    con = sqlite3.connect("app.db")
    cur = con.cursor()
    firesresponse = Fires.query.all()
    if(len(firesresponse) == 0):
        return redirect(url_for('getdata'))
    #regionsresponse = Regions.query.all()
    #power = Power.query.all()
    return render_template("main.html", rows=firesresponse)

@app.route("/firms")
def firmspage():
    con = sqlite3.connect("app.db")
    cur = con.cursor()
    firmsresponse = Firms.query.all()
    firmsresplen = len(firmsresponse)
    print(firmsresplen)
    if(firmsresplen == 0):
        print("none detected")
        return redirect(url_for('getfirmsdata'))
    print("detected", firmsresponse)
    return render_template("firmspage.html", rows=firmsresponse)

@app.route("/update")
def update():
    sendmsg("Push")
    return redirect(url_for('index'))

@app.route("/map", methods=['GET', 'POST'])
def map():
    ee.Initialize(project='alshcheg-project1')
    form = MapForm()
    eurffl = ee.Image("users/sashatyu/2001-2022_fire_forest_loss_annual/EUR_fire_forest_loss_2001-22_annual")
    gff = ee.Image("UMD/hansen/global_forest_change_2021_v1_9")
    gfftc = gff.select(['treecover2000'])
    #cm.get_palette("terrain", n_class=8)
    vis_params = {
        "min": 0,
        "max": 100,
        "palette": cm.get_palette("hot", n_class=10)
    }
    #fed_oopt = ee.FeatureCollection("users/konstantinkobyakov/fed_oopt")
    """oopt_gdf = ee.data.computeFeatures({
        'expression': fed_oopt,
        'fileFormat': 'GEOPANDAS_GEODATAFRAME'
    })"""
    m = geemap.Map(
        width=800,
        height=600,
    )
    #m.add_geojson(in_geojson = "./fed_oopt_vect.geojson", layer_name = 'GeoJSON', fill_colors=["#6AFF59"])
    m.add_layer(ee_object = gfftc, vis_params = vis_params, name='GFFTC')
    m.add_layer(ee_object = eurffl, vis_params = {"palette": ["#F782FF"]}, name='EURFFL')
    #m.addLayer(gfftc, 'GFFTC')
    #m.addLayer(fed_oopt, {}, 'oopt')
    #m.add_data(data = oopt_gdf, column = 'TITLE')
    m.addLayerControl()
    m.setControlVisibility()
    return render_template("mappage.html", folmap=m._repr_html_(), form=form)

@app.route("/getdata")
def getdata():
    ee.Initialize(project='alshcheg-project1')
    eurffl = ee.Image("users/sashatyu/2001-2022_fire_forest_loss_annual/EUR_fire_forest_loss_2001-22_annual")
    fed_oopt = ee.FeatureCollection("users/konstantinkobyakov/fed_oopt")
    gff = ee.Image("UMD/hansen/global_forest_change_2021_v1_9")
    gffex = gff.select(['treecover2000']).gt(30)
    gffex = gffex.mask(gffex)
    eurfflmask = eurffl.mask(gffex)
    eurfflmask = eurfflmask.mask(eurfflmask)
    convolve = eurfflmask.gt(0).connectedComponents(ee.Kernel.circle(3), 10)
    convolve_mask = convolve.select('labels').unmask()
    filtered = eurfflmask.subtract(convolve_mask).gt(0)
    filtered = filtered.mask(filtered)
    lossAreaImage = filtered.gt(0).multiply(ee.Image.pixelArea())
    addedband = lossAreaImage.addBands(eurfflmask)
    lossRegYear = addedband.reduceRegions(
        collection=fed_oopt,
        reducer=ee.Reducer.sum().group(groupField=1),
        scale=30
    )
    forestedAreaImage = gffex.gt(0).multiply(ee.Image.pixelArea())
    forestedRegYear = forestedAreaImage.addBands(gffex).reduceRegions(
        collection=fed_oopt,
        reducer=ee.Reducer.sum().group(groupField=1),
        scale=30,
    )
    lossRegYearNoGeom = lossRegYear.select(
        propertySelectors = ['TITLE', 'CATEGORY', 'groups'],
        retainGeometry = False
    )
    forestedYearNoGeom = forestedRegYear.select(
        propertySelectors = ['TITLE', 'CATEGORY', 'SUBRF', 'groups'],
        retainGeometry = False
    )
    # creating dataframe
    df1 = ee.data.computeFeatures({
        'expression': lossRegYearNoGeom,
        'fileFormat': 'PANDAS_DATAFRAME'
    })
    print("INIT LENGTH: ", df1.shape[0])
    def extractyear(targetyear):
        for i in range(2001, 2023):
            colname = "y" + str(i)
            targetyear[colname] = 0
        for elem in targetyear["groups"]:
            gtemp = int(elem["group"])
            g = "y200" + str(gtemp) if gtemp < 10 else "y20" + str(gtemp)
            s = float(elem["sum"])
            targetyear[g] = s
    years = np.arange(2001, 2023)
    years2 = []
    for year in years: years2.append("y" + str(year))
    years = np.array(years2)
    firstelem = df1.iloc[0]
    print("CP2: ", df1.shape[0])
    extractyear(firstelem)
    yeardf = pd.DataFrame(data = firstelem[4:].values.reshape(1, -1), columns = years)
    for i in range (1, df1.shape[0]):
        curelem = df1.iloc[i]
        extractyear(curelem)
        yeardf.loc[len(yeardf.index)] = curelem[4:].values.reshape(1, -1)[0]
    mergeddf = df1.join(yeardf)
    print("CP3: ", mergeddf.shape[0])
    mergeddf = mergeddf.drop(columns=['geo', 'groups'])
    df2 = ee.data.computeFeatures({
        'expression': forestedYearNoGeom,
        'fileFormat': 'PANDAS_DATAFRAME'
    })
    df2["area"] = ""
    for i in range(df2.shape[0]):
        curelem = df2.iloc[i]["groups"]
        if (len(curelem) > 0):
            df2.loc[i, "area"] = curelem[0]["sum"]
        else:
            #print(i, " ", df2.iloc[i]["TITLE"])
            df2.loc[i, "area"] = 0
    df2 = df2.drop(columns=["geo", "groups"])
    mergeddf["area"] = df2["area"]
    # filling the object
    L = mergeddf.shape[0]
    print("L: ", L)
    for i in range(L):
        fires_obj = Fires(
            category = mergeddf['CATEGORY'][i],
            title = mergeddf['TITLE'][i],
            year2001 = mergeddf['y2001'][i],
            year2002 = mergeddf['y2002'][i],
            year2003 = mergeddf['y2003'][i],
            year2004 = mergeddf['y2004'][i],
            year2005 = mergeddf['y2005'][i],
            year2006 = mergeddf['y2006'][i],
            year2007 = mergeddf['y2007'][i],
            year2008 = mergeddf['y2008'][i],
            year2009 = mergeddf['y2009'][i],
            year2010 = mergeddf['y2010'][i],
            year2011 = mergeddf['y2011'][i],
            year2012 = mergeddf['y2012'][i],
            year2013 = mergeddf['y2013'][i],
            year2014 = mergeddf['y2014'][i],
            year2015 = mergeddf['y2015'][i],
            year2016 = mergeddf['y2016'][i],
            year2017 = mergeddf['y2017'][i],
            year2018 = mergeddf['y2018'][i],
            year2019 = mergeddf['y2019'][i],
            year2020 = mergeddf['y2020'][i],
            year2021 = mergeddf['y2021'][i],
            year2022 = mergeddf['y2022'][i],
            area = mergeddf['area'][i]
        )
        with app.app_context():
            db.session.add(fires_obj)
            db.session.commit()
    # filling the second table
    rdfcol1 = np.array([], dtype=np.intc)
    rdfcol2 = np.array([])
    rdfcol3 = np.array([])
    for i in range(df2.shape[0]):
        curelem = df2.iloc[i]
        #print("TESTTESTTESTTESTTESTTEST2: ", curelem)
        subdivlist = curelem["SUBRF"].split(",")
        #print("TESTTESTTESTTESTTESTTEST2: ", subdivlist)
        for j in range(len(subdivlist)):
            #if j>0:
                #print(i, ", ", subdivlist)
            #regionsdf.iloc[i] = [i, curelem["TITLE"], subdivlist[j]]
            rdfcol1 = np.append(rdfcol1, i)
            rdfcol2 = np.append(rdfcol2, curelem["TITLE"])
            rdfcol3 = np.append(rdfcol3, subdivlist[j])
            #rdfcol3.append(subdivlist[j])
    rdftest = np.array([rdfcol1, rdfcol2, rdfcol3])
    rdftest = np.transpose(rdftest)
    regionsdf = pd.DataFrame(data=rdftest, columns=["OOPTID", "TITLE", "REGION"])
    L2 = regionsdf.shape[0]
    for i in range(L2):
        regionsobj = Regions(
            oopt_id = regionsdf['OOPTID'][i],
            title = regionsdf['TITLE'][i],
            region = regionsdf['REGION'][i]
        )
        with app.app_context():
            db.session.add(regionsobj)
            db.session.commit()
    return redirect(url_for('map'))

@app.route("/getfirmsdata")
def getfirmsdata():
    print("getfirmsdata entered")
    ee.Initialize(project='alshcheg-project1')
    years = ee.List.sequence(2001, 2023)

    fed_oopt = ee.FeatureCollection("users/konstantinkobyakov/fed_oopt")

    firms = ee.ImageCollection("FIRMS").select('confidence')

    def firms_mask(m):
        firms_mask = m.gte(10)
        masked = m.updateMask(firms_mask)
        return masked

    firmsM = firms.map(firms_mask)

    def byYear(x):
        firms2 = firmsM.filterDate(ee.Date.fromYMD(x, 1, 1), ee.Date.fromYMD(x, 12, 31))
        cf = firms2.count().rename('colfire')
        area = ee.Image.pixelArea()
        firmsmask = cf.gt(0)
        witharea = cf.addBands(area)
        masked = witharea.updateMask(firmsmask)
        #var firms2_1 = witharea.updateMask(firms2.gte(10));
        return masked

    firms3 = ee.ImageCollection.fromImages(years.map(byYear))

    firms4 = firms3.toBands()

    fire_oopt = firms4.reduceRegions(
        collection = fed_oopt,
        reducer = ee.Reducer.sum(),
        scale = 1000,
    )

    #var ppnames = ee.List(['0_colfire', '1_colfire',  '2_colfire', '3_colfire', '4_colfire', '5_colfire','6_colfire', '7_colfire', '8_colfire', '9_colfire', '10_colfire', '11_colfire', '12_colfire', '13_colfire', '14_colfire', '15_colfire', '16_colfire', '17_colfire', '18_colfire', '19_colfire', '20_colfire', '21_colfire', '22_colfire', 'CATEGORY', 'SUBRF', 'TITLE', 'n_id']);
    ppnames = ee.List(['0_area', '0_colfire', '1_area', '1_colfire', '2_area', '2_colfire', '3_area', '3_colfire', '4_area', '4_colfire']) \
    .cat(['5_area', '5_colfire', '6_area', '6_colfire', '7_area', '7_colfire', '8_area', '8_colfire', '9_area', '9_colfire']) \
    .cat(['10_area', '10_colfire', '11_area', '11_colfire', '12_area', '12_colfire', '13_area', '13_colfire', '14_area', '14_colfire']) \
    .cat(['15_area', '15_colfire', '16_area', '16_colfire', '17_area', '17_colfire', '18_area', '18_colfire', '20_area', '20_colfire']) \
    .cat(['20_area', '20_colfire', '21_area', '21_colfire', '22_area', '22_colfire', 'CATEGORY', 'SUBRF', 'TITLE', 'n_id'])

    def renamingfunc(number):
        Numb1 = ee.Number(number).format('%04d')
        #Numb2 = ee.String(Numb1)
        return [ee.String("area").cat(Numb1), ee.String("colfire").cat(Numb1)]

    yearnames = years.map(renamingfunc)
    #var yearnames = years.map(function (number) {
    #  var N = ee.Number(number).toInt();
    #  return [ee.String(N).cat(ee.String("area")), ee.String(N).cat(ee.String("colfire"))];
    #});
    #print(yearnames);
    yearnames2 = yearnames.flatten().cat(['CATEGORY', 'SUBRF', 'TITLE', 'n_id'])

    fire_renamed = fire_oopt.select(
        propertySelectors = ppnames,
        newProperties = yearnames2,
        retainGeometry = False
    )
    df3 = ee.data.computeFeatures({
        'expression': fire_renamed,
        'fileFormat': 'PANDAS_DATAFRAME'
    })
    df3 = df3.drop(columns=['geo', 'n_id', 'SUBRF'])
    L3 = df3.shape[0]
    print("firms obj reached")
    for i in range(L3):
        firms_obj = Firms(
            category=df3['CATEGORY'][i], title=df3['TITLE'][i], area2001=df3['area2001'][i], firmcount2001=round(df3['colfire2001'][i]),
            area2002=df3['area2002'][i], firmcount2002=round(df3['colfire2002'][i]), area2003=df3['area2003'][i], firmcount2003=round(df3['colfire2003'][i]),
            area2004=df3['area2004'][i], firmcount2004=round(df3['colfire2004'][i]), area2005=df3['area2005'][i], firmcount2005=round(df3['colfire2005'][i]),
            area2006=df3['area2006'][i], firmcount2006=round(df3['colfire2006'][i]), area2007=df3['area2007'][i], firmcount2007=round(df3['colfire2007'][i]),
            area2008=df3['area2008'][i], firmcount2008=round(df3['colfire2008'][i]), area2009=df3['area2009'][i], firmcount2009=round(df3['colfire2009'][i]),
            area2010=df3['area2010'][i], firmcount2010=round(df3['colfire2010'][i]), area2011=df3['area2011'][i], firmcount2011=round(df3['colfire2011'][i]),
            area2012=df3['area2012'][i], firmcount2012=round(df3['colfire2012'][i]), area2013=df3['area2013'][i], firmcount2013=round(df3['colfire2013'][i]),
            area2014=df3['area2014'][i], firmcount2014=round(df3['colfire2014'][i]), area2015=df3['area2015'][i], firmcount2015=round(df3['colfire2015'][i]),
            area2016=df3['area2016'][i], firmcount2016=round(df3['colfire2016'][i]), area2017=df3['area2017'][i], firmcount2017=round(df3['colfire2017'][i]),
            area2018=df3['area2018'][i], firmcount2018=round(df3['colfire2018'][i]), area2019=df3['area2019'][i], firmcount2019=round(df3['colfire2019'][i]),
            area2020=df3['area2020'][i], firmcount2020=round(df3['colfire2020'][i]), area2021=df3['area2021'][i], firmcount2021=round(df3['colfire2021'][i]),
            area2022=df3['area2022'][i], firmcount2022=round(df3['colfire2022'][i]), area2023=df3['area2023'][i], firmcount2023=round(df3['colfire2023'][i])
            )
        print("firms obj created")
        with app.app_context():
            db.session.add(firms_obj)
            db.session.commit()
            print("sent!")
    return redirect(url_for('firmspage'))