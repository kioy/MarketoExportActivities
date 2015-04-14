# MarketoExportActivities
Exporting lead activities via Marketo REST API

Usage: mktoExportActivities.py <options>

Options:

  -h                                this help  
  -i --instance <instance>          Marketo Instance URL such as https://123-XYZ-456.mktorest.com  
  -o --output <filename>	    Output filename  
  -d --id <client id>               Marketo LaunchPoint Client Id: eg. 3d96eaef-f611-42a0-967f-00aeeee7e0ea  
  -s --secret <client secret>       Marketo LaunchPoint Client Secret: eg. i8s6RRq1LhPlMyATEKfLWl1255bwzrF
  -c --since <date>                 Since Date time for calling Get Paging Token: eg. 2015-01-31
  -g --debug                        Pring debugging information
  -j --not-use-jst                  Change TimeZone for Activity Date field. Default is JST.
  -f --change-data-field <fields>   Specify comma separated 'UI' fields name such as 'Behavior Score' for extracting from 'Data Value Changed' activities. default fields: 'Lead Score, Lifecycle Status'
  -w --add-webvisit-activity        Adding Web Visit activity. It might be a cause of slowdown.
  -m --add-mail-activity            Adding mail open/click activity. It might be a cause of slowdown.
    
Mail bug reports and suggestion to : Yukio Y <unknot304 AT gmail.com>

Please refer Market REST API documents: http://docs.marketo.com
Search article with "Create a Custom Service for Use with ReST API"
