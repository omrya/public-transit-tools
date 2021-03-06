################################################################################
## Toolbox: Add GTFS to a Network Dataset / Transit Analysis Tools
## Created by: Melinda Morang, Esri, mmorang@esri.com
## Last updated: 21 November 2017
################################################################################
'''Helper methods for analysis tools.'''
################################################################################
'''Copyright 2017 Esri
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.'''
################################################################################

import datetime
import arcpy

def make_analysis_time_of_day_list(start_day_input, end_day_input, start_time_input, end_time_input, increment_input):
    '''Make a list of datetimes to use as input for a network analysis time of day run in a loop'''

    start_time, end_time = convert_inputs_to_datetimes(start_day_input, end_day_input, start_time_input, end_time_input)

   # How much to increment the time in each solve, in minutes
    increment = datetime.timedelta(minutes=increment_input)
    timelist = [] # Actual list of times to use for the analysis.
    t = start_time
    while t <= end_time:
        timelist.append(t)
        t += increment

    return timelist


def convert_inputs_to_datetimes(start_day_input, end_day_input, start_time_input, end_time_input):
    '''Parse start and end day and time from tool inputs and convert them to datetimes'''

    # For an explanation of special ArcMap generic weekday dates, see the time_of_day parameter
    # description in the Make Service Area Layer tool documentation
    # http://desktop.arcgis.com/en/arcmap/latest/tools/network-analyst-toolbox/make-service-area-layer.htm
    days = {
        "Monday": datetime.datetime(1900, 1, 1),
        "Tuesday": datetime.datetime(1900, 1, 2),
        "Wednesday": datetime.datetime(1900, 1, 3),
        "Thursday": datetime.datetime(1900, 1, 4),
        "Friday": datetime.datetime(1900, 1, 5),
        "Saturday": datetime.datetime(1900, 1, 6),
        "Sunday": datetime.datetime(1899, 12, 31)}
    
    # Lower end of time window (HH:MM in 24-hour time)
    generic_weekday = False
    if start_day_input in days: #Generic weekday
        generic_weekday = True
        start_day = days[start_day_input]
    else: #Specific date
        start_day = datetime.datetime.strptime(start_day_input, '%Y%m%d')
    start_time_dt = datetime.datetime.strptime(start_time_input, "%H:%M")
    start_time = datetime.datetime(start_day.year, start_day.month, start_day.day, start_time_dt.hour, start_time_dt.minute)

    # Upper end of time window (HH:MM in 24-hour time)
    # End time is inclusive.  An analysis will be run using the end time.
    if end_day_input in days: #Generic weekday
        if not generic_weekday:
            # The tool UI validation should prevent them from encountering this problem.
            arcpy.AddError("Your Start Day is a specific date, but your End Day is a generic weekday. \
Please use either a specific date or a generic weekday for both Start Date and End Date.")
            raise
        end_day = days[end_day_input]
        if start_day != end_day:
            # We can't interpret what the user intends if they choose two different generic weekdays,
            # and the solver won't be happy if the start day is after the end day, even if we add a \
            # week to the end day. So just don't support this case. If they want to solve across \
            # multiple days, they should use specific dates.
            # The tool UI validation should prevent them from encountering this problem.
            arcpy.AddError("If using a generic weekday, the Start Day and End Day must be the same.")
            raise

    else: #Specific date
        if generic_weekday:
            arcpy.AddError("Your Start Day is a generic weekday, but your End Day is a specific date. \
Please use either a specific date or a generic weekday for both Start Date and End Date.")
            raise
        end_day = datetime.datetime.strptime(end_day_input, '%Y%m%d')
    end_time_dt = datetime.datetime.strptime(end_time_input, "%H:%M")
    end_time = datetime.datetime(end_day.year, end_day.month, end_day.day, end_time_dt.hour, end_time_dt.minute)

    if start_time == end_time:
        arcpy.AddError("Start and end date and time are the same.")
        raise
    elif end_time < start_time:
        arcpy.AddError("End time is earlier than start time.")
        raise

    return start_time, end_time
 