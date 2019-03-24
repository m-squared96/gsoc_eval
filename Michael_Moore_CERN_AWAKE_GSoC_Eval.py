#!/usr/bin/python3

# Importing all required modules
# Python standard library modules
import datetime
import pytz
import csv

# Third-party modules
import h5py
import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt

def timestamp(filename):
    # Define UNIX timestamp (in ns) on filename as an integer variable
    unix_timestamp = int(filename[5:24])

    # UNIX timestamp is generally accepted in seconds, not nanoseconds, so convert by dividing by 10^9
    ts_in_seconds = unix_timestamp//1e9

    # Create parent datetime object
    dt = datetime.datetime.utcfromtimestamp(ts_in_seconds)

    # datetime object 'dt' is already in UTC time. To convert to CERN local time, use pytz module to reference the UTC +01:00 timezone:
    utc_time = dt
    cern_tz = pytz.timezone('Europe/Berlin') # Berlin and Geneva in the same timezone
    cern_time = dt.astimezone(cern_tz)

    # Display times
    print('UTC:', utc_time)
    print('CERN:', cern_time)

def dataset_finder(h5_file,dataset_list,address_str):
    '''
    Accepts h5py File or Group. Returns a list of dataset
    paths within the h5_file variable
    '''
    for entry in h5_file:
        if entry != '__DATA_TYPES__':
            if type(h5_file[entry]) in (h5py._hl.group.Group,h5py._hl.files.File):
                dataset_list = dataset_finder(h5_file[entry],dataset_list,address_str + '/' + entry)

            else:
                dataset_list.append(address_str + '/' + entry)

    return dataset_list

def dataset_output(filename):

    # Read in data file
    entire_directory = h5py.File(filename,'r')
    
    # Define empty list to feed into dataset_finder. Will then
    # contain paths to all datasets in the data file
    datasets = []
    datasets = dataset_finder(entire_directory,datasets,'')

    # Empty lists for use in capturing dataset metadata
    ds_shapes = []
    ds_sizes = []
    ds_dtypes = []

    for ds in datasets:
        ds_shapes.append(entire_directory[ds].shape) # Record dataset shape
        ds_sizes.append(entire_directory[ds].size) # Record dataset size
        
        # Problem with TypeBitfieldID datatype - not NumPy compatible
        try:
            # Record dtype if not an issue
            ds_dtypes.append(str(entire_directory[ds].dtype)) 
            
        except TypeError:
            # If an error is raised, manually record 'TypeBitfieldID'
            ds_dtypes.append('TypeBitfieldID')

    # Empty list to contain all data for output to CSV file
    all_info = []

    # Iterate through all lists created above and combine info about:
    # 1. Dataset path
    # 2. Dataset shape
    # 3. Dataset size
    # 4. Dataset data type
    for name,shape,size,dtype in zip(datasets,ds_shapes,ds_sizes,ds_dtypes):
        all_info.append({'Dataset':name,'Shape':shape,'Size':size,'Data Type':dtype})
        
    # Write this data to a file, with the 'fields' list defining
    # column headings
    with open('Datasets.csv','w+') as file:
        fields = ['Dataset','Shape','Size','Data Type']
        writer = csv.DictWriter(file,fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_info)
        
    file.close()
    return entire_directory

def event_image(file):

    # Creating NumPy array from data stored in data file
    image_array = np.array(file['AwakeEventData/XMPP-STREAK/StreakImage/streakImageData'])

    # Extracting image height and width data from data file
    image_height = np.array(file['AwakeEventData/XMPP-STREAK/StreakImage/streakImageHeight'])[0]
    image_width = np.array(file['AwakeEventData/XMPP-STREAK/StreakImage/streakImageWidth'])[0]

    # Reshape array using numpy.reshape and filter using scipy.signal.medfilt
    raw_image = np.reshape(image_array,(image_height,image_width))
    filtered_image = sig.medfilt(raw_image,[3,3])

    # Plot image
    plt.figure()
    plt.imshow(filtered_image)
    plt.title('Event image')
    plt.xlabel('X - Pixels')
    plt.ylabel('Y - Pixels')

    # Save image
    plt.savefig('MMoore_Event_Image.png')

def main():
    
    # Conveniently define data file
    filename = 'Data/1541962108935000000_167_838.h5'

    timestamp(filename)
    h5_file = dataset_output(filename)

    event_image(h5_file)

main()
