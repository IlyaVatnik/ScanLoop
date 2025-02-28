# -*- coding: utf-8 -*-
"""
Created on Tue Nov 20 19:09:12 2018


@author: Ilya
"""

__date__='2025.02.24'
__version__='3.4'

from PyQt5.QtCore import pyqtSignal, QObject
import numpy as np
import winsound
import time



class ScanningProcess(QObject):
  

    S_update_status=pyqtSignal(str) #signal to initiate update the index of the current file in lineEdit_CurrentFile of main window
    S_saveData=pyqtSignal(object,str) #signal to initiate saving measured spectrum to a file
    S_saveSpectrumToOSA=pyqtSignal(str) # signal used if high resolution needed. Initiate saving spectral data to inner hard drive of OSA
    S_addPosition_and_FilePrefix=pyqtSignal(str) #signal to initiate saving current position of the stages and current file index to file "Positions.txt"
    S_finished=pyqtSignal()  # signal to finish
    S_print=pyqtSignal(str) # signal used to print into main text browser
    S_print_error=pyqtSignal(str) # signal used to print errors into main text browser


    minimumPeakHight=1

    def __init__(self):
        super().__init__()
        self.OSA=None # add Optical Spectral Analyzer
        self.stages=None # add all three stages
        self.piezo_stage=None
        self.FullSpan=10
        self.IsHighRes=False

        self.scanning_step=30
        self.seeking_step=30
        self.backstep=30    #in microns, to move stage axis_to_get_contact to loose the contact
        self.level_to_detect_contact=-3  # dBm, used to determine if there is contact between the taper and the sample. see function checkIfContact for details
        self.current_file_index=1
        self.stop_file_index=100
        self.number_of_scans_at_point=1
        self.is_squeeze_span_for_seeking_contact=False
        self.is_low_res_for_seeking_contact=False
        self.is_seeking_contact=False
        self.recognize_contact_logic='min'
        
        self.is_follow_peak=False
        self.max_allowed_shift=1000
        
        self.save_out_of_contact=False
        self.LunaJonesMeasurement=False
        
        # self.scanning_type='Along Z, get contact along X'
        self.axis_to_scan='Z'
        self.axis_to_get_contact='X'
        self.no_backstep=False
        
        self.is_running=False  ## Variable is "True" during scanning process. Pushing on "scanning" button in main window sets is_running True and start scanning process.
    ### Another pushing on "scanning" button during the scanning proccess set is_running to "False" and interrupt the scanning process

        self.span_for_scanning=0.05 #nm, Value of span in searching_contact function. Used if is_squeeze_span_for_seeking_contact==True

        IsInContact=False # True - when taper is in contact with the sample
        
    def set_parameters(self,dictionary):
        for key in dictionary:
            try:
                self.__setattr__(key, dictionary[key])
            except:
                pass
        
                
    def get_parameters(self)->dict:
        '''
        Returns
        -------
        Seriazible attributes of the object
        '''
        d=dict(vars(self)).copy() #make a copy of the vars dictionary
        del d['stages']
        del d['OSA']
        del d['piezo_stage']
        return d
    
    def update_OSA_parameters(self):
        try:
            self.FullSpan=self.OSA._Span
        except:
            pass
        try:
            self.IsHighRes=self.OSA.IsHighRes
        except:
            self.IsHighRes=False

    # def set_axes(self): # set axis depending on choice in MainWindow
    #     s=self.scanning_type
    #     # try:
    #     self.axis_to_get_contact=s.split(', get contact along ')[1]
        
    #     self.axis_to_scan=s.split(', get contact along ')[0].split('Along ')[1]
    #     # except IndexError:
        #     if 'Nano' in s:
        #         self.axis_to_scan='Nano'
        #         self.axis_to_get_contact=None
        #     else:
        #         self.S_print_error.emit('\n Scanning directions are badly defined \n')
       

    def set_OSA_to_Searching_Contact_State(self): #set rough resolution and narrowband span
    
        # print(self.OSA._Span)
        
        if self.is_squeeze_span_for_seeking_contact:
            self._FullSpan=self.OSA._Span
            self.OSA.SetMode(3) # set APEX OSA to O.S.A. mode - it works faster
            self.OSA.SetSpan(self.span_for_scanning)

        
        self.IsHighRes=self.OSA.IsHighRes
        
        if self.IsHighRes and self.is_low_res_for_seeking_contact:
            self.OSA.SetWavelengthResolution('Low')
        time.sleep(0.05)
        print("OSA set to seeking contact state")

    def set_OSA_to_Measuring_State(self): #set back  resolution and preset span
        if self.is_squeeze_span_for_seeking_contact:
            self.OSA.SetMode(4) # set APEX OSA to Tracking Generator mode back
            self.OSA.SetSpan(self._FullSpan)
        if self.IsHighRes and self.is_low_res_for_seeking_contact:
            self.OSA.SetWavelengthResolution('High')

        time.sleep(0.05)
        print("OSA set to mearing state")

    def search_contact(self): ## move taper towards sample until contact has been obtained
        total_seeking_shift=0    
        wavelengthdata, spectrum=self.OSA.acquire_spectrum()
        time.sleep(0.05)
           
        self.set_OSA_to_Searching_Contact_State()
        self.IsInContact=self.checkIfContact(spectrum) #check if there is contact already
        
        while not self.IsInContact:
            self.move_along_contact_axis(self.seeking_step)
            total_seeking_shift+=self.seeking_step
            self.S_print.emit('Moved to Sample')
            wavelengthdata, spectrum=self.OSA.acquire_spectrum()
            time.sleep(0.05)
            self.IsInContact=self.checkIfContact(spectrum)
            if total_seeking_shift>self.max_allowed_shift:
                self.is_running=False
                self.S_print_error.emit('max allowed shift for seeking is approached. Seeking for contact has been stopped')
            if not self.is_running : ##if scanning process is interrupted,stop searching contact
                self.set_OSA_to_Measuring_State()
                self.OSA.acquire_spectrum()
                self.S_print.emit('\nSeeking for contact interrupted')
                return False
        
        
        self.S_print.emit('\nContact found\n')
        self.set_OSA_to_Measuring_State()
        winsound.Beep(1000, 500)
        return True

    def losing_contact(self): ##move taper away from sample until contact is lost
        self.set_OSA_to_Searching_Contact_State()
        while self.IsInContact:
            self.move_along_contact_axis(-self.backstep)
            self.S_print.emit('Moved Back from Sample')
            wavelengthdata,spectrum=self.OSA.acquire_spectrum()
            time.sleep(0.05)
            self.IsInContact=self.checkIfContact(spectrum)
            if not self.is_running : ##if scanning process is interrupted,stop searching contact
                self.set_OSA_to_Measuring_State()
                self.OSA.acquire_spectrum()
                return False
        self.S_print.emit('\nContact lost\n')
        self.set_OSA_to_Measuring_State()
        return True

    def checkIfContact(self, spectrum):  ## take measured spectrum and decide if there is contact between the taper and the sample
        if self.recognize_contact_logic=='min':
            value=np.min(spectrum)
        elif self.recognize_contact_logic=='mean':
            value=np.mean(spectrum)
        if value<self.level_to_detect_contact:
            return True
        else:
            return False

    def move_along_scan_axis(self,step):
        if self.axis_to_scan == 'Piezo':
            self.piezo_stage.move_by(step)
        elif self.axis_to_scan == 'None':
            return
        else:
            self.stages.shiftOnArbitrary(self.axis_to_scan,step)
    
    def move_along_contact_axis(self,step):
        if self.axis_to_get_contact == 'Piezo':
            self.piezo_stage.move_by(step)
        elif self.axis_to_get_contact == 'None':
            return
        else:
            self.stages.shiftOnArbitrary(self.axis_to_get_contact,step)
        

    """
    Main function
    """
    def run(self):
        time.sleep(0.05)
        ### main loop
        
        self.update_OSA_parameters()
    
        
        while self.is_running and self.current_file_index<self.stop_file_index+1:
            self.S_update_status.emit('Step {} of {}'.format(self.current_file_index,self.stop_file_index))
            if self.save_out_of_contact:
                wavelengths_background,background_signal=self.OSA.acquire_spectrum()
                self.S_saveData.emit(np.stack((wavelengths_background, background_signal),axis=1),'p='+str(self.current_file_index)+'_out_of_contact') # save Jones matrixes to Luna for out of contact
   
            time0=time.time()
       
            ## Getting in contact between the taper and the sample
            if self.is_seeking_contact:
                self.search_contact()
            else:
                self.move_along_contact_axis(self.seeking_step)
                


            if not self.is_running:
                break
            
            
            ## Acquring and saving data
            for jj in range(0,self.number_of_scans_at_point):
                self.S_print.emit('saving sweep # ' + str(jj+1))
                wavelengthdata, spectrum=self.OSA.acquire_spectrum()
                time.sleep(0.05)
                
                Data=np.stack((wavelengthdata, spectrum),axis=1)
                self.S_saveData.emit(Data,'p='+str(self.current_file_index)+'_j='+str(jj)) # save spectrum to file
                if not self.is_running: break

            #update indexes in MainWindow and save positions into "Positions.txt"

            if self.is_follow_peak and max(spectrum)-min(spectrum)>self.minimumPeakHight:
                self.OSA.SetCenter(wavelengthdata[np.argmin(spectrum)])

            if not self.is_running:
                break

            if not self.no_backstep:
                if self.is_seeking_contact:
                    self.losing_contact()
                else:
                    self.move_along_contact_axis(-self.seeking_step)
                

            if not self.is_running:
                break
     
            ##  move sample along scanning axis
            self.move_along_scan_axis(self.scanning_step)
            self.current_file_index+=1

            self.S_print.emit('\n Shifted along the scanning axis\n')

            self.S_print.emit('Time elapsed for measuring at single point is {} \n'.format(time.time()-time0))

        # if scanning finishes because all points along scanning axis are measured
        if not self.is_running:
            self.S_print_error.emit('\nScanning interrupted\n')
        if self.current_file_index>self.stop_file_index:
            self.is_running=False
            print('\nScanning finished\n')
        
        self.S_finished.emit()

    def __del__(self):
        print('Closing scanning object...')

if __name__ == "__main__":

       ScanningProcess=ScanningProcess(None,None)