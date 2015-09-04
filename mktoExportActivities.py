#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
mktoExportActivities.py: Extracting Leads Activities via Marketo REST API
Usage: mktoExportActivities.py <options>

Options:
  -h                                this help
  -i --instance <instance>          Marketo Instance URL such as https://app-abj.marketo.com
  -o --output <filename>	    Output filename
  -d --id <client id>               Marketo LaunchPoint Client Id: eg. 3d96eaef-f611-42a0-967f-00aeeee7e0ea
  -s --secret <client secret>       Marketo LaunchPoint Client Secret: eg. i8s6RRq1LhPlMyATEKfLWl1255bwzrF
  -c --since <date>                 Since Date time for calling Get Paging Token: eg. 2015-01-31
  -g --debug                        Pring debugging information
  -j --not-use-jst                  Change TimeZone for Activity Date field. Default is JST.
  -f --change-data-field <fields>   Specify comma separated 'UI' fields name such as 'Behavior Score' for extracting from 'Data Value Changed' activities. default fields: 'Lead Score'
  -w --add-webvisit-activity        Adding Web Visit activity. It might be a cause of slowdown.
  -m --add-mail-activity            Adding mail open/click activity. It might be a cause of slowdown.
    
Mail bug reports and suggestion to : Yukio Y <unknot304 AT gmail.com>

