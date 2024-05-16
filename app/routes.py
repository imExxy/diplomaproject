from app import app
from app import db
from flask import Flask, render_template, redirect, url_for, session
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
from app.forms import MapForm, StatsFormReg, StatsIndiv, FiresReg, FirmsReg
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

@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
def index():
    con = sqlite3.connect("app.db")
    cur = con.cursor()
    firesresponse = Fires.query.all()
    if(len(firesresponse) == 0):
        return redirect(url_for('getdata'))
    #regionsresponse = Regions.query.all()
    #power = Power.query.all()
    firesregquery = """select *
    from fires f
    join regions r on f.id = r.oopt_id
    where r.region like \'"""
    selected_region = ""
    form_fr = FiresReg()
    if(form_fr.validate_on_submit()):
        if(form_fr.reg.data):
            selected_region = form_fr.reg.data
    toexec = firesregquery + selected_region + "\';"
    regresponse = cur.execute(toexec).fetchall()
    return render_template("fireregform.html", rows=firesresponse, rows2=regresponse, form=form_fr)

@app.route("/firms", methods=['GET', 'POST'])
def firmspage():
    con = sqlite3.connect("app.db")
    cur = con.cursor()
    firmsresponse = Firms.query.all()
    firmsresplen = len(firmsresponse)
    print(firmsresplen)
    if(firmsresplen == 0):
        print("none detected")
        return redirect(url_for('getfirmsdata'))
    #print("detected", firmsresponse)
    form_firmr = FirmsReg()
    firmsregquery = """select *
    from firms f
    join regions r on f.id = r.oopt_id
    where r.region like \'"""
    selected_region = ""
    if(form_firmr.validate_on_submit()):
        if(form_firmr.reg.data):
            selected_region = form_firmr.reg.data
    toexec = firmsregquery + selected_region + "\';"
    regresponse = cur.execute(toexec).fetchall()
    return render_template("firmregform.html", rows=firmsresponse, rows2=regresponse, form=form_firmr)

@app.route("/update")
def update():
    sendmsg("Push")
    return redirect(url_for('index'))

@app.route("/map", methods=['GET', 'POST'])
def map():
    ee.Initialize(project='alshcheg-project1')
    formmap = MapForm()
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
    m2 = geemap.Map(
        width=800,
        height=600,
    )
    if formmap.validate_on_submit():
        if (formmap.raster_layers.data):
            print("1: ", formmap.raster_layers)
            #print("2: ", formmap.raster_layers[0])
            print("3: ", formmap.raster_layers.data)
            resplist = formmap.raster_layers.data
            if('gff' in resplist):
                print("to add gff")
                #session["l1"] = "yes"
                m.add_layer(ee_object = gfftc, vis_params = vis_params, name='GFFTC')
            #else:
                #print("removing l1")
                #session.pop("l1", None)
            if('eurffl' in resplist):
                print("to add eurffl")
                #session["l2"] = "yes"
                m.add_layer(ee_object = eurffl, vis_params = {"palette": ["#F782FF"]}, name='EURFFL')
            #else:
                #print("removing l2")
                #session.pop("l2", None)
        if (formmap.year_selection.data):
            selected_year = formmap.year_selection.data
            if(selected_year >= 2001 and selected_year <= 2023):
                firms = ee.ImageCollection("FIRMS").select('confidence')
                def firms_mask(m):
                    firms_mask = m.gte(10)
                    masked = m.updateMask(firms_mask)
                    return masked
                firmsM = firms.map(firms_mask)
                testforyear = firmsM.filterDate(ee.Date.fromYMD(selected_year, 1, 1), ee.Date.fromYMD(selected_year, 12, 31))
                m2.add_layer(ee_object = testforyear, vis_params = {"palette": ["#F782FF"]}, name='FIRMS')
    #print(session)
    #if("l1" in session):
        #print("l1 att 2")
        #m.add_layer(ee_object = gfftc, vis_params = vis_params, name='GFFTC')
        #return render_template("mapform.html", folmap=m._repr_html_(), form=formmap)
    #if("l2" in session):
        #print("l2 att 2")
        #m.add_layer(ee_object = eurffl, vis_params = {"palette": ["#F782FF"]}, name='EURFFL')
        #return render_template("mapform.html", folmap=m._repr_html_(), form=formmap)
    #m.add_layer(ee_object = gfftc, vis_params = vis_params, name='GFFTC')
    #m.add_layer(ee_object = eurffl, vis_params = {"palette": ["#6AFF59"]}, name='EURFFL')
    m.add_geojson(in_geojson = "./fed_oopt_vect.geojson", layer_name = 'GeoJSON', fill_colors=["#F782FF"])
    m2.add_geojson(in_geojson = "./fed_oopt_vect.geojson", layer_name = 'GeoJSON', fill_colors=["#F782FF"])
    #m.addLayer(gfftc, 'GFFTC')
    #m.addLayer(fed_oopt, {}, 'oopt')
    #m.add_data(data = oopt_gdf, column = 'TITLE')
    #m.addLayerControl()
    #m.setControlVisibility()
    return render_template("mapform.html", folmap=m._repr_html_(), folmap2=m2._repr_html_(), form=formmap)

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
            rdfcol1 = np.append(rdfcol1, i+1)
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
    # extra (forested mask setup)
    gff = ee.Image("UMD/hansen/global_forest_change_2021_v1_9")
    gffex = gff.select(['treecover2000']).gt(30)
    gffex = gffex.mask(gffex)
    forestedAreaImage = gffex.gt(0).multiply(ee.Image.pixelArea())
    # extra end
    years = ee.List.sequence(2001, 2023)

    fed_oopt = ee.FeatureCollection("users/konstantinkobyakov/fed_oopt")

    firms = ee.ImageCollection("FIRMS").select('confidence')

    def firms_mask(m):
        firms_mask = m.gte(10)
        masked = m.updateMask(firms_mask)
        return masked

    firmsM = firms.map(firms_mask)
    # extra step begin
    def forestmaskhelper(m):
        return m.updateMask(forestedAreaImage)
    testmask = firmsM.map(forestmaskhelper)
    # extra step end

    def byYear(x):
        firms2 = testmask.filterDate(ee.Date.fromYMD(x, 1, 1), ee.Date.fromYMD(x, 12, 31))
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

