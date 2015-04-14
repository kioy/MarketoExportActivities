# -*- coding:utf-8 -*-
#!/usr/bin/env python
"""
mktoExportActivities.py invoke Marketo REST API with Python script  
Usage: mktoExportActivities.py -i <Marketo Instance URL> -o <output> -h

Options:
  -i --instance <instance>      Marketo Instance URL such as https://app-abj.marketo.com
  -o --output <filename>		Output filename
  -h                            this help

Mail bug reports and suggestion to : Yukio Y <unknot304 AT gmail.com>
"""
import sys, os, errno  
import argparse
import csv
import getpass    

import time
import datetime
import json
import httplib2
import logging
import pytz
from datetime import datetime

 
# Reference:
# Marketo REST API: http://developers.marketo.com/documentation/rest/


# -------
# Base class for all the rest service
#
#    mkto_instance: eg. http://123-abc-456.mktorest.com
#    grant_type: client_credentials
#    client_id: eg. 3d96eaef-f611-42a0-967f-002fasdweeea
#    client_secret: eg. i8s6RRq1LhPlMyATEKfLW2300CMbwzrF
#
class MarketoClient:
    def __init__(self, mkto_instance, grant_type, client_id, client_secret):
        self.identity_url = mkto_instance + '/identity'
        self.endpoint_url = mkto_instance
        self.access_token_url = self.identity_url + '/oauth/token?grant_type=' + grant_type + '&client_id=' + client_id + '&client_secret=' + client_secret

        self.request_headers = {'Accept': 'application/json',
                                'Content-Type': 'application/json; charset=UTF-8'
                                }
        self.http_client = httplib2.Http()

        # send request
        response, content = self.http_client.request(self.access_token_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        self.access_token = data ['access_token']
        # print >> sys.stderr, "Access Token: " + self.access_token


    # get lead by id
    def getLeadRaw(self, id, fields):
        leads_url = self.endpoint_url + '/rest/v1/lead/' + id + '.json?access_token=' + self.access_token
        leads_url = leads_url + '&files=' + fields
        response, content = self.http_client.request(leads_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        # print >> sys.stderr, data
        return data

    # get leads by filter
    def getLeadsRaw(self, filter_type, filter_values, fields):
        leads_url = self.endpoint_url + '/rest/v1/leads.json?access_token=' + self.access_token
        leads_url = leads_url + '&filterType=' + filter_type + '&filterValues=' + filter_values + '&fields=' + fields
        response, content = self.http_client.request(leads_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        # print >> sys.stderr, data
        return data

    # get Paging Token, since may be formatted as "2015-04-10"
    def getPagingToken(self, since):
        leads_url = self.endpoint_url + '/rest/v1/activities/pagingtoken.json?access_token=' + self.access_token
        leads_url = leads_url + '&sinceDatetime=' + since
        response, content = self.http_client.request(leads_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        pageToken = data ['nextPageToken']
        # print >> sys.stderr, data
        return pageToken

    # get lead changes
    def getLeadChangesRaw(self, token, fields):
        leads_url = self.endpoint_url + '/rest/v1/activities/leadchanges.json?access_token=' + self.access_token
        leads_url = leads_url + '&nextPageToken=' + token + '&fields=' + fields
        response, content = self.http_client.request(leads_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        # print >> sys.stderr, data
        return data

    # get lead activities. activity_type_ids may take Click Link in Email(11), Web Visit(1) and Click Link on a page(3)
    def getLeadActivitiesRaw(self, token, activity_type_ids):
        leads_url = self.endpoint_url + '/rest/v1/activities.json?access_token=' + self.access_token
        #leads_url = leads_url + '&nextPageToken=' + token + '&activityTypeIds=1&activityTypeIds=11&activityTypeIds=3'
        leads_url = leads_url + '&nextPageToken=' + token + '&activityTypeIds=' + activity_type_ids
        response, content = self.http_client.request(leads_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        # print >> sys.stderr, data
        return data

    # get activity Types
    def getActivityTypesRaw(self):
        leads_url = self.endpoint_url + '/rest/v1/activities/types.json?access_token=' + self.access_token
        response, content = self.http_client.request(leads_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        # print >> sys.stderr, data
        return data
        
    def updateAccessToken(self):
        response, content = self.http_client.request(self.access_token_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        self.access_token = data ['access_token']
        # print >> sys.stderr, self.access_token
        # timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d %H:%M:%S')

    def enableDebug(self):
        httplib2.debuglevel = 1

 

if __name__ == "__main__": 
    desc = u'{0} [Options]\nDetailed options -h or --help'.format(__file__)
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-i', '--instance',
        type = str,
        dest = 'mkto_instance',
        required = True,
        help = 'Marketo REST API Instance URL such as https://123-XYZ-456.mktorest.com'
	)
    parser.add_argument(
        '-d', '--id',
        type = str,
        dest = 'mkto_client_id',
        required = True,
        help = 'Marketo LaunchPoint Client Id: eg. 3d96eaef-f611-42a0-967f-00aeeee7e0ea'
	)
    parser.add_argument(
        '-s', '--secret',
        type = str,
        dest = 'mkto_client_secret',
        required = True,
        help = 'Marketo LaunchPoint Client Secret: eg. i8s6RRq1LhPlMyATEKfLWl1255bwzrF'
	)
    parser.add_argument(
        '-o', '--output',
        type = str,
        dest = 'output_file',
        required = False,
        help = 'Output file name'
	)
    parser.add_argument(
        '-c', '--since',
        type = str,
        dest = 'mkto_date',
        required = True,
        help = 'sinceDate time for calling Get Paging Token: eg. 2015-01-31'
	)
    parser.add_argument(
        '-g', '--debug',
        action='store_true',
        dest = 'debug',
        default = False,
        required = False,
        help = 'Pring debugging information'
	)
    parser.add_argument(
        '-j', '--not-use-jst',
        action='store_true',
        dest = 'not_jst',
        default = False,
        required = False,
        help = 'Pring debugging information'
	)
    
    args = parser.parse_args()
    
    # initiate Marketo ReST API
    mktoClient = MarketoClient(args.mkto_instance, 'client_credentials', args.mkto_client_id, args.mkto_client_secret)
    
    # enable debug information
    if args.debug:
        mktoClient.enableDebug()

    # file handler
    if args.output_file:
        fh = open(args.output_file, 'w')
    else:
        fh = sys.stdout

    mywriter = csv.writer(fh, delimiter = ',')


    # get web visits, click link activities
    # token = mktoClient.getPagingToken(args.mkto_date)
    # moreResult=True
    # while moreResult:
    #     raw_data = mktoClient.getLeadActivitiesRaw(token, '10,11,12,13')
    #     moreResult = raw_data ['moreResult']
    #     # parse result section
    #     raw_data_result = raw_data ['result']
    #     csv_raw = list()
    #     for result in raw_data_result:
    #         csv_raw.append(result ['id'])
    #         csv_raw.append(result ['activityTypeId'])
    #         csv_raw.append(result ['leadId'])
    #         csv_raw.append(result ['activityDate'])
    #     print >> sys.stderr, "Activity: " + json.dumps(raw_data, indent=4)



    mywriter.writerow(["activityDate", "leadId", "id", "activityType", "leadScore", "lifecycleStatus"])

    # dictionaly for the leadStatus and lifecycleStatus for each leads
    lastLeadScore = {}
    lastLifecycleStatus = {}

    # get value change activities
    token = mktoClient.getPagingToken(args.mkto_date)
    moreResult=True
    while moreResult:
        raw_data = mktoClient.getLeadChangesRaw(token,"leadScore,lifecycleStatus")
        moreResult = raw_data ['moreResult']
        # print >> sys.stderr, "Activity: " + json.dumps(raw_data, indent=4)

        # parse result section
        raw_data_result = raw_data ['result']
        for result in raw_data_result:
            csv_row = []

            # convert datetime (CST) to JST
            activityDate = unicode(result ['activityDate']).encode('utf-8')
            activityDate = activityDate.replace("T", " ")
            activityDate = activityDate.replace("Z", "")
            if args.not_jst == False: # use JST
                jstActivityDate = datetime.strptime(activityDate, '%Y-%m-%d %H:%M:%S')
                jstActivityDate = pytz.utc.localize(jstActivityDate)
                jstActivityDate = jstActivityDate.astimezone(pytz.timezone('Asia/Tokyo'))
                activityDate = jstActivityDate.strftime('%Y-%m-%d %H:%M:%S')

            csv_row.append(activityDate)

            leadId = result ['leadId']
            csv_row.append(leadId)
            csv_row.append(result ['id'])

            # if this activity explains "Created", leadScore and lifecycleStatus is empty
            if  result ['activityTypeId'] == 12:
                csv_row.append("Created")
                csv_row.append(0)
                csv_row.append("")
                # store the latest leadScore and lifecycleStatus for this lead
                lastLeadScore [leadId] = 0
                lastLifecycleStatus [leadId] = ""
                # write row into csv 
                mywriter.writerow(csv_row)
                continue

            # if this activity explains "Data Value Cahnged", added leadScore and lifecycleStatus 
            
            fields = result ['fields']
            csv_row.append("Data Value Changed")
            for field in fields:
                if field ['name'] == "leadScore":
                    leadScore = int(unicode(field['newValue']).encode('utf-8'))
                    csv_row.append(leadScore)
                    csv_row.append(lastLifecycleStatus.get(leadId))
                    lastLeadScore[leadId] = leadScore
                elif field ['name'] == "lifecycleStatus":
                    leadLifecycleStatus = unicode(field['newValue']).encode('utf-8')
                    csv_row.append(lastLeadScore.get(leadId))
                    csv_row.append(leadLifecycleStatus)
                    lastLifecycleStatus[leadId] = leadLifecycleStatus
                else:
                    csv_row.append(lastLeadScore.get(leadId))
                    csv_row.append(lastLifecycleStatus.get(leadId))

            # write row into csv 
            mywriter.writerow(csv_row)

    if fh is not sys.stdout:
        fh.close()

    # test methods
    # mktoClient.updateAccessToken()
    # mktoClient.getLeadRaw("101099", "email")
    # mktoClient.getLeadsRaw("id", "101095", "id")
    # raw_data = mktoClient.getActivityTypesRaw()
    # print >> sys.stderr, "Activity Types: " + json.dumps(raw_data, indent=4)


