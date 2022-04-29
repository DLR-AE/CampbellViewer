"""
# Python code to extract mode shapes out of HAWCStab2 binary files
#
#
"""

import numpy as np

########
# Basic Turbine Classes
########
class TurbineDataClass(object):
    """ Main class for turbine data """
    def __init__(self):
        super(TurbineDataClass, self).__init__()

        
        

class SubstructureDataClass(object):
    """ Main class for substructure data """
    def __init__(self):
        super(SubstructureDataClass, self).__init__()

        # define list for data
        self.body_data = []
        self.opstate   = []
        
    def numbody(self):
        return len(self.body_data)        
        

class BodyDataClass(object):
    """ Main class for body data """
    def __init__(self):
        super(BodyDataClass, self).__init__()

        # define list for data
        self.s = []
        
    def numele(self):
        return len(self.s)        

#########
#
#########
class HS2BINReader(object):
    """
    
    Attributes:
        turbine(TurbineDataClass): turbine data class
        __offset(int)            : current offset of bytes in bin file, position in file
    
    """
    def __init__(self, file: str, parent=None):
        """
        Args:
            file(str): file name of the bin file
        """
        super(HS2BINReader, self).__init__()
        
        self.__file = file
        
        # init attributes
        self.substructure = []
        self.__offset = 0
        
        # read the binary into the buffer
        self.__read_file()
        
        # read the turbine data from buffer
        self.__read_turbine()
        
    ###
    # private methods
    def __read_file(self):
        """reads the bin file as binary data into a buffer object
        """
        with open(self.__file, 'br') as f:
            self.__buff = f.read()


    #~ def __read_int(self, count: int):
        #~ """
        #~ Args:
            #~ count(int): number of byted to read
        #~ """
        #~ data = None
        
        #~ num_bytes = np.frombuffer(self.__buff, dtype=np.int32, count=1, offset=self.__offset).squeeze()
        #~ print(num_bytes)
        
        #~ # offset the first 32bit int == 4 bytes
        #~ self.__offset += 4
        
        #~ # read the data
        #~ if num_bytes == 4*count:
            #~ # 32 bit integer
            #~ data = np.frombuffer(self.__buff, dtype=np.int32, count=count, offset=self.__offset)
            #~ self.__offset += 4 * count
        #~ elif num_bytes == 8*count:
            #~ # 64 bit integer
            #~ data = np.frombuffer(self.__buff, dtype=np.int64, count=count, offset=self.__offset)
            #~ self.__offset += 8 * count            
        #~ elif num_bytes == 16*count:
            #~ # 128 bit integer
            #~ data = np.frombuffer(self.__buff, dtype=np.int64, count=count, offset=self.__offset)            
            #~ self.__offset += 16 * count
        #~ else:
            #~ return data
            
        #~ # finally spool forward another 32 bits = 4 bytes
        #~ self.__offset += 4
        
        #~ return data.squeeze()

    def __read_data(self, dtype, count: int):
        """
        Args:
            dtype()   : numpy data type
            count(int): number of byted to read
        """
        data = None
        
        num_bytes = np.frombuffer(self.__buff, dtype=np.int32, count=1, offset=self.__offset).squeeze()
        #~ print(num_bytes)
        
        # offset the first 32bit int == 4 bytes
        self.__offset += 4
        
        # decide on data type
        current_dtype = None
        byte_offset   = None
        if dtype == int:
            if num_bytes == 4*count:
                # 32 bit int
                current_dtype = np.int32
                byte_offset   = 4
            elif num_bytes == 8*count:
                # 64 bit real
                current_dtype = np.int64            
                byte_offset   = 8
            elif num_bytes == 16*count:
                # 128 bit real
                current_dtype = np.int128
                byte_offset   = 16
        elif dtype == float:
            if num_bytes == 4*count:
                # 32 bit int
                current_dtype = np.float32
                byte_offset   = 4
            elif num_bytes == 8*count:
                # 64 bit real
                current_dtype = np.float64            
                byte_offset   = 8
            elif num_bytes == 16*count:
                # 128 bit real
                current_dtype = np.float128
                byte_offset   = 16
        
        # read the data
        data = np.frombuffer(self.__buff, dtype=current_dtype, count=count, offset=self.__offset)
        self.__offset += byte_offset * count
            
        # finally spool forward another 32 bits = 4 bytes
        self.__offset += 4
        
        return data.squeeze()
    
    def __read_turbine(self):
        """
        """
        
        # read substructure
        num_subs = self.__read_data(dtype=int,count=1)
        for isub in range(num_subs):
            self.substructure.append(SubstructureDataClass())
            
            # read bodies
            num_bodies = self.__read_data(int,1)
            for ibody in range(num_bodies):
                self.substructure[isub].body_data.append(BodyDataClass())
                
                # read elements
                num_elements = self.__read_data(int, 1)
                self.substructure[isub].body_data[ibody].s = np.empty([num_elements])
                for iele in range(num_elements):
                    self.substructure[isub].body_data[ibody].s[iele] = self.__read_data(float,1)
     
    ###
    # public methods
    def numsubstr(self):
        return len(self.substructure)





###################################################################
# Main program
###################################################################
if __name__ == '__main__':
    print('hello')
    file = 'IWT_7.5-164_Rev-2.5.2_HS2_coarse.bin'
    MyTurbine = HS2BINReader(file)
    
    num_subs = MyTurbine.numsubstr()    
    print("number of substructures:", num_subs)
    for i in range(num_subs):
        print(f"substructure {i+1}:")
        num_bodies = MyTurbine.substructure[i].numbody()    
        print("    number of bodies       :", num_bodies)
        for ii in range(num_bodies):            
            print(f"    body {ii+1}:")
            num_elements = MyTurbine.substructure[i].body_data[ii].numele()
            print("        number of elements     :", num_elements)
            print(f"        {MyTurbine.substructure[i].body_data[ii].s}")
    
    
    