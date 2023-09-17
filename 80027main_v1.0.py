# https://openskynetwork.github.io/opensky-api/rest.html
# https://opensky-network.org/api/states/all?time=1458564121&icao24=3c6444
# https://www.findlatitudeandlongitude.com/l/Boulder+County%2C+Colorado%2C+USA/5766660/

# icao24: str - ICAO24 address of the transmitter in hex string representation.
# callsign: str - callsign of the vehicle. Can be None if no callsign has been received.
# origin_country: str - inferred through the ICAO24 address.
# time_position: int - seconds since epoch of last position report. Can be None if there was no position report received by OpenSky within 15s before.
# last_contact: int - seconds since epoch of last received message from this transponder.
# longitude: float - in ellipsoidal coordinates (WGS-84) and degrees. Can be None.
# latitude: float - in ellipsoidal coordinates (WGS-84) and degrees. Can be None.
# geo_altitude: float - geometric altitude in meters. Can be None.
# on_ground: bool - true if aircraft is on ground (sends ADS-B surface position reports).
# velocity: float - over ground in m/s. Can be None if information not present.
# true_track: float - in decimal degrees (0 is north). Can be None if information not present.
# vertical_rate: float - in m/s, incline is positive, decline negative. Can be None if information not present.
# sensors: list [int] - serial numbers of sensors which received messages from the vehicle within the validity period of this state vector. Can be None if no filtering for sensor has been requested.
# baro_altitude: float - barometric altitude in meters. Can be None.
# squawk: str - transponder code aka Squawk. Can be None.
# spi: bool - special purpose indicator.
# position_source: int - origin of this state’s position: 0 = ADS-B, 1 = ASTERIX, 2 = MLAT, 3 = FLARM
# category: int - aircraft category: 0 = No information at all, 1 = No ADS-B Emitter Category Information, 2 = Light (< 15500 lbs), 3 = Small (15500 to 75000 lbs), 4 = Large (75000 to 300000 lbs), 5 = High Vortex Large (aircraft such as B-757), 6 = Heavy (> 300000 lbs), 7 = High Performance (> 5g acceleration and 400 kts), 8 = Rotorcraft, 9 = Glider / sailplane, 10 = Lighter-than-air, 11 = Parachutist / Skydiver, 12 = Ultralight / hang-glider / paraglider, 13 = Reserved, 14 = Unmanned Aerial Vehicle, 15 = Space / Trans-atmospheric vehicle, 16 = Surface Vehicle – Emergency Vehicle, 17 = Surface Vehicle – Service Vehicle, 18 = Point Obstacle (includes tethered balloons), 19 = Cluster Obstacle, 20 = Line Obstacle.

import datetime
import time
import array
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from FlightDistance import *

# assigned regular string date
start_date_time = datetime.datetime(2023, 9, 16, 22, 00)
end_date_time = datetime.datetime(2023, 9, 17, 21, 59)
starttime = int(time.mktime(start_date_time.timetuple()))
endtime = int(time.mktime(end_date_time.timetuple()))

now = int(time.time())

from opensky_api import OpenSkyApi
api = OpenSkyApi()

print("Current in airspace:")
states = api.get_states(bbox=(39.898345, 39.929616, -105.167308, -105.094004))
for s in states.states:
	print("(%r, %r, %r, %r, %r, %r, %r)" % (s.icao24, s.callsign, s.longitude, s.latitude, s.geo_altitude, s.baro_altitude, s.velocity))

homela = 39.+0./60+0./3600. #  reference longitude (adjust 0s in minutes, seconds)
homelo = -105.-0./60-0./3600. # reference longitude (adjust 0s in minutes, seconds)

arrivals = api.get_arrivals_by_airport("KBJC", starttime, endtime)
departures = api.get_departures_by_airport("KBJC", starttime, endtime)
print("RMMA Arrivals:")
if arrivals is not None:
    for flight in arrivals:
        print(datetime.datetime.fromtimestamp(flight.firstSeen), flight.icao24)
        # track = api.get_track_by_aircraft(flight.icao24,flight.firstSeen+10)
        # print(track)
        # traj = np.array(track.path)
print("RMMA Departures:")
if departures is not None:
    for flight in departures:
        print(datetime.datetime.fromtimestamp(flight.firstSeen), flight.icao24)
        track = api.get_track_by_aircraft(flight.icao24,flight.firstSeen+10)
        print(track)
        traj = np.array(track.path)

        plt.figure(figsize=(12, 12)) 

        fs = str(datetime.datetime.fromtimestamp(flight.firstSeen))

        plt.subplot(2, 2, 1)
        plt.plot(traj[:,2], traj[:,1])
        plt.gca().set_aspect('equal')
        plt.title(flight.icao24+" "+flight.callsign+" "+fs)
        plt.xlabel("longitude [deg]")
        plt.ylabel("latitude [deg]")
        plt.grid(True, which="both", ls="-")

        dateconv = np.vectorize(datetime.datetime.fromtimestamp)
        t = dateconv(traj[:,0])
         
        plt.subplot(2, 2, 2)
        plt.plot(t, traj[:,3])
        plt.title(flight.icao24+" "+flight.callsign+" "+fs)
        plt.xlabel("local time [DD HH:MM]")
        plt.ylabel("barometric altitude [m]")
        plt.xticks( rotation=25 )

        projdist=np.array([])
        for i,item in enumerate(traj):
            projdist=np.append(projdist,projectedDistance(traj[i,1], traj[i,2]))

        plt.subplot(2, 2, 3)
        plt.plot(t, projdist[:])
        plt.title("Ref. (λ,φ) = "+f"({homelo:{3}.{7}}, {homela:{2}.{6}})")
        plt.xlabel("local time [DD HH:MM]")
        plt.ylabel("projected distance [mi]")
        plt.xticks( rotation=25 )

        losdist=np.array([])
        for i,item in enumerate(traj):
            losdist=np.append(losdist,lineofsightDistance(traj[i,1], traj[i,2], traj[i,3]))

        plt.subplot(2, 2, 4)
        plt.plot(t, losdist[:])
        plt.title("Ref. (λ,φ) = "+f"({homelo:{3}.{7}}, {homela:{2}.{6}})")
        plt.xlabel("local time [DD HH:MM]")
        plt.ylabel("line of sight distance [ft]")
        plt.yscale("log")
        plt.grid(True, which="both", ls="-")
        plt.xticks( rotation=25 )

        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4,hspace=0.4)
        # plt.rcParams['figure.constrained_layout.use'] = True
         
        plt.show(block=False)
        plt.savefig('/Users/brian/Documents/github/flight/results/'+flight.icao24+'_'+fs+'.png') 
