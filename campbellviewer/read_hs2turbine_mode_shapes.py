"""
# Python code to extract mode shapes out of HAWCStab2 binary files

The HAWCStab2 model is set up hierarchically in this way:

    TURBNINE
        |
        --> substructure i
                |
                |
                --> bodies
                |   |
                |   --> body ii
                |   |        |
                |   |        --> body data s (arc position for each element)
                |   |
                |   --> body ii + 1
                |       |
                |       --> body data s (arc position for each element)
                |
                --> opstate jj (states)
                        




"""

import numpy as np

########
# Basic Turbine Classes
########
class SubstructureDataClass(object):
    """ Main class for substructure data 
    
    Attributes:
        bodies(list) : list of element properties of type of a body
        opstate(list): list of operational state data
    """
    def __init__(self):
        super(SubstructureDataClass, self).__init__()

        # define list for data
        self.bodies  = []
        self.opstate = []
        
    def numbody(self):
        return len(self.bodies)        
        

class BodyDataClass(object):
    """ Main class for body element data 
    
    Attributes:
        s(ndarry) : (N,1) arc length position of end nodes of an element
    """
    def __init__(self):
        super(BodyDataClass, self).__init__()

        # define list for data
        self.s = None
        
    def numele(self):
        if not self.s is None:
            return len(self.s)
        else:
            return 0

#########
#
#########
class HS2BINReader(object):
    """
    
    Attributes:
        substructure(list)      : list of substructures present in a turbine
        num_modes(int)          : number of modes stored in the binary file
        num_steps(int)          : number of state points e.g. wind steps/ rpm steps
        operational_data(ndarry): (N,3) map of operational data
                                  i = operation point, j = 0 -> wind speed, j = 1 -> pitch, j = 2 -> power
        __offset(int)           : current offset of bytes in bin file, position in file/cached string
        __buff(bytes)           : cached binary file
        __num_DOF(int)          : parameter for the number of DOFs = u_x, u_y, u_z, theta_x, theta_y, theta_z
    
    """
    def __init__(self, file: str, parent=None):
        """
        Args:
            file(str): file name of the bin file
        """
        super(HS2BINReader, self).__init__()
        
        self.__file = file
        
        # init attributes
        self.substructure     = []
        self.num_modes        = 0
        self.num_steps        = 0
        self.operational_data = None
        self.__offset         = 0
        self.__num_DOF        = 6
        
        # read the binary into the buffer
        self.__read_file()
        
        # read the turbine data from buffer
        self.__read_turbine()
        
        # read the operational modal state data from buffer
        # these data follow directly the turbine data
        self.__read_opstate()
        
    ###
    # private methods
    def __read_file(self):
        """reads the bin file as binary data into a buffer object
        """
        with open(self.__file, 'br') as f:
            self.__buff = f.read()


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
                # 64 bit int
                current_dtype = np.int64            
                byte_offset   = 8
            elif num_bytes == 16*count:
                # 128 bit int
                current_dtype = np.int128
                byte_offset   = 16
        elif dtype == float:
            if num_bytes == 4*count:
                # 32 bit real
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
        """ read the hierarchical structure data and save
            it in internal data structure.
        """
        
        # read substructure
        num_subs = self.__read_data(dtype=int,count=1)
        for isub in range(num_subs):
            self.substructure.append(SubstructureDataClass())
            
            # read bodies
            num_bodies = self.__read_data(int,1)
            for ibody in range(num_bodies):
                self.substructure[isub].bodies.append(BodyDataClass())
                
                # read elements
                num_elements = self.__read_data(int, 1)
                self.substructure[isub].bodies[ibody].s = np.empty([num_elements])
                for iele in range(num_elements):
                    self.substructure[isub].bodies[ibody].s[iele] = self.__read_data(float,1)
                    
                    
    def __read_opstate(self):
        """read the modal operational state data from buffer
        """
        
        # read operation information
        opstate_info = self.__read_data(dtype=int,count=2)
        self.num_modes = opstate_info[0]
        self.num_steps = opstate_info[1]
        print(self.num_modes, self.num_steps)
        
        # read operation data map (N,3)
        self.operational_data = np.zeros([self.num_steps,3])
        dummy = self.__read_data(dtype=float,count=1)
        
        # loop over states
        #~ for i_state in range(self.num_steps):
            #~ self.operational_data[i_state,:] = self.__read_data(dtype=float,count=3)
            
            # if non blade then
            # loop over substructures
            # one have to know, which number the three-bladed substructure is!
            
                # loop over modes
                    
                    #loop over bodies
                    
            #else if blade substructure
            # loop over substructures
            # one have to know, which number the three-bladed substructure is!
            
                # loop over modes
                    
                    #loop over bodies
            
            
        self.operational_data[0,:] = self.__read_data(dtype=float,count=3)
        
        # switch sign for pitch and convert to degree
        self.operational_data[1,:] = np.rad2deg(-self.operational_data[1,:])
        print(self.operational_data)
        
     
    ###
    # public methods
    def numsubstr(self):
        return len(self.substructure)





###################################################################
# Main program
###################################################################
if __name__ == '__main__':
    print('########## HAWCStab2 binary result reader ##########\n')
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
            num_elements = MyTurbine.substructure[i].bodies[ii].numele()
            print("        number of elements     :", num_elements)
            print(f"        {MyTurbine.substructure[i].bodies[ii].s}")
    
    
    