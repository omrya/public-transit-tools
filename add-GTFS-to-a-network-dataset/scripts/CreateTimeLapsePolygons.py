import datetime
import arcpy
arcpy.CheckOutExtension("Network")
arcpy.env.overwriteOutput = True

class CustomError(Exception):
    pass

try:

    #Check out the Network Analyst extension license
    if arcpy.CheckExtension("Network") == "Available":
        arcpy.CheckOutExtension("Network")
    else:
        arcpy.AddError("You must have a Network Analyst license to use this tool.")
        raise CustomError


#####################
    # Must already have a TimeOfDay DATE field added to polygons



    # ----- Get and process inputs -----

    # Service Area from the map that is ready to solve with all the desired settings
    # (except time of day - we'll adjust that in this script)
    input_network_analyst_layer = arcpy.GetParameter(0)
    
    # Output feature class of SA polygons which can be used to make a time lapse
    # End result will have a time field indicating which time of day the polygon is for
    output_feature_class = arcpy.GetParameterAsText(1)

    # Start and end day and time
    # Note: Datetime format check is in tool validation code
    
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
    start_day = arcpy.GetParameterAsText(2)
    if start_day in days: #Generic weekday
        start_day = days[start_day]
    else: #Specific date
        start_day = datetime.datetime.strptime(start_day, '%Y%m%d')
    start_time_input = arcpy.GetParameterAsText(3)
    start_time_dt = datetime.datetime.strptime(start_time_input, "%H:%M")
    start_time = datetime.datetime(start_day.year, start_day.month, start_day.day, start_time_dt.hour, start_time_dt.minute)

    # Upper end of time window (HH:MM in 24-hour time)
    # End time is inclusive.  An analysis will be run using the end time.
    end_day = arcpy.GetParameterAsText(4)
    if end_day in days: #Generic weekday
        end_day = days[end_day]
    else: #Specific date
        end_day = datetime.datetime.strptime(end_day, '%Y%m%d')
    end_time_input = arcpy.GetParameterAsText(5)
    end_time_dt = datetime.datetime.strptime(end_time_input, "%H:%M")
    end_datetime = datetime.datetime(end_day.year, end_day.month, end_day.day, end_time_dt.hour, end_time_dt.minute)

    # How much to increment the time in each solve, in minutes
    increment_input = arcpy.GetParameter(6)
    increment = datetime.timedelta(minutes=increment_input)
    timelist = [] # Actual list of times to use for the analysis.
    t = start_time
    while t <= end_time:
        timelist.append(t)
        t += increment


    # ----- Solve NA layer in a loop for each time of day -----

    # Grab the solver properties object from the NA layer so we can set the time of day
    solverProps = arcpy.na.GetSolverProperties(input_network_analyst_layer)

    # Grab the polygons sublayer, which we will export after each solve.
    sublayerNames = arcpy.na.GetNAClassNames(input_network_analyst_layer) # To ensure compatibility with localized software
    PolygonsSubLayer = arcpy.mapping.ListLayers(input_network_analyst_layer, sublayerNames["SAPolygons"])[0]

    for t in timelist:
        arcpy.AddMessage("Solving Service Area at time %s" % str(t))
        
        # Switch the time of day and solve the layer
        solverProps.timeOfDay = t
        arcpy.na.Solve(input_network_analyst_layer)
        
        # Calculate the TimeOfDay field
        expression = '"' + str(t) + '"'
        arcpy.management.CalculateField(PolygonsSubLayer, "TimeOfDay", expression, "PYTHON")
        # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
        
        #Append the polygons to the output feature class. If this was the first
        #solve, create the feature class.
        if not arcpy.Exists(output_feature_class):
            arcpy.management.CopyFeatures(PolygonsSubLayer, output_feature_class)
        else:
            arcpy.management.Append(PolygonsSubLayer, output_feature_class)

except CustomError:
    pass
except:
    raise
finally:
    arcpy.CheckInExtension("Network")