Please refer Market REST API documents: http://docs.marketo.com
Search article with "Create a Custom Service for Use with ReST API"
"""

import sys, os, errno  
import argparse
import csv
import getpass    

import time
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
        self.debug = False

        # send request
        response, content = self.http_client.request(self.access_token_url, 'GET', '', self.request_headers)
        data = json.loads(content)
        self.access_token = data ['access_token']
        # print >> sys.stderr, "Access Token: " + self.access_token
        # print >> sys.stderr, "Access Token Expired in", data ['expires_in']


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
        print >> sys.stderr, "Access Token Expired in", data ['expires_in']
        # timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d %H:%M:%S')

    def enableDebug(self):
        httplib2.debuglevel = 1
        self.debug = True

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description='Extract Lead Activities via Marketo API')
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
        help = 'Specify comma separated "UI" fields name such as "Behavior Score" for extracting from "Data Value Changed" activities. default fields: "Lead Score"'
	)
    parser.add_argument(
        '-m', '--add-mail-activity',
        action = 'store_true',
        dest = 'mail_activity',
        default = False,
        required = False,
        help = 'Adding mail open/click activity. It might be a cause of slowdown.'
	)
    parser.add_argument(
        '-w', '--add-webvisit-activity',
        action = 'store_true',
        dest = 'web_activity',
        default = False,
        required = False,
        help = 'Adding Web Visit activity. It might be a cause of slowdown.'
	)
    
    args = parser.parse_args()

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
    default_header = ["Activity Id", "Activity Date", "Activity Type Id", "Activity Type Name", "Lead Id"]

    tracking_fields = ["Lead Score"]
    default_header.extend(tracking_fields)

    if args.change_data_fields:
        change_data_fields =  args.change_data_fields.split(",")
        for field in change_data_fields:
            tracking_fields.append(field)
            default_header.append(field)

    if args.mail_activity:
        default_header.extend(["Mail","Link in Mail"])
        default_activity_id = default_activity_id + ",10,11"

    if args.web_activity:
        default_header.extend(["Web Page","Link on Page","Query Parameters"])
        default_activity_id = default_activity_id + ",1,3"

    # write header to fh
    mywriter.writerow(default_header)


    # initiate dictionalies for storing latest leadStatus, lifecycleStatus and specified fields through command argument for each leads
    last_custom_fields = {}
    for field in tracking_fields:
        last_custom_fields[field] = {}

    
    #
    # initiate Marketo ReST API
    mktoClient = MarketoClient(args.mkto_instance, 'client_credentials', args.mkto_client_id, args.mkto_client_secret)
    
    # enable debug information
    if args.debug:
        mktoClient.enableDebug()


    # get value change activities
    token = mktoClient.getPagingToken(args.mkto_date)
    moreResult=True
    while moreResult:
        raw_data = mktoClient.getLeadActivitiesRaw(token, default_activity_id)
        if args.debug:
            print >> sys.stderr, "Activity: " + json.dumps(raw_data, indent=4)
        success = raw_data ['success']
        if success == False:
            errors = raw_data ['errors']
            error_code = errors [0] ['code']
            error_message = errors[0] ['message']
            if error_code == "602":
                if args.debug:
                    print >> sys.stderr, "Access Token has been expired. Now updating..."
                mktoClient.updateAccessToken()
                continue
            else:
                print >> sys.stderr, "Error:"
                print >> sys.stderr, "REST API Error Code: ", error_code
                print >> sys.stderr, "Message: ", error_message
                if fh is not sys.stdout:
                    fh.close()
                sys.exit(1)

        token = raw_data ['nextPageToken']
        moreResult = raw_data ['moreResult']

        if args.debug:
            print >> sys.stderr, "Activity: " + json.dumps(raw_data, indent=4)

        #check if there is result field
        if raw_data.has_key('result') == False:
                print >> sys.stderr, "Error:"
                print >> sys.stderr, "There is no specific activities."
                if fh is not sys.stdout:
                    fh.close()
                sys.exit(1)

        raw_data_result = raw_data ['result']
        for result in raw_data_result:
            csv_row = []
            # id
            csv_row.append(result ['id'])

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
            csv_row.append(activityTypeNameDict[activityTypeId])
            
            # leadId
            leadId = result ['leadId']
            csv_row.append(leadId)

            # 12:Created
            # leadScore, lifecycleStatus and other custom fields is empty, because of lead is just created.
            #
            # JSON results example:
            # 
            # {
            #   "id": 303290,
            #   "leadId": 101093,
            #   "activityDate": "2015-04-09T05:34:40Z",
            #   "activityTypeId": 12,
            #   "primaryAttributeValueId": 101093,
            #   "attributes": [
            #     {
            #       "name": "Created Date",
            #       "value": "2015-04-09"
            #     },
            #     {
            #       "name": "Form Name",
            #       "value": "YY_Program.YY_Form"
            #     },
            #     {
            #       "name": "Source Type",
            #       "value": "Web form fillout"
            #     }
            #   ]
            # }
            if  activityTypeId == 12:
                for field in tracking_fields:
                    csv_row.append("")
                    # is this correct... Lead Score should be integer but it will be initialized as ""
                    last_custom_fields [field][leadId] = ""

                # adding empty field value for mail related column
                if args.mail_activity:
                    csv_row.append("")
                    csv_row.append("")

                # adding empty field value for web related column
                if args.web_activity:
                    csv_row.append("")
                    csv_row.append("")

                # write row into csv 
                mywriter.writerow(csv_row)
                continue

            # 
            # 13: Change Data Value
            # Lead Score and other standard/custom fields are updated!
            #
            # JSON results example:
            # {
            #  "id": 303306,
            #  "leadId": 101093,
            #  "activityDate": "2015-04-09T09:51:00Z",
            #  "activityTypeId": 13,
            #  "primaryAttributeValueId": 641,
            #  "primaryAttributeValue": "YY_Field_1",
            #  "attributes": [
            #   {
            #     "name": "New Value",
            #     "value": "marketo"
            #   },
            #   {
            #     "name": "Old Value",
            #     "value": "coverity"
            #   },
            #   {
            #     "name": "Reason",
            #     "value": "Form fill-out, URL: http://yy.marketo.com/lp/yy.html"
            #   },
            #   {
            #     "name": "Source",
            #     "value": "Web form fillout"
            #   }
            #  ]
            # }
            if  activityTypeId == 13:
                activity_field = unicode(result ['primaryAttributeValue']).encode('utf-8')
                if activity_field in tracking_fields:
                    for field in tracking_fields:
                        if field == activity_field:
                            attributes = result ['attributes']
                            for attribute in attributes:
                                if attribute ['name'] == "New Value":
                                    value = unicode(attribute ['value']).encode('utf-8')
                                    csv_row.append(value)
                                    # store current value
                                    last_custom_fields [field][leadId] = value
                                    break
                        else:
                            # if it is not matched, adding latest value or empty
                            csv_row.append(last_custom_fields [field].get(leadId))
                else:
                    # this activity is not related to tracking_fields, so we skip this activity without writerow
                    continue

                # adding empty field value for mail related column
                if args.mail_activity:
                    csv_row.append("")
                    csv_row.append("")

                # adding empty field value for web related column
                if args.web_activity:
                    csv_row.append("")
                    csv_row.append("")

                # write row into csv 
                mywriter.writerow(csv_row)
                continue

            # 
            # 10: Open Mail
            # JSON results example:
            # {
            #  "id": 303306,
            #  "leadId": 101093,
            #  "activityDate": "2015-04-09T09:51:00Z",
            #  "activityTypeId": 10,
            #  "primaryAttributeValueId": 5,
            #  "primaryAttributeValue": "RestAPITester.01_Mail",
            #  "attributes": [
            #   {
            #     "name": "Device",
            #     "value": "unknown"
            #   },
            #   {
            #     "name": "Is Mobile Device",
            #     "value": false
            #   },
            #   {
            #     "name": "Platform",
            #     "value": "unknown"
            #   },
            #   {
            #     "name": "User Agent",
            #     "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko)"
            #   }
            #  ]
            # }
            if  activityTypeId == 10:
                for field in tracking_fields:
                    csv_row.append(last_custom_fields [field].get(leadId))

                # Mail
                mail =  unicode(result ['primaryAttributeValue']).encode('utf-8')
                csv_row.append(mail)
                # Click in Mail
                csv_row.append("")

                # adding empty field value for web related column
                if args.web_activity:
                    csv_row.append("")
                    csv_row.append("")

                # write row into csv 
                mywriter.writerow(csv_row)
                continue
                
            # 
            # 11: Click in Mail
            # JSON results example:
            # {
            #  "id": 303306,
            #  "leadId": 101093,
            #  "activityDate": "2015-04-09T09:51:00Z",
            #  "activityTypeId": 10,
            #  "primaryAttributeValueId": 5,
            #  "primaryAttributeValue": "RestAPITester.01_Mail",
            #  "attributes": [
            #   {
            #     "name": "Device",
            #     "value": "unknown"
            #   },
            #   {
            #     "name": "Is Mobile Device",
            #     "value": false
            #   },
            #   {
            #     "name": "Link",
            #     "value": "http://unknot304.blogspot.jp/2015/02/munchkin-tag.html"
            #   },
            #   {
            #     "name": "Platform",
            #     "value": "unknown"
            #   },
            #   {
            #     "name": "User Agent",
            #     "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko)"
            #   }
            #  ]
            # }
            if  activityTypeId == 11:
                for field in tracking_fields:
                    csv_row.append(last_custom_fields [field].get(leadId))

                # Mail
                mail =  unicode(result ['primaryAttributeValue']).encode('utf-8')
                csv_row.append(mail)

                attributes = result ['attributes']
                # Click in Mail
                for attribute in attributes:
                    if attribute ['name'] == "Link":
                        value = unicode(attribute ['value']).encode('utf-8')
                        csv_row.append(value)
                        break

                # adding empty field value for web related column
                if args.web_activity:
                    csv_row.append("")
                    csv_row.append("")

                # write row into csv 
                mywriter.writerow(csv_row)
                continue
                
            # 
            # 1: Web Visit
            # JSON results example:
            # {
            #  "id": 303306,
            #  "leadId": 101093,
            #  "activityDate": "2015-04-09T09:51:00Z",
            #  "activityTypeId": 10,
            #  "primaryAttributeValueId": 14,
            #  "primaryAttributeValue": "unknot304.jp/",
            #  "attributes": [
            #   {
            #     "name": "Client IP Address",
            #     "value": "202.212.192.233"
            #   },
            #   {
            #     "name": "Query Parameters",
            #     "value": ""
            #   },
            #   {
            #     "name": "Referrer URL",
            #     "value": ""
            #   },
            #   {
            #     "name": "User Agent",
            #     "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko)"
            #   }
            #  ]
            # }
            if  activityTypeId == 1:
                for field in tracking_fields:
                    csv_row.append(last_custom_fields [field].get(leadId))

                # adding empty field value for mail related column
                if args.mail_activity:
                    csv_row.append("")
                    csv_row.append("")

                if args.web_activity:
                    # Web
                    web =  unicode(result ['primaryAttributeValue']).encode('utf-8')
                    csv_row.append(web)
                    # Link on Web
                    csv_row.append("")
                    # Query Parameter
                    web_attributes = result ['attributes']
                    for web_attribute in web_attributes:
                        if web_attribute ['name'] == "Query Parameters":
                            qparam = unicode(web_attribute ['value']).encode('utf-8')
                            csv_row.append(qparam)
                            break

                # write row into csv 
                mywriter.writerow(csv_row)
                continue
                
            # 
            # 3: Click on Web
            # JSON results example:
            # {
            #  "id": 303306,
            #  "leadId": 101093,
            #  "activityDate": "2015-04-09T09:51:00Z",
            #  "activityTypeId": 10,
            #  "primaryAttributeValueId": 10,
            #  "primaryAttributeValue": "na-ab09.marketo.com/lp/user/01_PDF__DL.html",
            #  "attributes": [
            #   {
            #     "name": "Client IP Address",
            #     "value": "202.212.192.233"
            #   },
            #   {
            #     "name": "Query Parameters",
            #     "value": ""
            #   },
            #   {
            #     "name": "Referrer URL",
            #     "value": ""
            #   },
            #   {
            #     "name": "User Agent",
            #     "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko)"
            #   }
            #   {
            #     "name": "Webpage ID",
            #     "value": 7
            #   }
            #  ]
            # }
            if  activityTypeId == 3:
                for field in tracking_fields:
                    csv_row.append(last_custom_fields [field].get(leadId))

                # adding empty field value for mail related column
                if args.mail_activity:
                    csv_row.append("")
                    csv_row.append("")

                if args.web_activity:
                    # Web
                    csv_row.append("")
                    # Link on Web
                    link =  unicode(result ['primaryAttributeValue']).encode('utf-8')
                    csv_row.append(link)
                    # Query Parameter
                    web_attributes = result ['attributes']
                    for web_attribute in web_attributes:
                        if web_attribute ['name'] == "Query Parameters":
                            qparam = unicode(web_attribute ['value']).encode('utf-8')
                            csv_row.append(qparam)
                            break

                # write row into csv 
                mywriter.writerow(csv_row)
                continue

    if fh is not sys.stdout:
        fh.close()

    # testing methods
    # mktoClient.updateAccessToken()
    # mktoClient.getLeadRaw("101099", "email")
    # mktoClient.getLeadsRaw("id", "101095", "id")
    # raw_data = mktoClient.getActivityTypesRaw()
    # print >> sys.stderr, "Activity Types: " + json.dumps(raw_data, indent=4)