@app.route("/stats",  methods=['GET', 'POST'])
def stats():
    con = sqlite3.connect("app.db")
    cur = con.cursor()
    firesresponse = Fires.query.all()
    if(len(firesresponse) == 0):
        return redirect(url_for('getdata'))
    firmsresponse = Firms.query.all()
    firmsresplen = len(firmsresponse)
    #print(firmsresplen)
    if(firmsresplen == 0):
        #print("none detected")
        return redirect(url_for('getfirmsdata'))
    sf1 = StatsFormReg()
    qtext1 = """select sum(year2001) as y2001, sum(year2002) as y2002, sum(year2003) as y2003,
    sum(year2004) as y2004, sum(year2005) as y2005, sum(year2006) as y2006,
    sum(year2007) as y2007, sum(year2008) as y2008, sum(year2009) as y2009,
    sum(year2010) as y2010, sum(year2011) as y2011, sum(year2012) as y2012,
    sum(year2013) as y2013, sum(year2014) as y2014, sum(year2015) as y2015,
    sum(year2016) as y2016, sum(year2017) as y2017, sum(year2018) as y2018,
    sum(year2019) as y2019, sum(year2020) as y2020, sum(year2021) as y2021,
    sum(year2022) as y2022
    from fires;"""
    qtext2 = """select sum(area2001) as a2001, sum(area2002) as y2002, sum(area2003) as y2003,
    sum(area2004) as a2004, sum(area2005) as a2005, sum(area2006) as a2006,
    sum(area2007) as a2007, sum(area2008) as a2008, sum(area2009) as a2009,
    sum(area2010) as a2010, sum(area2011) as a2011, sum(area2012) as a2012,
    sum(area2013) as a2013, sum(area2014) as a2014, sum(area2015) as a2015,
    sum(area2016) as a2016, sum(area2017) as a2017, sum(area2018) as a2018,
    sum(area2019) as a2019, sum(area2020) as a2020, sum(area2021) as a2021,
    sum(area2022) as a2022, sum(area2023) as a2023
    from firms;"""
    qtext2_2 = """select sum(firmcount2001) as fc2001, sum(firmcount2002) as fc2002, sum(firmcount2003) as fc2003,
    sum(firmcount2004) as fc2004, sum(firmcount2005) as fc2005, sum(firmcount2006) as fc2006,
    sum(firmcount2007) as fc2007, sum(firmcount2008) as fc2008, sum(firmcount2009) as fc2009,
    sum(firmcount2010) as fc2010, sum(firmcount2011) as fc2011, sum(firmcount2012) as fc2012,
    sum(firmcount2013) as fc2013, sum(firmcount2014) as fc2014, sum(firmcount2015) as fc2015,
    sum(firmcount2016) as fc2016, sum(firmcount2017) as fc2017, sum(firmcount2018) as fc2018,
    sum(firmcount2019) as fc2019, sum(firmcount2020) as fc2020, sum(firmcount2021) as fc2021,
    sum(firmcount2022) as fc2022, sum(firmcount2023) as fc2023
    from firms;"""
    q1res = cur.execute(qtext1).fetchall()
    q2res = cur.execute(qtext2).fetchall()
    q2res2 = cur.execute(qtext2_2).fetchall()
    q1l = len(q1res)
    """for i in range(q1l):
        print(i, " - ", q1res[i])"""
    q1labels = np.arange(2001, 2023)
    q2labels = np.arange(2001, 2024)
    q1labelsstr = []
    q2labelsstr = []
    for year in q1labels:
        q1labelsstr.append(str(year))
    for year in q2labels:
        q2labelsstr.append(str(year))
    q1reslist = list(q1res[0])
    q2reslist = list(q2res[0])
    q2res2list = list(q2res2[0])
    lossmax = max(q1reslist) / 1000000
    firmsareamax = max(q2reslist) / 1000000
    firmscountmax = max(q2res2list)
    lossnorm = []
    firmsareanorm = []
    firmscountnorm = []
    for i in range(len(q1reslist)):
        temp = q1reslist[i] / 1000000 #to sq km
        q1reslist[i] = temp
        lossnorm.append(temp / lossmax * 100)
    for i in range(len(q2reslist)):
        temp = q2reslist[i] / 1000000
        q2reslist[i] = temp
        firmsareanorm.append(temp / firmsareamax * 100)
        firmscountnorm.append(q2res2list[i] / firmscountmax * 100) # no need to convert sq m to sq km
    firmsareanorm.pop()
    firmscountnorm.pop()
    # creating a view
    cur.execute("""create view if not exists lossallyears as
    select (year2001 + year2002 +  year2003 +year2004 + year2005 +year2006 + year2007 +
    year2008 + year2009 + year2010 + year2011 + year2012 + year2013 + year2014 + year2015 +
    year2016 + year2017 + year2018 + year2019 + year2020 + year2021 + year2022) as comb, id
    from fires;""")
    cur.execute("""create view if not exists firmsareaallyears as
    select (area2001 + area2002 +  area2003 + area2004 + area2005 + area2006 + area2007 +
    area2008 + area2009 + area2010 + area2011 + area2012 + area2013 + area2014 + area2015 +
    area2016 + area2017 + area2018 + area2019 + area2020 + area2021 + area2022 + area2023) as combfa, id
    from firms;""")
    cur.execute("""create view if not exists firmscountallyears as
    select (firmcount2001 + firmcount2002 +  firmcount2003 + firmcount2004 + firmcount2005 + firmcount2006 + firmcount2007 +
    firmcount2008 + firmcount2009 + firmcount2010 + firmcount2011 + firmcount2012 + firmcount2013 + firmcount2014 + firmcount2015 +
    firmcount2016 + firmcount2017 + firmcount2018 + firmcount2019 + firmcount2020 + firmcount2021 + firmcount2022 + firmcount2023)
    as combfc, id from firms;""")
    # region query
    queryforlossbyregions = """select r.region, (avg(l.comb) * 100 / 22 / f2.area) as meanratioloss,
    (avg(f.combfa) * 100 / 23 / f2.area) as meanratiofa
    from regions r
    left join lossallyears l on r.oopt_id = l.id
    left join firmsareaallyears f on r.oopt_id = f.id
    left join fires f2 on r.oopt_id  = f2.id
    group by r.region """
    queryforregionsabs = """select r.region, sum(l.comb) as totalloss, sum(f.combfa) as totalfirmsarea,
    sum(f3.combfc) as totalfirmscount,
    sum(f2.area) as forest, count (oopt_id) as oopts
    from regions r
    left join lossallyears l on r.oopt_id = l.id
    left join firmsareaallyears f on r.oopt_id = f.id
    left join fires f2 on r.oopt_id  = f2.id
    left join firmscountallyears f3 on r.oopt_id = f3.id
    group by r.region """
    queryooptrel = """select category, title, (l.comb * 100 / 22 / f.area)
    as meanratioloss, (f2.combfa * 100 / 23 / f.area) as meanratiofa
    from fires f
    join lossallyears l on f.id = l.id
    join firmsareaallyears f2 on f.id = f2.id """
    queryooptabs = """select category, title, l.comb as totalloss, f2.combfa as totalfirmsarea,
    f3.combfc as totalfirmscount, area as forest
    from fires f
    join lossallyears l on f.id = l.id
    join firmsareaallyears f2 on f.id = f2.id
    join firmscountallyears f3 on f.id = f3.id """
    qrelright = "order by meanratioloss"
    qabsright = "order by totalloss"
    if(sf1.validate_on_submit):
        print("In!")
        if(sf1.to_sort_rel.data == "fa"):
            print("Change")
            qrelright = "order by meanratiofa"
        if(sf1.direction_rel.data == "down"):
            qrelright += " desc"
            print("Change2")
        if(sf1.to_sort_abs.data == "fa"):
            qabsright = "order by totalfirmsarea"
        if(sf1.to_sort_abs.data == "fc"):
            qabsright = "order by totalfirmscount"
        if(sf1.to_sort_abs.data == "forest"):
            qabsright = "order by forest"
        if(sf1.direction_abs.data == "down"):
            qabsright += " desc"
    regionreltext = queryforlossbyregions + qrelright + ";"
    regionabstext = queryforregionsabs + qabsright + ";"
    ooptreltext = queryooptrel + qrelright + ";"
    ooptabstext = queryooptabs + qabsright + ";"
    regionsrel = cur.execute(regionreltext).fetchall()
    regionsabs = cur.execute(regionabstext).fetchall()
    ooptrel = cur.execute(ooptreltext).fetchall()
    ooptabs = cur.execute(ooptabstext).fetchall()
    for i in range(len(regionsrel)):
        #print(i, " - ", regionsrel[i])
        regionsrel[i] = (i+1,) + regionsrel[i]
    for i in range(len(regionsabs)):
        regionsabs[i] = (i+1,) + regionsabs[i]
    for i in range(len(ooptrel)):
        ooptrel[i] = (i+1,) + ooptrel[i]
    for i in range(len(ooptabs)):
        ooptabs[i] = (i+1,) + ooptabs[i]
    return render_template("statsform.html", labels1=q1labelsstr, values1=q1reslist, labels2=q2labelsstr, values2=q2reslist,
                           labels2_2=q2labelsstr, values2_2=q2res2list, labels3=q1labelsstr, values3_1=lossnorm,
                           values3_2=firmsareanorm, values3_3=firmscountnorm, rows=regionsrel, rows2=regionsabs,
                           rows3 = ooptrel, rows4 = ooptabs, form=sf1)

