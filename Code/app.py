# app.py file to create flask app
# Jonathan Surgeon 6/7/21

#import dependecies
import numpy as np
from numpy.lib.function_base import _msort_dispatcher

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify
#####################################
# database setup
#####################################
# create engine to hawaii.sqlite
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
Base.prepare(engine,reflect=True)
# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station


#####################################
# flask setup
#####################################
app = Flask(__name__)

#####################################
# flask routes
#####################################
# define what the application will do when it hits the index route
@app.route('/')
def home():
    print("Server has recieved request for 'Home' page")
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>You can search the Database from /api/v1.0/ by adding a start date, or a start and end date with a '/' in between."
        f"<br/>&emsp;&emsp;Example: to search September 29, 2011 through October 29, 2012. /api/v1.0/2011-11-29/2012-10-29"
        )
# define what the app will do when it hits /api.v1.0/precipitation
@app.route('/api/v1.0/precipitation')
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # get most recent date in dataset and the date from a year prior
    recent_date = session.query(measurement.date).order_by(measurement.date.desc()).limit(1).all()
    query_date = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    
    # query last year of precipitation data
    past_year = session.query(measurement.date, measurement.prcp).filter(measurement.date >= query_date).all()
    
    # close session
    session.close()
    
    # convert query results (past_year) into dictionary, using date as the key and precipitation as the value
    all_precips = []
    
    for date, prcp in past_year:
        precip_dict = {}
        precip_dict[date] = prcp
        all_precips.append(precip_dict)

    #return jsonified list of dicitionary items (all_precips)
    return jsonify(all_precips)

# define app route /api/v1.0/stations to show list of all 9 stations
@app.route("/api/v1.0/stations")
def stations():
    
    # create our session (link) from Python to the DB
    session = Session(engine)

    # query database for station ids and names
    stations = session.query(station.station, station.name).all()

    # close session
    session.close()

    # return jsonified stations
    return jsonify(stations)

# define app route /api/v1.0/tobs
@app.route("/api/v1.0/tobs")
def tobs():

    # create our session (link) from Python to the DB
    session = Session(engine)

    # query database to find the most active station for the last year
    result = session.query(station.station,func.count(station.station)).filter(station.station==measurement.station).\
        group_by(station.station).order_by(func.count(station.station).desc()).limit(1).all()

    most_active = result[0][0]

    #query the database to get the most recent date in dataset and the date from a year prior
    recent_date = session.query(measurement.date).order_by(measurement.date.desc()).limit(1).all()
    query_date = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    # query the database for the last 12 months of temperature observation data for the most active station
    past_year_temps = session.query(measurement.date, measurement.tobs).filter(measurement.date >= query_date).\
        filter(measurement.station==most_active).all()
    
    # close session
    session.close()

     # convert query results (past_year_temps) into dictionary, using date as the key and tobs as the value
    all_tobs = []
    for date, tobs in past_year_temps:
        tobs_dict = {}
        tobs_dict[date] = tobs
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)

# define app route /api/v1.0/<start>
@app.route("/api/v1.0/<start>")
def search_route(start):
    """Fetch minimum, average, and maximum termperature for all dates greater than and equal to given <start>"""

    # create our session (link) from Python to the DB
    session = Session(engine)

    # try and except block to catch strings in the wrong format
    format = "%Y-%m-%d"
    try:
        dt.datetime.strptime(start,format)
    except ValueError:
        return ("The date given is not in the correct format, it should be YYYY-MM-DD.<br/><br/>TRY AGAIN"), 404

    # query database filtering with given date (start), return tempterature mins, max, and average for the date range
    sel = [
    func.avg(measurement.tobs),
    func.min(measurement.tobs),
    func.max(measurement.tobs)
    ]
    result = session.query(*sel).filter(measurement.date >= start).all()

    # close session
    session.close()

    # return values
    return jsonify({"Minimum Temp": result[0][1]},
        {"Maximum Temp": result[0][2]},
        {"Average Temp": round(result[0][0],2)}    
    )

# define app route /api/v1.0/<start>/<end>
@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
    """Fetch minimum, average, and maximum termperature for all dates between start and end, inclusive"""

    # create our session (link) from Python to the DB
    session = Session(engine)

    # try and except block to catch strings in the wrong format
    format = "%Y-%m-%d"
    try:
        dt.datetime.strptime(start,format)
        dt.datetime.strptime(end,format)
    except ValueError:
        return ("The either one or both of the dates given are not in the correct format, they should be formatted as YYYY-MM-DD.<br/><br/>TRY AGAIN"), 404

    # check to see if start and end are in proper logical order (ie start < end). If not, rearrange 
    if(start > end):
        temp = start
        start = end
        end = temp
    
    # query database filtering with given dates (start & end), return tempterature mins, max, and average for the date range
    sel = [
    func.avg(measurement.tobs),
    func.min(measurement.tobs),
    func.max(measurement.tobs)
    ]
    result = session.query(*sel).filter(measurement.date >= start).filter(measurement.date <= end).all()

    # close session
    session.close()

    # return values
    return jsonify({"Minimum Temp": result[0][1]},
        {"Maximum Temp": result[0][2]},
        {"Average Temp": round(result[0][0],2)}    
    )

if __name__ == "__main__":
    app.run(debug=True)
