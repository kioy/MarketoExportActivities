# -*- coding:utf-8 -*-
#!/usr/bin/env python
"""
mktoExportActivities.py invoke Marketo REST API with Python script  
Usage: mktoExportActivities.py -i <Marketo Instance URL> -o <output> -h

Options:
  -h                                this help
  -i --instance <instance>          Marketo Instance URL such as https://app-abj.marketo.com
  -o --output <filename>	    Output filename
  -d --id <client id>               Marketo LaunchPoint Client Id: eg. 3d96eaef-f611-42a0-967f-00aeeee7e0ea
  -s --secret <client secret>       Marketo LaunchPoint Client Secret: eg. i8s6RRq1LhPlMyATEKfLWl1255bwzrF
  -c --since <date>                 Since Date time for calling Get Paging Token: eg. 2015-01-31
  -g --debug                        Pring debugging information
  -j --not-use-jst                  Change TimeZone for Activity Date field. Default is JST.
  -f --change-data-field <fields>   Specify comma separated API fields name such as leadScore for extracting Data Value Changed activities. default: "leadScore,lifecycleStatus"
  -w --add-webvisit-activity        Adding Web Visit activity. It might be a cause of slowdown.
  -m --add-mail-activity            Adding mail open/click activity. It might be a cause of slowdown.
    
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
        help = 'Change TimeZone for Activity Date field. Default is JST.'
	)
    parser.add_argument(
        '-f', '--change-data-fields',
        type = str,
        dest = 'change_data_fields',
        required = False,
        help = 'Specify comma separated API fields name such as leadScore for extracting Data Value Changed activities. default: leadScore,lifecycleStatus'
	)
    parser.add_argument(
        '-w', '--add-webvisit-activity',
        action = 'store_true',
        dest = 'web_activity',
        default = False,
        required = False,
        help = 'Adding Web Visit activity. It might be a cause of slowdown.'
	)
    parser.add_argument(
        '-m', '--add-mail-activity',
        action = 'store_true',
        dest = 'mail_activity',
        default = False,
        required = False,
        help = 'Adding mail open/click activity. It might be a cause of slowdown.'
	)
    
    args = parser.parse_args()

    # enable debug information
    if args.debug:
        mktoClient.enableDebug()

    # initiate file handler, selecting file output or stdout according to command arguments
    if args.output_file:
        fh = open(args.output_file, 'w')
    else:
        fh = sys.stdout
    mywriter = csv.writer(fh, delimiter = ',')


    # prepairing activityTypeName
    # Currently, this script supports the following activityType for extracting activity.
    activityTypeNameDict = {1:'Visit Webpage', 3:'Click Link', 10:'Open Email', 11:'Click Email', 12:'New Lead', 13:'Change Data Value'}
    default_activity_id = "12,13"

    # preparing csv headers according to command arguments. if user set -w option, we add "page" and "link"
    default_header = ["id", "activityDate", "activityTypeId", "activityTypeName", "leadId", "leadScore", "lifecycleStatus"]
    if args.change_data_fields:
        tracking_fields = args.change_data_fields.split(",")
        default_header.extend(tracking_fields)

    if args.mail_activity:
        deafult_header.extend(["mail","linkInMail"])
        default_activity_id = default_activity_id + ",10,11"

    if args.web_activity:
        default_header.extend(["page","link"])
        default_activity_id = default_activity_id + ",1,3"

    # write header to fh
    mywriter.writerow(default_header)


    # initiate dictionalies for storing latest leadStatus, lifecycleStatus and specified fields through command argument for each leads
    last_leadScore = {}
    last_lifecycleStatus = {}
    last_custom_fields = {}
    for field in tracking_fields:
        last_custom_fields[field].append({})

    
    #
    # initiate Marketo ReST API
    mktoClient = MarketoClient(args.mkto_instance, 'client_credentials', args.mkto_client_id, args.mkto_client_secret)
    

    # get value change activities
    token = mktoClient.getPagingToken(args.mkto_date)
    moreResult=True
    while moreResult:
        raw_data = mktoClient.getLeadActivitiesRaw(token, default_activity_id)
        moreResult = raw_data ['moreResult']
        # print >> sys.stderr, "Activity: " + json.dumps(raw_data, indent=4)
        # parse result section
        raw_data_result = raw_data ['result']
        csv_raw = list()
        for result in raw_data_result:
            # id
            csv_raw.append(result ['id'])

            # activityDate
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

            # activityTypeId
            activityTypeId = result ['activityTypeId']
            csv_row.append(activityTypeId)

            # activityTypeName
            csv_row.append(activityTypeNameDict[activity_type_id])
            
            # leadId
            leadId = result ['leadId']
            csv_row.append(leadId)

            # 12:Created
            # leadScore, lifecycleStatus and other custom fields is empty, because of lead is just created.
            if  activityTypeId == 12:
                # leadScore
                csv_row.append(0)
                # lifecycleStatus
                csv_row.append("")
                # store the latest leadScore and lifecycleStatus for this lead
                last_leadScore [leadId] = 0
                last_lifecycleStatus [leadId] = ""

                for field in tracking_fields:
                    csv_row.append("")
                    # is this correct? YY
                    last_custom_fields [field][leadId] = ""

                if args.mail_activity:
                    csv_row.append("")
                    csv_row.append("")

                if args.web_activity:
                    csv_row.append("")
                    csv_row.append("")

                # write row into csv 
                mywriter.writerow(csv_row)
                continue

            # 
            # 13: Data Value Changed
            # leadScore, lifecycleStatus and other custom fields is updated!
            if  activityTypeId == 13:
                fields = result ['fields']
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


