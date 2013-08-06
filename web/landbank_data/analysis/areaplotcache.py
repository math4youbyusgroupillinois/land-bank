from models import CommunityAreas as CA, Wards as W, CensusTract as CT, AreaPlotCache as Cache, Assessor, PinAreaLookup as PAL
import json

# This script should be run whenever we want to update the area plots
def set_or_update_plot(area_type, area_id, key_name, value, area_label):
    cached_data, was_created = Cache.objects.get_or_create(\
        area_type = area_type\
        ,area_id = area_id\
        )
    if was_created:
        print 'created new cache object for ' + area_label
        cached_data.json_str = json.dumps({key_name:value})
    else:
        print 'got existing cache object for ' + area_label
        # turn json data into a dict
        try: obj = json.loads(cached_data.json_str)
        except: obj = {}
        # set a dict value
        obj[key_name] = value
        # turn dict into json string
        cached_data.json_str = json.dumps(obj)
    # save this instance of AreaPlotCache with new/updated data to database
    cached_data.save()

def run():
    # Get all single-family homes from assessor's file
    sfhs = Assessor.objects.filter(ptype_id=1)
    create_community_area_plots(sfhs)
    create_ward_plots(sfhs)
    create_census_tract_plots(sfhs)

def create_community_area_plots(sfhs):
    for ca in CA.objects.all():
        # Find all properties in this community area
        pins = PAL.objects.filter(community_area_id__exact=ca.id)
        properties = []
        for p in pins:
            try: properties.append(sfhs.get(pin=p.pin))
            except: continue
        # Calculate plot data for this community area based on properties[] list
        # ...
        # Set plot data with this method to create/update the json_str field
        area_type = 'Community Area'
        area_id = ca.id
        key_name = 'property_count'
        value = len(properties)
        area_label = ca.area_name
        set_or_update_plot(area_type, area_id, key_name, value, area_label)

def create_ward_plots(sfhs):        
    for w in W.objects.all():
        pins = PAL.objects.filter(ward_id__exact=w.id)
        properties = []
        for p in pins:
            try: properties.append(sfhs.get(pin=p.pin))
            except: continue
        # Do calculations on the list of properties in the ward
        # Set plot data with this method to create/update the json_str field
        area_type = 'Ward'
        area_id = w.id
        key_name = 'property_count'
        value = len(properties)
        area_label = 'Ward ' + unicode(w.ward)
        set_or_update_plot(area_type, area_id, key_name, value, area_label)

def create_census_tract_plots(sfhs):
    for ct in CT.objects.all():
        pins = PAL.objects.filter(census_tract_id__exact=ct.id)
        properties = []
        for p in pins:
            try: properties.append(sfhs.get(pin=p.pin))
            except: continue
        # Do calculations on the list of properties in the census tract
        # Set plot data with this method to create/update the json_str field
        area_type = 'Census Tract'
        area_id = ct.id
        key_name = 'property_count'
        value = len(properties)
        area_label = unicode(ct.fips)
        set_or_update_plot(area_type, area_id, key_name, value, area_label)
