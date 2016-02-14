# MarketoExportActivities
Exporting lead activities via Marketo REST API. Output format is comma separated (csv) file.

# Usage
Usage: mktoExportActivities.py [options]

Options:

  `-h                                :this help`  
  `-i/--instance <instance>          :Marketo Instance URL such as https://123-XYZ-456.mktorest.com`  
  `-o/--output <filename>	     :Output filename`  
  `-d/--id <client id>               :Marketo LaunchPoint Client Id: eg. 3d96eaef-f611-42a0-967f-00aeeee7e0ea`  
  `-s/--secret <client secret>       :Marketo LaunchPoint Client Secret: eg. i8s6RRq1LhPlMyATEKfLWl1255bwzrF`  
  `-c/--since <date>                 :Since Date time for calling Get Paging Token: eg. 2015-01-31`  
  `-l/--listid <list id>             :ListId to filter leads (You can find the ID from URL like ST443A1, 443 is list id)`
  `-g/--debug                        :Pring debugging information`  
  `-j/--not-use-jst                  :Change TimeZone for Activity Date field. Default is JST.`  
  `-f/--change-data-field <fields>   :Specify comma separated 'UI' fields name such as 'Behavior Score' for extracting from 'Data Value Changed' activities. default fields: 'Lead Score'`  
  `-w/--add-webvisit-activity        :Adding Web Visit/Web Click Link activity. It might be a cause of slowdown.`  
  `-m/--add-mail-activity            :Adding mail open/click activity. It might be a cause of slowdown.`  
    
Example:  
`python mktoExportActivities.py -i https://012-RYY-345.mktorest.com -d 4e430960-xxxx-43c6-bbbb-c763a2f22dcd -s 0Sprrsdfis68h1fVY4xohgAq3xAPK19P -c 2015-04-09 -f "Behavior Score, Demographic Score" -m -w`  

# Required
Python2.7
httplib2  

you can install httplib2 as follows,  
-Install pip if you don’t have it.  
-download https://bootstrap.pypa.io/get-pip.py  
-invoke command in console  
     `sudo python get-pip.py`  

-install httplib2 if you don’t have it.  
-invoke command in console  
     `sudo pip install httplib2`  


# Reference
Please refer Market REST API documents: http://docs.marketo.com  
Search article with "Create a Custom Service for Use with ReST API"  


# License
This source is licensed under an MIT License, see the LICENSE file for full details. If you use this code, it would be great to hear from you.
