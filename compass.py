# Script for fetching information from the Compass website written by Mr Belluzzo (with some code by me added at the end) run by compassbg.py
# from datetime import datetime
# import json
import logging
# from os import environ
# import requests

from requests_toolbelt import sessions

log = logging.getLogger(__name__)

class CompassAPI:
    def __init__(self, username, password, schoolcode):
        self.s = sessions.BaseUrlSession(base_url="https://"+schoolcode+".compass.education/services/")
        self.s.post("admin.svc/AuthenticateUserCredentials",
                    json={"username": username, "password": password})
        self.user_details = self.get_personal_details().get('data')
        self.user_id = self.user_details['userRoles'][0]['userId']

    def _paged_post_all(self, url, data):
        data = data.copy()
        data.update({"page": 1, "start": 0, "limit": 100})
        result = self.s.post(url, json=data).json()
        log.info("Total records: %i" % result["d"]["total"])
        print("Total records: %i" % result["d"]["total"])
        for item in result["d"]["data"]:
            yield item

        while data["start"] + data["limit"] < result["d"]["total"]:
            data["page"] += 1 
            data["start"] += data["limit"]
            result = self.s.post(url, json=data).json()
            for item in result['d']['data']:
                yield item

    def get_user_details_blob_by_id(self, id):
        data = {"id": self.user_id, "targetUserId": id}
        return self.s.post('User.svc/GetUserDetailsBlobByUserId',
                            json=data).json()['d']
#NEEDS FIXING
    def get_personal_details(self):
        return self.s.post("mobile.svc/GetPersonalDetails").json()['d']
    

#bad code by Jun below
    def get_calender_events_by_user(self, date):
        data = {
            "userId": self.user_id,
            "homePage": True,
            "startDate": date,
            "endDate": date,
            "page": 1,
            "start": 0,
            "limit": 25
            }
        return self.s.post('Calendar.svc/GetCalendarEventsByUser', json=data).json()['d']
    
    def get_user_id(self):
        return self.user_id
    
    def get_lessons_by_instance_id(self,instanceId):
        data = {"instanceId": instanceId}
        return self.s.post('Activity.svc/GetLessonsByInstanceId',json=data).json()['d']