@app.route("/statsindividual",  methods=['GET', 'POST'])
def stats_indiv():
    con = sqlite3.connect("app.db")
    cur = con.cursor()
    firesresponse = Fires.query.all()
    if(len(firesresponse) == 0):
        return redirect(url_for('getdata'))
    firmsresponse = Firms.query.all()
    firmsresplen = len(firmsresponse)
    #print(firmsresplen)
    if(firmsresplen == 0):
        #print("none detected")
        return redirect(url_for('getfirmsdata'))
    si_form = StatsIndiv()
    selected_oopt = "Тункинский"
    selected_region = "Республика Бурятия"
    if(si_form.validate_on_submit()):
        if(si_form.oopt.data):
            selected_oopt = si_form.oopt.data
    #t1query = Fires.query
    #t1query = t1query.filter(Fires.title == selected_oopt)
    #t1queryres = t1query.all()
    t1query = "select * from fires where title like \'" + selected_oopt + "\';"
    t1qres = cur.execute(t1query).fetchall()
    notfoundmessage = ""
    if(len(t1qres) == 0): # go back to default
        selected_oopt = "Тункинский"
        notfoundmessage = "Результаты не найдены, графики представлены для Тункинского национального парка"
        t1query = "select * from fires where title like \'" + selected_oopt + "\';"
        t1qres = cur.execute(t1query).fetchall()
    t2query = "select * from firms where title like \'" + selected_oopt + "\';"
    t2qres = cur.execute(t2query).fetchall()
    print("outputting")
    print(t1qres)
    print(t2qres)
    losslist = list(t1qres[0])
    losslisttrim = losslist[3:-1]
    fafclist = list(t2qres[0])
    falist = fafclist[3::2]
    fclist = fafclist[4::2]
    for i in range(len(losslisttrim)):
        losslisttrim[i] /= 1000000
    for i in range(len(falist)):
        falist[i] /= 1000000
    print("test: ", losslisttrim)
    print("test fa : ", falist)
    print("test fc : ", fclist)
    #print(t1queryres.year2003)
    q1labels = np.arange(2001, 2023)
    q2labels = np.arange(2001, 2024)
    q1labelsstr = []
    q2labelsstr = []
    for year in q1labels:
        q1labelsstr.append(str(year))
    for year in q2labels:
        q2labelsstr.append(str(year))
    return render_template("statsform2.html", form=si_form, labels=q1labels.tolist(), values=losslisttrim,
    labels2=q2labels.tolist(), values2=falist, labels3=q2labels.tolist(), values3=fclist, nfm=notfoundmessage)