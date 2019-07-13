from brukeropusreader import read_file
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pprint

class Wave:
    ''' an object to parse bruker opus file and convert/process into
    other formats such as dataframe or numpy array
    initializing object
    Wave(root)

    file is assumed to be stored according to the following format
    -root
    + --date1
    + --date2
    .....

    '''
    def __init__(self, root):
        ''' create object by __init__(root)
        :root:(str) path to the root directory of the stored file
        '''
        self.root = root
        self.file_names = self.listpath(self.root)
        self.values = self.parse_values(self.file_names)
    def list_names(self):
        ''' list names of the values'''
        pprint.pprint([key for key in self.values.keys()])
    def listpath(self, root_path):
        ''' list paths of all files in the root dir'''
        date_dirs = os.listdir(root_path)
        paths=[]
        for date_dir in date_dirs:
            if date_dir[0]=='.':
                continue
            file_names = os.listdir(os.path.join(root_path, date_dir))
            for file_name in file_names:
                path = os.path.join(root_path, date_dir, file_name)
                paths.append([path,file_name[:-2]])
        return paths
    def parse_values(self, filenames):
        '''parse values of .0 files from bruker opus'''
        if not hasattr(self, 'file_error'):
            self.file_error=[]
        values = {}
        for filename in filenames:
            if filename[0][-2:]=='.0':
                try:
                    bruker_object = read_file(filename[0])
                except ValueError:
                    print(f'ValueError {filename}')
                    self.file_error.append(f'ValueError {filename}')
                    continue
                wave = pd.DataFrame(bruker_object.spectrum, 1/np.array(bruker_object.wave_nums)*1e7)
                wave.columns = ['intensity(relative)']
                wave.index.name = 'wavelength(nm)'
                values[filename[1]] = wave
        return values
    def to_csv(self, root_path):
        '''save all waves to csv into the direction root_path
        use example
        wave.to_csv('./savedir')
        '''
        if not os.path.exists(root_path):
            os.mkdir(root_path)
        for wave_name, wave_data in self.values.items():
            wave_data.to_csv(f'{root_path}/{wave_name}.csv')
    def load_csv(self, root_path):
        '''load waves from csv
        note that this will replace all your current waves
        usage
        wave.load_csv('./savedir')
        '''
        end_filenames=os.listdir(root_path)
        filenames = [[os.path.join(root_path, end_filename), end_filename[:-4]]
                for end_filename in end_filenames]
        if not hasattr(self, 'file_error'):
            self.file_error=[]
        values = {}
        for filename in filenames:
            print(filename)
            if filename[0][-4:]=='.csv':
                #print(f'reading file{filename[0]}')
                try:
                    df = pd.read_csv(filename[0],index_col=0)
                except ValueError:
                    #print(f'ValueError {filename}')
                    self.file_error.append(f'ValueError {filename}')
                    continue
                wave = df
                values[filename[1]] = wave
        self.values=values
        return values

    def plot(self, wave_name):
        ''' plot a wave file
        usage
        wave.plot('wave3')
        '''
        plt.plot(self.values[wave_name])
        plt.show()
