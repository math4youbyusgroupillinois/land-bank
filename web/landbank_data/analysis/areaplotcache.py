from models import CommunityAreas as CA, Wards as W, CensusTract as CT, AreaPlotCache as Cache, Assessor, PinAreaLookup as PAL
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from django_pandas.managers import *

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
#    sfhs = Assessor.objects.filter(ptype_id=1)
    create_community_area_plots()
#    create_ward_plots(sfhs)
#    create_census_tract_plots(sfhs)

def create_community_area_plots():
    for ca in CA.objects.all()[:1]:
        # Find all properties in this community area
        pins = PAL.objects.filter(community_area_id__exact=ca.id).values('pin')
        properties = Assessor.objects.filter(pin__in=pins)
        prop_values= properties.values('ca_name', 'ptype', 'ptype_desc','sqft_land', 'sqft_bldg','current_land_assmt','current_building_assmt')
        df=pd.DataFrame.from_records(prop_values)
        #ptype(1=='SINGLE FAMILY')
        sf=df[df['ptype']== 1 ]
        sf['sqft_land_tmp']=sf['sqft_land']
        sf['sqft_land_tmp'][sf['sqft_land'] == 0.0]=np.nan
        sf['sqft_bldg_tmp']=sf['sqft_bldg']
        sf['sqft_bldg_tmp'][sf['sqft_bldg'] == 0.0]=np.nan
        sf['land_assmt_11_psf']=sf['current_land_assmt']/sf['sqft_land_tmp']
        sf['bldg_assmt_11_psf']=sf['current_building_assmt']/sf['sqft_bldg_tmp']
        sf['Msqft_land_11']=(10 ** (-3))*sf['sqft_land']
        sf['Msqft_bldg_11']=(10 ** (-3))*sf['sqft_bldg']
        ap_land_psf=sf['land_assmt_11_psf'].map(lambda x: x if x != np.inf else np.nan)
        ap_bldg_psf=sf['bldg_assmt_11_psf'].map(lambda x: x if x != np.inf else np.nan)
        fig = plt.figure()
        
        fig.suptitle(ca.area_name ,fontsize=14)
        ax=fig.add_subplot(221)
        n_land_psf, bins_land_psf, patches = ax.hist(ap_land_psf[ap_land_psf.notnull()].T, bins = 10, normed=False, facecolor='red', alpha=0.4)
        ax.set_xlabel('$')
        ax.set_ylabel('Count')
        ax.set_title('Land PSF and Size Dist')
        ax.grid(True)
        ax=fig.add_subplot(222)
        to_hist = ap_bldg_psf.T.values
        to_hist = to_hist[np.logical_not(np.isnan(to_hist))]
        n_bldg_psf, bins_bldg_psf, patches = ax.hist(to_hist, bins = 10, normed=False, facecolor='red', alpha=0.4)
        ax.set_xlabel('$')
        ax.grid(True)
        ax.set_title('Building PSF and Size Dist')
        ax=fig.add_subplot(223)
        ax.set_xlabel('10^3 ft^2')
        ax.set_ylabel('count')
        n_land_msf, bins_land_msf, patches = ax.hist(sf['Msqft_land_11'][ap_land_psf.notnull()].T, bins = 10, normed=False, facecolor='blue', alpha=0.4)
        ax.grid(True)
        ax=fig.add_subplot(224)
        ax.set_xlabel('10^3 ft^2')
        n_bldg_msf, bins_bldg_msf, patches = ax.hist(sf['Msqft_bldg_11'][ap_land_psf.notnull()].T, bins = 10, normed=False, facecolor='blue', alpha=0.4)
        ax.grid(True)
        fig.set_size_inches(7,5)
        fig.tight_layout()
        fig.subplots_adjust(top=0.85)
#       fig.savefig('/home/evan/Documents/chicago/dssg-landbank-project/analysis/ca_desc/'+ ca + '.png')
#       plt.show()
        hist_data=build_json(ca.area_name,n_land_psf,bins_land_psf,n_bldg_psf,bins_bldg_psf,n_land_msf,bins_land_msf,n_bldg_msf,bins_bldg_msf)
        # Calculate plot data for this community area based on properties[] list
        # ...
        # Set plot data with this method to create/update the json_str field
        area_type = 'Community Area'
        area_id = ca.id
        key_name = 'histData'
        value = json.dumps(hist_data, indent=4, separators=(',', ':'))
        area_label = ca.area_name
        set_or_update_plot(area_type, area_id, key_name, value, area_label)

def build_json(ca,n_land_psf,bins_land_psf,n_bldg_psf,bins_bldg_psf,n_land_msf,bins_land_msf,n_bldg_msf,bins_bldg_msf):
        histData = {}
        histData['title']=ca
        histData['land_psf']=[]
        for b,v in zip(bins_land_psf,n_land_psf):
            histData['land_psf'].append({'x':b, 'y':v})
            histData['bldg_psf'] = []
        for b,v in zip(bins_bldg_psf,n_bldg_psf):
            histData['bldg_psf'].append({'x':b, 'y':v})
        histData['land_msf'] = []
        for b,v in zip(bins_land_msf,n_land_msf):
            histData['land_msf'].append({'x':b, 'y':v})
        histData['bldg_msf'] = []
        for b,v in zip(bins_bldg_msf,n_bldg_msf):
            histData['bldg_msf'].append({'x':b, 'y':v})
        return histData

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

