import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import exists

from flask import Flask, jsonify

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(engine, reflect=True)
Base.classes.keys()

Measurement = Base.classes.measurement
Station = Base.classes.station

#weather app
app = Flask(__name__)

session = Session(engine)

recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

year_ago_date = dt.date(2017, 8, 23) - dt.timedelta(days = 365)



@app.route("/")
def home():
    return (f"Surf's Up!: Hawai'i Climate API<br/>"
            f"Available Routes:<br/>"
            f"/api/v1.0/precipitation<br/>"
            f"/api/v1.0/stations<br/>"
            f"/api/v1.0/tobs<br/>"
            f"/api/v1.0/start (input YYYY-MM-DD)<br/>"
            f"/api/v1.0/start/end (input YYYY-MM-DD/YYYY-MM-DD)")

@app.route("/api/v1.0/precipitation")
def precipitation():
      
    session = Session(engine)
    
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(func.strftime('%Y-%m-%d',Measurement.date) >= year_ago_date).order_by(Measurement.date).all()
    
    precipData = []
    for result in results:
        precipDict = {result.date: result.prcp}
        precipData.append(precipDict)
        
    return jsonify(precipData)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.name).all()
    all_stations = list(np.ravel(results))
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    
    session = Session(engine)

    results = (session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == 'USC00519281')
                      .filter(Measurement.date >= year_ago_date)
                      .order_by(Measurement.date)
                      .all())

    tempData = []
    for result in results:
        tempDict = {result.date: result.tobs}
        tempData.append(tempDict)

    return jsonify(tempData)

@app.route("/api/v1.0/<start>")
def start(startDate):
    
    session = Session(engine)
    
    sel = [Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    results =  (session.query(*sel)
                       .filter(func.strftime("%Y-%m-%d", Measurement.date) >= startDate)
                       .group_by(Measurement.date)
                       .all())

    dates = []
    
    valid_entry = session.query(exists().where(Measurement.date == startDate)).scalar()
    
    if valid_entry: 
                      
        for result in results:
            date_dict = {}
            date_dict["Date"] = result[0]
            date_dict["Low Temp"] = result[1]
            date_dict["Avg Temp"] = result[2]
            date_dict["High Temp"] = result[3]
            dates.append(date_dict)
            return jsonify(dates)
    
    return jsonify({"error": f"Input date {startDate} not valid. Date range is 2010-01-01 to 2017-08-23"}), 404

@app.route("/api/v1.0/<start>/<end>")
def startEnd(startDate, endDate):
    
    session = Session(engine)
    
    sel = [Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    results =  (session.query(*sel)
                       .filter(func.strftime("%Y-%m-%d", Measurement.date) >= startDate)
                       .filter(func.strftime("%Y-%m-%d", Measurement.date) <= endDate)
                       .group_by(Measurement.date)
                       .all())

    dates = [] 

    valid_entry_start = session.query(exists().where(Measurement.date == startDate)).scalar() 
    valid_entry_end = session.query(exists().where(Measurement.date == endDate)).scalar()

    if valid_entry_start and valid_entry_end:                     
        for result in results:
            date_dict = {}
            date_dict["Date"] = result[0]
            date_dict["Low Temp"] = result[1]
            date_dict["Avg Temp"] = result[2]
            date_dict["High Temp"] = result[3]
            dates.append(date_dict)
            return jsonify(dates)
        
    if not valid_entry_start and not valid_entry_end:
    	return jsonify({"error": f"Input start date {startDate} and end date {endDate} not valid. Date range is 2010-01-01 to 2017-08-23"}), 404

    if not valid_entry_start:
    	return jsonify({"error": f"Input start date {startDate} not valid. Date range is 2010-01-01 to 2017-08-23"}), 404

    if not valid_entry_end:
    	return jsonify({"error": f"Input end date {endDate} not valid. Date range is 2010-01-01 to 2017-08-23"}), 404

if __name__ == "__main__":
    app.run(debug=True)
            