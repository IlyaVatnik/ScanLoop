# -*- coding: utf-8 -*-

__version__='20.8.6'
__date__='2025.03.03'

import os
if __name__=='__main__':
    os.chdir('..')
    
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import sys
import json
import time 

from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QDialog,QLineEdit,QComboBox,QCheckBox,QMessageBox

import importlib
import Common.Consts

from Hardware.Config import Config
from Hardware.PiezoStageE53D_serial import PiezoStage

'''
from Hardware.Interrogator import Interrogator
from Hardware.YokogawaOSA import OSA_AQ6370
from Hardware.ova5000 import Luna
from Hardware.KeysightOscilloscope import Scope
from Hardware.APEX_OSA import APEX_OSA_with_additional_features
'''

from Logger.Logger import Logger
from Visualization.Painter import MyPainter
from Utils.PyQtUtils import pyqtSlotWExceptions
from Windows.UIs.MainWindowUI import Ui_MainWindow
from Common.Hardware_ports import Hardware_ports


from Scripts import Analyzer
from Scripts import Spectral_processor





def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

class ThreadedMainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        # Handle threads
        self.threads = []
        self.destroyed.connect(self.kill_threads)

    
    def add_thread(self, objects):
        """
        Creates thread, adds it into to-destroy list and moves objects to it.
        Thread is QThread there.
        :param objects -- list of QObjects.
        :return None
        """
        # Create new thread
        thread = QThread()

        # Add new thread to list of threads to close on app destroy.
        self.threads.append(thread)

        # Move objects to new thread.
        for obj in objects:
            obj.moveToThread(thread)

        thread.start()
        return thread

    def kill_threads(self):
        """
        Closes all of created threads for this window.
        :return: None
        """
        # Iterate over all the threads and call wait() and quit().
        for thread in self.threads:
#            thread.wait()
            thread.quit()



class MainWindow(ThreadedMainWindow):
    force_OSA_acquireAll = pyqtSignal()
    force_OSA_acquire = pyqtSignal()
    force_stage_move = pyqtSignal(str,float)
    force_piezo_stage_move=pyqtSignal(float)
    force_scope_acquire = pyqtSignal()
    force_scanning_process=pyqtSignal()
    force_laser_scanning_process=pyqtSignal()
    force_laser_sweeping_process=pyqtSignal()
    
    update_powermeter_graph=pyqtSignal(float)
    
    '''
    Initialization
    '''
    def __init__(self, parent=None,version='0.0',date='0.0.0'):
        super().__init__(parent)
        self.path_to_main=os.getcwd()
        # GUI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("ScanLoop V."+version+', released '+date)
       
        self.stages=None
        self.OSA=None
        self.scope=None
        self.laser=None
        self.powermeter=None
        self.piezo_stage=None
        
        self.painter = MyPainter(self.ui.groupBox_spectrum)
        self.analyzer=Analyzer.Analyzer(os.getcwd()+'\\ProcessedData\\Processed_spectrogram.pkl3d')
        self.logger = Logger(parent=None)
        self.spectral_processor=Spectral_processor.Spectral_processor(self.path_to_main)
        self.hardware_ports=Hardware_ports()
        from Scripts.ScanningProcessOSA import ScanningProcess
        self.scanningProcess=ScanningProcess()
        # from Visualization.Powermeter_painter import Powermeter_painter
        # self.powermeter_graph=Powermeter_painter()
        # self.add_thread([self.powermeter_graph])
        self.add_thread([self.painter,self.logger,self.analyzer,self.spectral_processor,self.scanningProcess])
        
        
        self.ui.tabWidget_instruments.currentChanged.connect(self.on_TabChanged_instruments_changed)
        self.init_hardware_parameters_toolbox()
        self.init_OSA_interface()
        self.init_analyzer_interface()
        self.init_laser_interface()
        self.init_logger_interface()
        self.init_painter_interface()
        self.init_powermeter_interface()
        self.init_processing_interface()
        self.init_scanning_interface()
        self.init_scope_interface()
        self.init_stages_interface()
        self.init_piezo_stage_interface()
        self.piezo_stage_connected = 0
        self.init_menu_bar()
        
        self.load_parameters_from_file()
        
    def logText(self, text):
        self.ui.LogField.append(">" + text)
        
    def logWarningText(self, text):
        self.ui.LogField.append("<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\" >"
                             + ">" + text + "</span>")
        
        
    def init_menu_bar(self):
        self.ui.action_save_parameters.triggered.connect(self.save_parameters_to_file)
        self.ui.action_load_parameters.triggered.connect(self.load_parameters_from_file)
        self.ui.action_delete_all_figures.triggered.connect(self.delete_all_figures)
        self.ui.action_delete_all_measured_spectral_data.triggered.connect(self.delete_data_from_folders)
        
    def init_hardware_parameters_toolbox(self):
        self.ui.pushButton_set_hardware_ports.clicked.connect(self.on_pushButton_set_hardware_ports)
# =============================================================================
#         Stages interface
# =============================================================================
    def init_stages_interface(self):
        self.ui.pushButton_StagesConnect.pressed.connect(self.connect_stages)
        self.X_0,self.Y_0,self.Z_0=[0,0,0]
        self.ui.pushButton_MovePlusX.pressed.connect(
            lambda :self.setStageMoving('X',float(self.ui.lineEdit_StepX.text())))
        self.ui.pushButton_MoveMinusX.pressed.connect(
            lambda :self.setStageMoving('X',-1*float(self.ui.lineEdit_StepX.text())))
        self.ui.pushButton_MovePlusY.pressed.connect(
            lambda :self.setStageMoving('Y',float(self.ui.lineEdit_StepY.text())))
        self.ui.pushButton_MoveMinusY.pressed.connect(
            lambda :self.setStageMoving('Y',-1*float(self.ui.lineEdit_StepY.text())))
        self.ui.pushButton_MovePlusZ.pressed.connect(
            lambda :self.setStageMoving('Z',float(self.ui.lineEdit_StepZ.text())))
        self.ui.pushButton_MoveMinusZ.pressed.connect(
            lambda :self.setStageMoving('Z',-1*float(self.ui.lineEdit_StepZ.text())))
        self.ui.pushButton_zero_position_X.pressed.connect(lambda: self.on_pushButton_zeroingPositions('X'))
        self.ui.pushButton_zero_position_Y.pressed.connect(lambda: self.on_pushButton_zeroingPositions('Y'))
        self.ui.pushButton_zero_position_Z.pressed.connect(lambda: self.on_pushButton_zeroingPositions('Z'))
        self.ui.pushButton_zeroing_stages.pressed.connect(self.zeroing_stages)
# =============================================================================
#         Piezo Stage interface
# =============================================================================
    def init_piezo_stage_interface(self):
        self.ui.pushButton_PiezoStageConnect.clicked.connect(self.connect_PiezoStages)
        self.ui.pushButton_SetZero.clicked.connect(lambda: self.on_pushButton_zeroingPositions('Piezo'))
        self.ui.pushButton_piezo_decr_Z.pressed.connect(lambda: self.setPiezoStageMoving(-float(self.ui.lineEdit_piezo_step.text())))
        self.ui.pushButton_piezo_incr_Z.pressed.connect(lambda: self.setPiezoStageMoving(float(self.ui.lineEdit_piezo_step.text())))
        self.force_piezo_stage_move[float].connect(lambda i:self.piezo_stage.move_by(i))
# =============================================================================
#         # OSA interface
# =============================================================================
    def init_OSA_interface(self):        
        self.ui.pushButton_OSA_connect.pressed.connect(self.connect_OSA)
        self.ui.pushButton_OSA_Acquire.pressed.connect(
            self.on_pushButton_acquireSpectrum_pressed)
        self.ui.pushButton_OSA_AcquireAll.pressed.connect(
            self.on_pushButton_AcquireAllSpectra_pressed)
        self.ui.pushButton_OSA_AcquireRep.clicked[bool].connect(
            self.on_pushButton_acquireSpectrumRep_pressed)
        
        self.ui.pushButton_APEX_TLS.clicked[bool].connect(lambda x: self.OSA.tls.On() if x else self.OSA.tls.Off())
        self.ui.pushButton_APEX_calibration.clicked.connect(lambda : self.OSA.WavelengthCalib())
                

        self.ui.label_Luna_mode.setVisible(False)
        self.ui.comboBox_Luna_mode.setVisible(False)
        self.ui.comboBox_Luna_mode.currentTextChanged.connect(lambda : self.enable_scanning_process())
        self.ui.comboBox_Type_of_OSA.currentTextChanged.connect(self.features_visibility)
        self.ui.pushButton_set_max_OSA_range.pressed.connect(self.set_max_OSA_range)
        
        
        self.ui.lineEdit_StartWavelength.editingFinished.connect(
            lambda:self.OSA.change_range(start_wavelength=float(self.ui.lineEdit_StartWavelength.text())) 
            if (isfloat(self.ui.lineEdit_StartWavelength.text())) else 0)
        self.ui.lineEdit_StopWavelength.editingFinished.connect(
            lambda:self.OSA.change_range(stop_wavelength=float(self.ui.lineEdit_StopWavelength.text())) 
            if (isfloat(self.ui.lineEdit_StopWavelength.text())) else 0)      
        

        

# =============================================================================
#         # scope interface
# =============================================================================
    def init_scope_interface(self):   
        self.ui.pushButton_scope_connect.pressed.connect(self.connect_scope)
        self.ui.pushButton_scope_single.pressed.connect(
            self.on_pushButton_scope_single_measurement)
        self.ui.pushButton_scope_repeat.clicked[bool].connect(
            self.on_pushButton_scope_repeat__pressed)
        
# =============================================================================
#         powermeter interface
# =============================================================================
    def init_powermeter_interface(self):        
        self.ui.pushButton_powermeter_connect.pressed.connect(self.connect_powermeter)
        self.ui.pushButton_powermeter_graph.clicked[bool].connect(self.run_powermeter_graph)
        self.ui.checkBox_powermeter_for_laser_scanning.setEnabled(True)
        
        


# =============================================================================
#         # painter and drawing interface
# =============================================================================
    def init_painter_interface(self):

        self.ui.checkBox_FreezeSpectrum.stateChanged.connect(self.on_stateChangeOfFreezeSpectrumBox)
        self.ui.checkBox_ApplyFFTFilter.stateChanged.connect(self.on_stateChangeOfApplyFFTBox)
        self.ui.checkBox_HighRes.stateChanged.connect(self.on_stateChangeOfIsHighResolution)
        self.ui.pushButton_getRange.pressed.connect(self.on_pushButton_getRange)


# =============================================================================
#         saving interface
# =============================================================================
    def init_logger_interface(self):
        self.ui.pushButton_save_data.pressed.connect(self.on_pushButton_save_data)
        self.logger.S_print[str].connect(self.logText)
        self.logger.S_print_error[str].connect(self.logWarningText)
        

# =============================================================================
#         #scanning process
# =============================================================================
    def init_scanning_interface(self):        
        self.ui.pushButton_scan_in_space.toggled[bool].connect(self.on_pushButton_scan_in_space)
        self.ui.pushButton_set_scanning_parameters.clicked.connect(self.on_pushButton_set_scanning_parameters)

# =============================================================================
#         # processing
# =============================================================================
    def init_processing_interface(self):
        self.ui.pushButton_process_measured_spectral_data.pressed.connect(self.on_Push_Button_ProcessSpectra)
        self.ui.pushButton_processTDData.pressed.connect(self.on_pushButton_ProcessTD)
        self.ui.pushButton_choose_folder_to_process.clicked.connect(self.choose_folder_for_spectral_processor)
                
        self.ui.pushButton_process_arb_spectral_data.clicked.connect(self.process_arb_spectral_data_clicked)
        self.ui.pushButton_process_arb_TD_data.clicked.connect(self.process_arb_TD_data_clicked)
        self.ui.pushButton_plotSampleShape.clicked.connect(lambda:self.spectral_processor.plot_sample_shape())
            
        self.ui.pushButton_plotSampleShape_arb_data.clicked.connect(lambda:self.spectral_processor.plot_sample_shape())
        self.ui.pushButton_set_spectral_processor_parameters.clicked.connect(self.on_pushButton_set_spectral_processor_parameters)
        self.ui.pushButton_set_spectral_processor_parameters_2.clicked.connect(self.on_pushButton_set_spectral_processor_parameters)
        
        self.spectral_processor.S_print[str].connect(self.logText)
        self.spectral_processor.S_print_error[str].connect(self.logText)
# =============================================================================
#         # analyzer logic
# =============================================================================

    def init_analyzer_interface(self):
        '''
        Create connection between analyzer buttons and corresponding methods
        Note that connectiong through "lambda: " is needed otherwise matplotlib may crash as plots would be plotted in different threads

        Returns
        -------
        None.

        '''

        self.ui.pushButton_analyzer_choose_plotting_param_file.clicked.connect(
            self.choose_file_for_analyzer_plotting_parameters)
               
    # self.painter.FilterLowFreqEdge=float(self.ui.lineEdit_FilterLowFreqEdge.text())
    #         self.painter.FilterHighFreqEdge=float(self.ui.lineEdit_FilterHighFreqEdge.text())
    #         self.painter.FFTPointsToCut=int(self.ui.lineEdit_FilterPointsToCut.text())
    #     else:
        
        self.ui.lineEdit_FilterLowFreqEdge.editingFinished.connect(lambda: setattr(self.analyzer, 'FFTFilter_low_freq_edge', float(self.ui.lineEdit_FilterLowFreqEdge.text())))
        self.ui.lineEdit_FilterHighFreqEdge.editingFinished.connect(lambda: setattr(self.analyzer, 'FFTFilter_high_freq_edge', float(self.ui.lineEdit_FilterHighFreqEdge.text())))
        
        
        
        self.ui.pushButton_analyzer_choose_file_spectrogram.clicked.connect(
            self.choose_file_for_analyzer)
        self.ui.pushButton_analyzer_plot_ERV_from_file.clicked.connect(self.plot_ERV_from_file)
        self.ui.pushButton_analyzer_plotSampleShape.clicked.connect(lambda: self.analyzer.plot_sample_shape())
        self.ui.pushButton_analyzer_plot2D.clicked.connect(lambda: self.analyzer.plot_spectrogram())
        self.ui.pushButton_analyzer_plotSlice.clicked.connect(lambda: self.analyzer.plot_slice(float(self.ui.lineEdit_slice_position.text())))
        self.ui.pushButton_analyzer_plot_single_spectrum.clicked.connect(lambda: self.analyzer.plot_single_spectrum())
        self.ui.pushButton_analyzer_extract_ERV.clicked.connect(lambda: self.analyzer.extract_ERV())
        self.ui.pushButton_analyzer_get_modes_params.clicked.connect(lambda: self.analyzer.get_modes_parameters())
        self.ui.pushButton_analyzer_quantum_numbers_fitter.clicked.connect(lambda: self.analyzer.run_quantum_numbers_fitter())

        
        self.ui.pushButton_analyzer_apply_FFT_filter.clicked.connect(lambda: self.analyzer.apply_FFT_to_spectrogram())
        
        self.ui.pushButton_analyzer_choose_single_spectrum.clicked.connect(
            self.choose_single_spectrum_file_for_analyzer)
        self.ui.pushButton_analyzer_analyze_spectrum.clicked.connect(lambda: self.analyzer.analyze_spectrum(self.analyzer.single_spectrum_figure) 
                                                                     if (self.analyzer.single_spectrum_figure is not None) else
                                                                     self.analyzer.analyze_spectrum(self.painter.figure))
        
        # self.ui.pushButton_analyze_spectrum.clicked.connect(lambda: self.analyzer.analyze_spectrum( self.painter.figure))  
        self.ui.pushButton_analyzer_apply_FFT_filter_single_spectrum.clicked.connect(lambda: self.analyzer.apply_FFT_to_spectrum(self.analyzer.single_spectrum_figure))
        self.ui.pushButton_analyzer_save_single_spectrum.clicked.connect(self.analyzer.save_single_spectrum)        
        self.ui.pushButton_analyzer_resave_SNAP.clicked.connect(lambda : self.analyzer.resave_SNAP(self.ui.comboBox_analyzer_resave_type.currentText()))        
        self.ui.pushButton_set_analyzer_parameters.clicked.connect(self.on_pushButton_set_analyzer_parameters)
        self.ui.pushButton_delete_slice.clicked.connect(self.delete_slice_from_spectrogram)
        
        
        '''
        osc logic
        '''
        self.ui.pushButton_analyzer_plot_single_oscillogram.clicked.connect(lambda: self.analyzer.plot_single_oscillogram())
        self.ui.pushButton_analyzer_choose_single_oscillogram.clicked.connect(
            self.choose_single_oscillogram_for_analyzer)
        self.ui.pushButton_analyzer_fit_oscillogram.clicked.connect(lambda: self.analyzer.analyze_oscillogram(self.analyzer.single_oscillogram_figure) 
                                                                     if (self.analyzer.single_oscillogram_figure is not None) else
                                                                     self.analyzer.analyze_oscillogram(self.painter.figure))
        
        
        
        
        self.analyzer.S_print[str].connect(self.logText)
        self.analyzer.S_print_error[str].connect(self.logWarningText)
        
        # self.ui.pushButton_analyzer_save_as_pkl3d.clicked.connect(lambda: self.analyzer.save_as_pkl3d())
        
        # self.ui.pushButton_analyzer_save_cropped.clicked.connect(lambda: self.analyzer.save_cropped_data())

# =============================================================================
#         Pure Photonics Tunable laser
# =============================================================================
    def init_laser_interface(self):        
        self.ui.pushButton_laser_connect.clicked.connect(self.connect_laser)
        self.ui.pushButton_laser_On.clicked[bool].connect(self.on_pushButton_laser_On)
        self.ui.comboBox_laser_mode.currentIndexChanged.connect(self.change_laser_mode)
        self.ui.lineEdit_laser_fine_tune.editingFinished.connect(self.laser_fine_tuning)
        self.ui.pushButton_scan_laser_wavelength.clicked[bool].connect(self.laser_scanning)
        self.ui.pushButton_hold_laser_wavelength.clicked[bool].connect(self.laser_scaning_hold_wavelength)
        self.ui.pushButton_sweep_laser_wavelength.clicked[bool].connect(self.laser_sweeping)

# =============================================================================
#   interface methods
# =============================================================================
    
    def on_pushButton_set_hardware_ports(self):
        '''
        open dialog with hardware ports
        '''
        d = self.hardware_ports.get_attributes()
        from Windows.UIs.hardware_dialogUI import Ui_Dialog
        hardware_dialog = QDialog()
        ui = Ui_Dialog()
        ui.setupUi(hardware_dialog)
        set_widget_values(hardware_dialog,d)
        if hardware_dialog.exec_() == QDialog.Accepted:
            params=get_widget_values(hardware_dialog)
            self.hardware_ports.set_attributes(params)

    def connect_scope(self):
        '''
        create connection to scope
        use 'old' interface by Ilya or 'new' interface by Artem 

        Returns
        -------
        None.

        '''
        
        importlib.reload(Common.Consts)
        
        interface='new'
        try:
            if interface=='new':
                if self.ui.comboBox_type_of_scope.currentText()=='Keysight 4GHz':
                    from Hardware.scope import Scope
                    self.scope = Scope(self.hardware_ports.scope, protocol = 'inst0') # or Common.Consts.Scope.NAME
                elif self.ui.comboBox_type_of_scope.currentText()=='Rigol':
                    from Hardware.scope_rigol import Scope
                    self.scope=Scope(self.hardware_ports.scope_Rigol)
            elif interface=='old':
                from Hardware.KeysightOscilloscope import Scope
                self.scope=Scope(Common.Consts.Scope.HOST)
            self.add_thread([self.scope])
            self.scope.received_data.connect(self.painter.set_data)
            self.ui.tabWidget_instruments.setEnabled(True)
            self.ui.tabWidget_instruments.setCurrentIndex(1)
            self.ui.groupBox_scope_control.setEnabled(True)
            self.enable_scanning_process()
            widgets = (self.ui.horizontalLayout_3.itemAt(i).widget()
                       for i in range(self.ui.horizontalLayout_3.count()))
            for i,widget in enumerate(widgets):
                widget.setChecked(self.scope.channels_states[i])
                widget.stateChanged.connect(self.update_scope_channel_state)
            self.painter.TypeOfData='FromScope'
            self.logText('Connected to scope')
        
        except Exception as e:
            print(e)
            self.logWarningText('Connection to scope failed')

    def update_scope_channel_state(self):
        widgets = (self.ui.horizontalLayout_3.itemAt(i).widget()
                   for i in range(self.ui.horizontalLayout_3.count()))
        for i,widget in enumerate(widgets):
            self.scope.channels_states[i]=widget.isChecked()
            self.scope.set_channel_state(i+1,widget.isChecked())

    
    def features_visibility(self, OSA):
        try:
            if OSA=='Luna':
                self.ui.groupBox_features.setVisible(True)
                flag = True
            elif OSA=='APEX':
                self.ui.groupBox_features.setVisible(True)
                flag = False
            else:
                # self.ui.groupBox_features.setVisible(False)
                return
            self.ui.label_Luna_mode.setVisible(flag)
            self.ui.comboBox_Luna_mode.setVisible(flag)
            self.ui.label_29.setVisible(not flag)
            self.ui.comboBox_APEX_mode.setVisible(not flag)
        except:
            self.logWarningText(sys.exc_info())
    
    
    
    def connect_OSA(self):
        '''
        set connection to OSA: Luna, Yokogawa, ApEx Technologies or Astro interrogator

        Returns
        -------
        None.

        '''
        try:
            if self.ui.comboBox_Type_of_OSA.currentText()=='Luna':
                from Hardware.ova5000 import Luna
                self.OSA=Luna(port=self.hardware_ports.LUNA)  
            if self.ui.comboBox_Type_of_OSA.currentText()=='Yokogawa':
                from Hardware.YokogawaOSA import OSA_AQ6370
                HOST = self.hardware_ports.Yokogawa
                PORT = 10001
                timeout_short = 0.2
                timeout_long = 100
                self.OSA=OSA_AQ6370(None,HOST, PORT, timeout_long,timeout_short)
    #            self.OSA.received_spectra.connect(self.painter.set_spectra)
            elif self.ui.comboBox_Type_of_OSA.currentText()=='Astro interrogator':
                from Hardware.Interrogator import Interrogator
                cfg = Config("config_interrogator.json")
                self.repeatmode=False
                self.OSA = Interrogator(
                    parent=None,
                    host=self.hardware_ports.interrogator,
                    command_port=Common.Consts.Interrogator.COMMAND_PORT,
                    data_port=Common.Consts.Interrogator.DATA_PORT,
                    short_timeout=Common.Consts.Interrogator.SHORT_TIMEOUT,
                    long_timeout=Common.Consts.Interrogator.LONG_TIMEOUT,
                    config=cfg.config["channels"])
    
                self.ui.comboBox_interrogatorChannel.currentIndexChanged.connect(
                    self.OSA.set_channel_num)
                self.ui.comboBox_interrogatorChannel.setEnabled(True)
                self.ui.pushButton_OSA_AcquireRepAll.setEnabled(True)
                self.ui.pushButton_OSA_AcquireAll.setEnabled(True)
    
    
            elif self.ui.comboBox_Type_of_OSA.currentText()=='APEX':

                from Hardware.APEX_OSA import APEX_OSA_with_additional_features

                self.OSA = APEX_OSA_with_additional_features(self.hardware_ports.APEX)

                self.ui.checkBox_HighRes.setChecked(self.OSA.IsHighRes)
                self.ui.comboBox_APEX_mode.setEnabled(True)
                self.ui.pushButton_APEX_TLS.setEnabled(True)
                self.ui.pushButton_APEX_calibration.setEnabled(True)
                self.ui.comboBox_APEX_mode.setCurrentIndex(self.OSA.GetMode()-3)
                self.ui.comboBox_APEX_mode.currentIndexChanged[int].connect(lambda x: self.OSA.SetMode(x+3))
                self.spectral_processor.isInterpolation=True
                if self.OSA.tls.GetStatus()=='ON':
                    self.ui.pushButton_APEX_TLS.setChecked(True)
    
            self.add_thread([self.OSA])
            self.OSA.received_spectrum.connect(self.painter.set_data)
    
            self.force_OSA_acquire.connect(self.OSA.acquire_spectrum)
            self.ui.tabWidget_instruments.setEnabled(True)
            self.ui.tabWidget_instruments.setCurrentIndex(0)
            self.ui.lineEdit_StartWavelength.setText(str(self.OSA._StartWavelength))
            self.ui.lineEdit_StopWavelength.setText(str(self.OSA._StopWavelength))
    
            self.ui.groupBox_OSA_control.setEnabled(True)
            self.ui.checkBox_OSA_for_laser_scanning.setEnabled(True)
            self.logText('Connected with OSA')
            self.on_pushButton_acquireSpectrum_pressed()
            self.enable_scanning_process()
            self.painter.TypeOfData='FromOSA'
            self.OSA.S_print_error[str].connect(self.logWarningText)
        except Exception as e:
            print(e)
            self.logWarningText('Connection to OSA failed')

    def connect_stages(self):
        '''
        set connection to either Thorlabs or Standa stages 

        Returns
        -------
        None.

        '''
        try:
            if self.ui.comboBox_Type_of_Stages.currentText()=='3x Standa':
                from Hardware.MyStanda import StandaStages
                self.stages=StandaStages()
            elif self.ui.comboBox_Type_of_Stages.currentText()=='2x Thorlabs (Cube+NRT100)':
                import Hardware.MyThorlabsStages
                self.stages=Hardware.MyThorlabsStages.ThorlabsStages()
                self.ui.pushButton_MovePlusY.setEnabled(False)
                self.ui.pushButton_MoveMinusY.setEnabled(False)
                
            elif self.ui.comboBox_Type_of_Stages.currentText()=='2x Thorlabs (2 Cubes)':
                import Hardware.MyThorlabsStages_2_Cubes
                self.stages=Hardware.MyThorlabsStages_2_Cubes.ThorlabsStages_2_Cubes()
                self.ui.pushButton_MovePlusY.setEnabled(False)
                self.ui.pushButton_MoveMinusY.setEnabled(False)
            elif self.ui.comboBox_Type_of_Stages.currentText()=='3x Physik Instrumente':
                import Hardware.PIStages
                self.stages=Hardware.PIStages.PIStages()
    
            if self.stages.isConnected>0:
                self.logText('Connected to stages')
                self.add_thread([self.stages])
                self.stages.set_zero_positions(self.logger.load_zero_position()[0:3])
                self.stages.stopped.connect(self.update_indicated_positions)
                self.force_stage_move[str,float].connect(lambda S,i:self.stages.shiftOnArbitrary(S,i))
                self.update_indicated_positions()
             
                self.ui.groupBox_stand.setEnabled(True)

    
                self.enable_scanning_process()
        except Exception as e:
            print(e)
            self.logWarningText('Connection to stages failed')

    def zeroing_stages(self):
        '''
        move stages to zero position

        Returns
        -------
        None.

        '''
        self.stages.move_home()
        
    
    def connect_PiezoStages(self):
        try:
            self.piezo_stage = PiezoStage(self.hardware_ports.piezo_stage, 9600)
            self.piezo_stage_connected = 1
            # self.ui.label_abs_position.setText(f'Abs:{round(self.piezo_stage.abs_position, 3)} μm')
            self.logText('Connected to piezo stage')
            self.add_thread([self.piezo_stage])
            self.ui.label_PiezoStage_status.setStyleSheet("QLabel {\n"
            "    \n"
            "    background-color: rgb(0, 255, 0);\n"
            "}")
            self.piezo_stage.A18_SetChannelOpenOrClose(False)
            self.piezo_stage.zero_position=self.logger.load_zero_position()[3]
            self.piezo_stage.update_position()
            # self.ui.label_rel_position.setText(f'Rel: {round(self.piezo_stage.relative_position, 3)} μm')
            self.piezo_stage.stopped.connect(self.update_indicated_positions)
            self.update_indicated_positions()
            self.ui.groupBox_piezo.setEnabled(True)
            self.enable_scanning_process()
        except Exception as e:
            print(e)
            self.logWarningText('Connection to Piezo stages failed')
            self.ui.label_PiezoStage_status.setStyleSheet("QLabel {\n"
            "    \n"
            "    background-color: rgb(255, 15, 15);\n"
            "}")
  

    
    # def set_ZeroPosToPiezoStage(self):
    #     if self.piezo_stage_connected == 1:
            
    #     else:
    #         self.logWarningText('Piezo stage is not connected')
            
    
    # def MovePiezoStage(self, direction=1):
    #     if self.piezo_stage_connected == 1:
    #         to_move = float(self.ui.lineEdit_Step.text())*direction
    #         if 0 <= self.piezo_stage.relative_position + to_move <= 202:
    #             self.piezo_stage.abs_position += to_move
    #             self.piezo_stage.relative_position += to_move
    #             self.piezo_stage.A01_SendMove(self.piezo_stage.relative_position)
    #         _, self.piezo_stage.relative_position = self.piezo_stage.A06_ReadDataMove()
    #         _, self.piezo_stage.relative_position = self.piezo_stage.A06_ReadDataMove()
    #         self.ui.label_abs_position.setText(f'Abs:{round(self.piezo_stage.abs_position, 3)} μm')
    #         self.ui.label_rel_position.setText(f'Rel:{round(self.piezo_stage.relative_position, 3)} μm')
    #     else:
    #         self.logWarningText('Piezo stage is not connected')
    
    
    def connect_powermeter(self):
        '''
        set connection to powermeter Thorlabs

        Returns
        -------
        None.

        '''
        try:
            from Hardware import ThorlabsPM100
            self.powermeter=ThorlabsPM100.PowerMeter(self.hardware_ports.powermeter_serial_number)
            if self.powermeter is not None:
                self.ui.checkBox_powermeter_for_laser_scanning.setEnabled(True)
                self.ui.pushButton_powermeter_graph.setEnabled(True)
                self.logText('NOTE: if you want to use PM Graph feature, change the iPython Graphic preferences from ''Automatic'' to ''Tkinter''')
        except Exception as e:
            print(e)
            self.logWarningText('Connection to power meter failed')

    def connect_laser(self):
        '''
        set connection to Pure Photonics tunable laser
        Using 'serial' or 'pyvisa' interface 
        Returns
        -------
        None.

        '''
        interface='serial'
        COMPort=self.hardware_ports.laser_Pure_Photonics
        try:
            if self.ui.comboBox_laser_protocol_type.currentText()=='pyvisa':
                from Hardware.PurePhotonicsLaser_pyvisa import Laser   
            elif self.ui.comboBox_laser_protocol_type.currentText()=='serial':
                from Hardware.PurePhotonicsLaser_serial import Laser
            self.laser=Laser(COMPort)
            
            self.laser.S_print[str].connect(self.logText)
            self.laser.S_print_error[str].connect(self.logWarningText)
            
            self.laser.fineTuning(0)
            self.ui.pushButton_laser_On.setEnabled(True)
            # self.ui.groupBox_laser_sweeping.setEnabled(False)
            # self.ui.groupBox_laser_scanning.setEnabled(False)
    #            self.add_thread([self.laser])
            from Scripts.ScanningProcessLaser import LaserScanningProcess        
            self.laser_scanning_process=LaserScanningProcess(OSA=(self.OSA if self.ui.checkBox_OSA_for_laser_scanning.isChecked() else None),
                laser=self.laser,
                powermeter=(self.powermeter if self.ui.checkBox_powermeter_for_laser_scanning.isChecked() else None),
                step=float(self.ui.lineEdit_laser_lambda_scanning_step.text()),
                wavelength_start=float(self.ui.lineEdit_laser_lambda.text()),
                detuning=0,   
                max_detuning=float(self.ui.lineEdit_laser_scanning_max_detuning.text()),
                file_to_save='ProcessedData\\Power_from_powermeter_VS_laser_wavelength.laserdata')
            self.add_thread([self.laser_scanning_process])
            self.laser_scanning_process.S_updateCurrentWavelength.connect(lambda S:self.ui.label_current_laser_wavelength.setText(S))
            self.laser_scanning_process.S_update_fine_tune.connect(lambda S:self.ui.lineEdit_laser_fine_tune.setText(S))
            self.laser_scanning_process.S_saveData.connect(lambda Data,prefix: self.logger.save_data(Data,prefix,0,0,0,0,'FromOSA'))
            self.laser_scanning_process.S_update_main_wavelength.connect(lambda S:self.ui.lineEdit_laser_lambda.setText(S))
            self.laser_scanning_process.S_finished.connect(lambda: self.ui.pushButton_scan_laser_wavelength.setChecked(False))
            self.laser_scanning_process.S_finished.connect(
                    lambda : self.laser_scanning(False))
            self.force_laser_scanning_process.connect(self.laser_scanning_process.run)
            self.laser_scanning_process.S_print[str].connect(self.logText)
            self.laser_scanning_process.S_print_error[str].connect(self.logWarningText)
            self.logText('Connected to Pure Photonics Laser')
        except Exception as e:
            print(e)
            self.logWarningText('Connection to laser failed. Check the COM port number')
            
    
    def run_powermeter_graph(self,pressed:bool):
        '''
        plot live graph with data from powermeter
        
        Parameters
        ----------
        pressed : bool
            DESCRIPTION. current state of the button


        '''
        if pressed:
            # from Visualization.Powermeter_painter import Powermeter_painter
            # self.powermeter_graph=Powermeter_painter(self.powermeter)
            # self.add_thread([self.powermeter_graph])
            
            self.painter.create_powermeter_plot()
            self.powermeter.power_received.connect(self.painter.update_powermeter_plot)
            self.painter.powermeter_canvas_updated.connect(self.powermeter.get_power)
            self.painter.powermeter_canvas_updated.emit()
        else:
            self.powermeter.power_received.disconnect(self.painter.update_powermeter_plot)
            self.painter.powermeter_canvas_updated.disconnect(self.powermeter.get_power)
            # self.painter.delete_powermeter_plot()
            

    def on_pushButton_laser_On(self,pressed:bool):
        '''
        switch tunable laser between ON and OFF state

        Parameters
        ----------
        pressed : bool
            DESCRIPTION. current state of the button

        Returns
        -------
        None.

        '''
        if pressed:
            # self.ui.pushButton_texscan_laser_wavelength.setEnabled(True)
            self.ui.pushButton_scan_laser_wavelength.setEnabled(True)
            self.ui.groupBox_laser_sweeping.setEnabled(True)
            self.laser.setPower(float(self.ui.lineEdit_laser_power.text()))
            self.laser.setWavelength(float(self.ui.lineEdit_laser_lambda.text()))
            self.laser.setOn()
            self.ui.comboBox_laser_mode.setEnabled(True)

            self.ui.lineEdit_laser_fine_tune.setEnabled(True)
            self.laser.tuning=0
            self.ui.lineEdit_laser_fine_tune.setText('0')
            self.ui.label_current_laser_wavelength.setText('{:.5f}'.format(self.laser.main_wavelength))
            self.ui.lineEdit_laser_lambda.setEnabled(False) 
            self.ui.lineEdit_laser_power.setEnabled(False)

        else:
            self.laser.setOff()
            self.ui.pushButton_scan_laser_wavelength.setEnabled(False)
            self.ui.groupBox_laser_sweeping.setEnabled(False)
            # self.ui.pushButton_scan_laser_wavelength.setEnabled(False)
            self.ui.comboBox_laser_mode.setEnabled(False)
            self.ui.lineEdit_laser_fine_tune.setEnabled(False)
            self.ui.lineEdit_laser_lambda.setEnabled(True) 
            self.ui.lineEdit_laser_power.setEnabled(True)

    def change_laser_mode(self):
        '''
        change between Whisper, Dittering, and No Dittering modes of Pure Photonics Laser

        Returns
        -------
        None.

        '''
        try:
            self.laser.setMode(self.ui.comboBox_laser_mode.currentText())
        except Exception as e:
            print(e)
            self.logWarningText('Laser mode change failed')

    def laser_fine_tuning(self):
        '''
        fine tune of the Pure Photonics laser for the spectral shift specified at 
        lineEdit_laser_fine_tune

        Returns
        -------
        None.

        '''
        try:
            tuning=float(self.ui.lineEdit_laser_fine_tune.text())
            self.laser.fineTuning(tuning)
            self.ui.label_current_laser_wavelength.setText('{:.5f}'.format(self.laser.main_wavelength+tuning*1e-3))
        except AttributeError as e:
            pass
            # print(e)

    def laser_scanning(self,pressed:bool):
        '''
        run scan of the Pure Photonics laser wavelength and save data from either OSA or powermeter at each laser wavelength
        Spectra are saved to 'SpectralData\\'
        Power VS wavelength is saved to 'ProcessedData\\Power_from_powermeter_VS_laser_wavelength.txt' when scanning is stopped

        Parameters
        ----------
        pressed : bool
            DESCRIPTION. Current state of the scanning button

        Returns
        -------
        None.

        '''
        if pressed:
            self.ui.groupBox_laser_operation.setEnabled(False)
            if self.ui.checkBox_OSA_for_laser_scanning.isChecked()==True:
                self.ui.tabWidget_instruments.setEnabled(False)
            self.ui.pushButton_scan_in_space.setEnabled(False)
            self.ui.pushButton_sweep_laser_wavelength.setEnabled(False)
            self.ui.pushButton_hold_laser_wavelength.setEnabled(True)
            # self.laser_scanning_process.initialize_laser()
            self.laser_scanning_process.powermeter=self.powermeter
            self.laser_scanning_process.OSA=self.OSA
            
            self.laser_scanning_process.powermeter_for_laser_scanning=self.ui.checkBox_powermeter_for_laser_scanning.isChecked()
            self.laser_scanning_process.OSA_for_laser_scanning=self.ui.checkBox_OSA_for_laser_scanning.isChecked()
            self.laser_scanning_process.step=float(self.ui.lineEdit_laser_lambda_scanning_step.text())
            self.laser_scanning_process.wavelength_start=float(self.ui.lineEdit_laser_lambda.text())
            self.laser_scanning_process.tuning=float(self.ui.lineEdit_laser_fine_tune.text())
            self.laser_scanning_process.max_detuning=float(self.ui.lineEdit_laser_scanning_max_detuning.text())

            self.force_laser_scanning_process.emit()
            self.logText('Start laser scanning')

        else:
            self.laser_scanning_process.is_running=False
            if self.ui.checkBox_OSA_for_laser_scanning.isChecked()==True:
                self.ui.tabWidget_instruments.setEnabled(True)
            self.ui.groupBox_laser_operation.setEnabled(True)
            # self.ui.pushButton_laser_On.setEnabled(True)
            self.ui.pushButton_scan_in_space.setEnabled(True)
            self.ui.pushButton_sweep_laser_wavelength.setEnabled(True)
            self.ui.pushButton_hold_laser_wavelength.setEnabled(False)
            
            
    def laser_scaning_hold_wavelength(self,pressed:bool):
        '''
        hold PurePhotonics laser scanning process, and current wavelength unchanged, and save data continously

        Parameters
        ----------
        pressed : bool
            DESCRIPTION. Current state of the hold button within scanning proccess

        Returns
        -------
        None.
       
        '''
        self.laser_scanning_process.hold_wavelength=pressed
   

    def laser_sweeping(self,pressed:bool):
        '''
        run PurePhotonics laser 'fast' scanning without saving data

        Parameters
        ----------
        pressed : bool
            DESCRIPTION. Current state of the sweeping button

        Returns
        -------
        None.

        '''
        if pressed:
            self.ui.pushButton_laser_On.setEnabled(False)
            from Scripts.ScanningProcessLaser import LaserSweepingProcess
            self.laser_sweeping_process=LaserSweepingProcess(laser=self.laser,
                laser_power=float(self.ui.lineEdit_laser_power.text()),
                scanstep=float(self.ui.lineEdit_laser_lambda_sweeping_step.text()),
                wavelength_central=float(self.ui.lineEdit_laser_lambda_sweeping_central.text()),
                max_detuning=float(self.ui.lineEdit_laser_sweeping_max_detuning.text()),
                delay=float(self.ui.lineEdit_laser_lambda_sweeping_delay.text()))
            self.logText(float(self.ui.lineEdit_laser_lambda_sweeping_delay.text()))
            self.add_thread([self.laser_sweeping_process])
            self.laser_sweeping_process.S_updateCurrentWavelength.connect(
                lambda S:self.ui.label_current_scanning_laser_wavelength.setText(S))
            self.force_laser_sweeping_process.connect(self.laser_sweeping_process.run)
            self.logText('Start laser sweeping')
            self.laser_sweeping_process.S_finished.connect(
                self.ui.pushButton_sweep_laser_wavelength.toggle)
            self.laser_sweeping_process.S_finished.connect(lambda : self.laser_sweeping(False))
            self.ui.pushButton_scan_laser_wavelength.setEnabled(False)
            self.force_laser_sweeping_process.emit()

        else:
            self.ui.pushButton_laser_On.setEnabled(True)
            self.ui.pushButton_scan_laser_wavelength.setEnabled(True)
            self.laser_sweeping_process.is_running=False
            del self.laser_sweeping_process

 

    @pyqtSlotWExceptions()
    def on_equipment_ready(self, is_ready):
        self.ui.groupBox_theExperiment.setEnabled(is_ready)


    def setStageMoving(self,key,step):
        self.force_stage_move.emit(key,step)
        
    def setPiezoStageMoving(self,step):
        self.force_piezo_stage_move.emit(step)

    @pyqtSlotWExceptions("PyQt_PyObject")
    def update_indicated_positions(self):
        try:
            X_abs=(self.stages.abs_position['X'])
            Y_abs=(self.stages.abs_position['Y'])
            Z_abs=(self.stages.abs_position['Z'])
        
            X_rel=(self.stages.relative_position['X'])
            Y_rel=(self.stages.relative_position['Y'])
            Z_rel=(self.stages.relative_position['Z'])
        except:
            X_abs,Y_abs,Z_abs=0,0,0
            X_rel,Y_rel,Z_rel=0,0,0
        try:
            piezoZ_abs=self.piezo_stage.abs_position
            piezoZ_rel=self.piezo_stage.relative_position
        except:
            piezoZ_abs,piezoZ_rel=0,0

        self.ui.label_PositionX.setText(str(X_rel))
        self.ui.label_PositionY.setText(str(Y_rel))
        self.ui.label_PositionZ.setText(str(Z_rel))
        self.ui.label_piezo_rel_position.setText('{:.4f}'.format(piezoZ_rel))

        self.ui.label_AbsPositionX.setText(str(X_abs))
        self.ui.label_AbsPositionY.setText(str(Y_abs))
        self.ui.label_AbsPositionZ.setText(str(Z_abs))
        self.ui.label_piezo_abs_position.setText('{:.4f}'.format(piezoZ_abs))



    def on_pushButton_zeroingPositions(self,key='X'):
        try:
            X_0=(self.stages.abs_position['X'])
            Y_0=(self.stages.abs_position['Y'])
            Z_0=(self.stages.abs_position['Z'])
        except:
            X_0,Y_0,Z_0=0,0,0
        try:
            piezoZ_0=self.piezo_stage.abs_position
        except:
            piezoZ_0=0
        if key=='Piezo':
            self.piezo_stage.zero_position=piezoZ_0
        else:
            self.stages.zero_position[key]=self.stages.abs_position[key]
        try:
            self.stages.update_relative_positions()
        except:
                pass
        try:
            self.piezo_stage.update_position()
        except:
            pass
        self.logger.save_zero_position(X_0,Y_0,Z_0,piezoZ_0)
        self.update_indicated_positions()
        
    

    '''
    Interface logic
    '''

    def on_pushButton_scope_single_measurement(self):
        self.scope.acquire()

    def on_pushButton_scope_repeat__pressed(self,pressed):
        if pressed:
            self.painter.ReplotEnded.connect(self.scope.acquire)
            self.ui.pushButton_scope_single.setEnabled(False)
            self.ui.pushButton_scan_in_space.setEnabled(False)
            self.scope.acquire()
        else:
            self.painter.ReplotEnded.disconnect(self.scope.acquire)
#            self.painter.ReplotEnded.disconnect(self.force_scope_acquire)
            self.ui.pushButton_scope_single.setEnabled(True)
            self.ui.pushButton_scan_in_space.setEnabled(True)

    @pyqtSlotWExceptions()
    def on_pushButton_AcquireAllSpectra_pressed(self):
        self.force_OSA_acquireAll.emit()

    @pyqtSlotWExceptions()
    def on_pushButton_acquireSpectrum_pressed(self):
        self.force_OSA_acquire.emit()

    def set_max_OSA_range(self):
        if self.OSA is not None:
            self.OSA.change_range(self.OSA.min_wavelength,self.OSA.max_wavelength)
        else:
             self.logText('OSA not connected')

    @pyqtSlotWExceptions()
    def on_pushButton_acquireSpectrumRep_pressed(self,pressed):
        if pressed:
            self.painter.ReplotEnded.connect(self.force_OSA_acquire)
            self.ui.pushButton_OSA_Acquire.setEnabled(False)
            self.ui.pushButton_OSA_AcquireAll.setEnabled(False)
            self.ui.pushButton_scan_in_space.setEnabled(False)
            self.ui.checkBox_OSA_for_laser_scanning.setChecked(False)
            self.ui.checkBox_OSA_for_laser_scanning.setEnabled(False)
            # self.ui.pushButton_scan_laser_wavelength.setEnabled(False)
            self.force_OSA_acquire.emit()
        else:
            self.painter.ReplotEnded.disconnect(self.force_OSA_acquire)
            self.ui.pushButton_OSA_Acquire.setEnabled(True)
            self.ui.pushButton_OSA_AcquireAll.setEnabled(True)
            self.ui.pushButton_scan_in_space.setEnabled(True)
            # self.ui.pushButton_scan_laser_wavelength.setEnabled(True)
            self.ui.checkBox_OSA_for_laser_scanning.setEnabled(True)

#
#    @pyqtSlotWExceptions()
#    def on_pushButton_AcquireAllSpectraRep_pressed(self,pressed):
#        if pressed:
#
#            self.painter.ReplotEnded.connect(self.on_pushButton_AcquireAllSpectra_pressed)
#            self.ui.pushButton_OSA_AcquireAll.setEnabled(False)
#            self.ui.pushButton_OSA_Acquire.setEnabled(False)
#            self.ui.pushButton_OSA_AcquireRep.setEnabled(False)
#            self.ui.pushButton_scan_in_space.setEnabled(False)
#            self.force_OSA_acquireAll.emit()
#
#        else:
#
#            self.painter.ReplotEnded.disconnect(self.on_pushButton_AcquireAllSpectra_pressed)
#            self.ui.pushButton_OSA_AcquireAll.setEnabled(True)
#            self.ui.pushButton_OSA_Acquire.setEnabled(True)
#            self.ui.pushButton_OSA_AcquireRep.setEnabled(True)
#            self.ui.pushButton_scan_in_space.setEnabled(True)

    @pyqtSlotWExceptions()
    def enable_scanning_process(self):
        '''
        check whether both stages and measuring equipment have been connected to enable scanning features

        Returns
        -------
        None.

        '''
        if ((self.ui.groupBox_stand.isEnabled() or self.ui.groupBox_piezo.isEnabled()) and self.ui.tabWidget_instruments.isEnabled()):
            self.scanningProcess.OSA=self.OSA
            self.scanningProcess.stages=self.stages
            self.scanningProcess.piezo_stage=self.piezo_stage
            self.ui.groupBox_Scanning.setEnabled(True)
            self.ui.tabWidget_instruments.setCurrentIndex(0)
            if self.piezo_stage!=None and self.stages!=None:
                self.scanningProcess.S_saveData.connect(
                            lambda Data,prefix: self.logger.save_data(Data,prefix,
                                self.stages.relative_position['X'], self.stages.relative_position['Y'],
                                self.stages.relative_position['Z'],self.piezo_stage.relative_position,'FromOSA'))
            elif self.stages!=None:
                self.scanningProcess.S_saveData.connect(
                            lambda Data,prefix: self.logger.save_data(Data,prefix,
                                self.stages.relative_position['X'], self.stages.relative_position['Y'],
                                self.stages.relative_position['Z'],0,'FromOSA'))
            elif self.piezo_stage!=None:
                self.scanningProcess.S_saveData.connect(
                            lambda Data,prefix: self.logger.save_data(Data,prefix,
                                0, 0,
                                0,self.piezo_stage.relative_position,'FromOSA'))
            self.scanningProcess.S_finished.connect(lambda: self.ui.pushButton_scan_in_space.setChecked(False))
            self.scanningProcess.S_finished.connect(
                    lambda : self.on_pushButton_scan_in_space(False))
            self.scanningProcess.S_update_status.connect(lambda S: self.ui.label_scanning_index_status.setText(S))
            self.scanningProcess.S_print[str].connect(self.logText)
            self.scanningProcess.S_print_error[str].connect(self.logWarningText)
            
            if (self.ui.comboBox_Type_of_OSA.currentText()=='Luna' and self.ui.comboBox_Luna_mode.currentText() == 'Luna .bin files'):
                self.scanningProcess.LunaJonesMeasurement=True
                self.scanningProcess.S_saveData.connect(lambda data, name: self.OSA.save_binary(
                    f"{self.logger.SpectralBinaryDataFolder}"
                    + f"Sp_{name}_X={self.stages.relative_position['X']}"
                    + f"_Y={self.stages.relative_position['Y']}"
                    + f"_Z={self.stages.relative_position['Z']}_"+f"piezoZ={self.piezo_stage.relative_position}_.bin"))



    def on_pushButton_scan_in_space(self,pressed:bool):
        try:
            if pressed:

                if self.ui.tabWidget_instruments.currentIndex()==0: ## if OSA is active, scanning
                    self.scanningProcess.is_running=True
                    if self.scanningProcess.axis_to_scan=='Piezo':
                        final_position='{:.4f}'.format((self.scanningProcess.stop_file_index-self.scanningProcess.current_file_index)*self.scanningProcess.scanning_step+self.piezo_stage.relative_position)
                    else:
                        final_position=(self.scanningProcess.stop_file_index-self.scanningProcess.current_file_index)*self.scanningProcess.scanning_step+self.stages.relative_position[self.scanningProcess.axis_to_scan]
                    self.ui.label_scanning_final_position.setText(str(final_position))
                    self.ui.label_scanning_axis.setText(self.scanningProcess.axis_to_scan)
                                          ## with OSA
    
            #     elif self.ui.tabWidget_instruments.currentIndex()==1: ## if scope is active,
            #                                                           ## scanning with scope
            #         from Scripts.ScanningProcessScope import ScanningProcess
            #         self.scanningProcess=ScanningProcess(Scope=self.scope,Stages=self.stages,
            #             scanstep=int(self.ui.lineEdit_ScanningStep.text()),
            #             seekcontactstep=int(self.ui.lineEdit_SearchingStep.text()),
            #             backstep=int(self.ui.lineEdit_BackStep.text()),
            #             seekcontactvalue=float(self.ui.lineEdit_LevelToDetectContact.text()),
            #             ScanningType=int(self.ui.comboBox_ScanningType.currentIndex()),
            #             CurrentFileIndex=int(self.ui.lineEdit_CurrentFile.text()),
            #             StopFileIndex=int(self.ui.lineEdit_StopFile.text()),
            #             numberofscans=int(self.ui.lineEdit_numberOfScans.text()),
            #             searchcontact=self.ui.checkBox_searchContact.isChecked())
            #         self.scanningProcess.S_saveData.connect(
            #             lambda Data,prefix: self.logger.save_data(Data,prefix,
            #                 self.stages.relative_position['X'],
            #                 self.stages.relative_position['Y'],
            #                 self.stages.relative_position['Z'], 'FromScope'))
                
              

                self.ui.tabWidget_instruments.setEnabled(False)
                self.ui.groupBox_stand.setEnabled(False)
                self.ui.pushButton_set_scanning_parameters.setEnabled(False)
                self.force_scanning_process.connect(self.scanningProcess.run)
                self.logText('Start Scanning')
                self.force_scanning_process.emit()

    
            else:
                self.scanningProcess.is_running=False
                self.ui.tabWidget_instruments.setEnabled(True)
                self.ui.groupBox_scope_control.setEnabled(True)
                self.ui.groupBox_stand.setEnabled(True)
                self.ui.pushButton_set_scanning_parameters.setEnabled(True)
        except:
            print(sys.exc_info())
            self.logWarningText('Some error when making scanning')


    def on_pushButton_save_data(self):
        try:
            if self.stages is not None:
                X=self.stages.relative_position['X']
                Y=self.stages.relative_position['Y']
                Z=self.stages.relative_position['Z']
            else:
                X,Y,Z=0,0,0
            try:
                piezo_Z=self.piezo_stage.relative_position
            except:
                piezo_Z=0

            Ydata=self.painter.Ydata
            Data=self.painter.Xdata
            for YDataColumn in Ydata:
                if YDataColumn is not None:
                    Data=np.column_stack((Data, YDataColumn))

            FilePrefix=self.ui.lineEdit_saveSpectrumName.text()
            if (self.ui.comboBox_Type_of_OSA.currentText()=='Luna' and 
                    self.ui.comboBox_Luna_mode.currentText() == 'Luna .bin files'):
                        self.OSA.save_binary( f"{self.logger.SpectralBinaryDataFolder}"
                            + f"Sp_{FilePrefix}_X={X}"
                            + f"_Y={Y}"
                            + f"_Z={Z}_"+"piezoZ={:.4f}_.bin".format(piezo_Z))
                        self.logText("Saving Luna as bin")

            else:
                self.logger.save_data(Data,FilePrefix,X,Y,Z,piezo_Z,self.painter.TypeOfData)
        except:
                print(sys.exc_info())
                self.logWarningText('Error')
                

    def on_pushButton_getRange(self):
        Range=(self.painter.ax.get_xlim())
        self.ui.lineEdit_StartWavelength.setText(f'{Range[0]}:.1f')
        self.ui.lineEdit_StopWavelength.setText(f'{Range[1]}:.1f')
        try:
            self.OSA.change_range(start_wavelength=float(Range[0]),stop_wavelength=float(Range[1]))
            self.logText('Range is taken')
        except:
            self.logWarningText('Error while taking range')

#    def ChangeRange(self,Minimum=None,Maximum=None):
#        if Minimum is not None:
#            self.OSA.set_range(start_wavelength=float(Minimum))
#        if Maximum is not None:
#            self.OSA.set_range(stop_wavelength=float(Maximum))


    def on_stateChangeOfFreezeSpectrumBox(self):
        if self.ui.checkBox_FreezeSpectrum.isChecked() and self.painter.Xdata is not None:
            self.painter.savedY=list(self.painter.Ydata)
            self.painter.savedX=list(self.painter.Xdata)
        else:
            self.painter.savedY=[None]*8

    def on_stateChangeOfApplyFFTBox(self):
        if self.ui.checkBox_ApplyFFTFilter.isChecked():
            self.painter.ApplyFFTFilter=True
            self.painter.FilterLowFreqEdge=float(self.ui.lineEdit_FilterLowFreqEdge.text())
            self.painter.FilterHighFreqEdge=float(self.ui.lineEdit_FilterHighFreqEdge.text())
            self.painter.FFTPointsToCut=int(self.ui.lineEdit_FilterPointsToCut.text())
        else:
            self.painter.ApplyFFTFilter=False

    def on_stateChangeOfIsHighResolution(self):
        if self.OSA is not None:
            if self.ui.checkBox_HighRes.isChecked():
                self.OSA.SetWavelengthResolution('High')
            else:
                self.OSA.SetWavelengthResolution('Low')


    def on_TabChanged_instruments_changed(self,i):
        if i==0:
            self.painter.TypeOfData='FromOSA'
        elif i==1:
            self.painter.TypeOfData='FromScope'


    def on_Push_Button_ProcessSpectra(self):
        self.spectral_processor.processedData_dir_path=self.path_to_main+'\\ProcessedData\\'
        self.spectral_processor.source_dir_path=self.path_to_main+'\\SpectralData\\'
        self.spectral_processor.run()
        self.analyzer.spectrogram_file_path= self.spectral_processor.processedData_dir_path+self.spectral_processor.f_name
        self.ui.label_analyzer_file.setText(self.analyzer.spectrogram_file_path)
        self.analyzer.load_data()
        self.analyzer.plot_spectrogram()


    def on_pushButton_ProcessTD(self):
        from Scripts.ProcessAndPlotTD import ProcessAndPlotTD
        self.ProcessTD=ProcessAndPlotTD()
        Thread=self.add_thread([self.ProcessTD])
        self.ProcessTD.run(Averaging=self.ui.checkBox_processing_isAveraging.isChecked(),
            DirName='TimeDomainData',
            axis_to_plot_along=self.ui.comboBox_axis_to_plot_along.currentText(),
            channel_number=self.ui.comboBox_TD_channel_to_plot.currentIndex())
        Thread.quit()


    def plotSampleShape(self,DirName,axis):
        self.spectral_processor.plot_sample_shape()

    def delete_all_figures(self):
        if plt.get_backend()!='TkAgg':  
            for i in plt.get_fignums():
                plt.close(i)
        else:
            self.logWarningText('Deleting figures does not work with TKinter backend')
        # if plt.get_backend()!='TkAgg':
        #     plt.close(plt.close('all'))
        # else:
        #     matplotlib.use("Agg")
        #     plt.close(plt.close('all'))
        #     time.sleep(0.5)
        #     matplotlib.use("TkAgg")

    def save_parameters_to_file(self):
        '''
        save all parameters and values except paths to file

        Returns
        -------
        None.

        '''
        D={}
        D['MainWindow']=get_widget_values(self)
        D['Analyzer']=self.analyzer.get_parameters()
        D['Spectral_processor']=self.spectral_processor.get_parameters()
        D['Scanning_position_process']=self.scanningProcess.get_parameters()
        D['hardware_ports']=self.hardware_ports.get_attributes()

        #remove all parameters that are absolute paths 
        for k in D:
            l=[key for key in list(D[k].keys()) if ('path' in key)]
            for key in l:
                del D[k][key]
        self.logger.save_parameters(D)
        
        
    def load_parameters_from_file(self):
        Dicts=self.logger.load_parameters()
        if Dicts is not None:
            try:
                set_widget_values(self, Dicts['MainWindow'])
                self.analyzer.set_parameters(Dicts['Analyzer'])
                self.spectral_processor.set_parameters(Dicts['Spectral_processor'])
                self.scanningProcess.set_parameters(Dicts['Scanning_position_process'])
                self.hardware_ports.set_attributes(Dicts['hardware_ports'])
            except KeyError:
                pass


    def choose_folder_for_spectral_processor(self):
        self.spectral_processor.source_dir_path = str(
            QFileDialog.getExistingDirectory(self, "Select Directory"))+'\\'
        self.spectral_processor.processedData_dir_path=os.path.dirname(
            os.path.dirname(self.spectral_processor.source_dir_path))+'\\'
        self.ui.label_folder_to_process_files.setText(self.spectral_processor.source_dir_path+'\\')
        
       

    def process_arb_spectral_data_clicked(self):
        Folder=self.spectral_processor.source_dir_path
        try:
            self.spectral_processor.StepSize=int(Folder[Folder.index('Step=')+len('Step='):len(Folder)])
        except ValueError:
            self.spectral_processor.StepSize=0
        self.spectral_processor.run()
        self.analyzer.spectrogram_file_path= self.spectral_processor.processedData_dir_path+self.spectral_processor.f_name
        self.ui.label_analyzer_file.setText(self.analyzer.spectrogram_file_path)
        self.analyzer.load_data()
        self.analyzer.plot_spectrogram()
            

    def process_arb_TD_data_clicked(self):
        from Scripts.ProcessAndPlotTD import ProcessAndPlotTD
        self.ProcessTD=ProcessAndPlotTD()
        Thread=self.add_thread([self.ProcessTD])
        self.ProcessTD.run(Averaging=self.ui.checkBox_processingArbData_isAveraging.isChecked(),
            DirName=self.Folder,
            axis_to_plot_along=self.ui.comboBox_axis_to_plot_along_arb_data.currentText(),
            channel_number=self.ui.comboBox_TD_channel_to_plot_arb_data.currentIndex())
        Thread.quit()

       
    def plot_ERV_from_file(self):
        DataFilePath= str(QFileDialog.getOpenFileName(
            self, "Select Data File",'','*.pkl')).split("\',")[0].split("('")[1]
        self.analyzer.plot_ERV_from_file(DataFilePath)
        
    

    def choose_file_for_analyzer(self):
        DataFilePath= str(QFileDialog.getOpenFileName(self, "Select Data File",'','*.pkl *.pkl3d *.SNAP *.cSNAP' )).split("\',")[0].split("('")[1]
        if DataFilePath=='':
            self.logWarningText('file is not chosen or previous choice is preserved')
        self.analyzer.spectrogram_file_path=DataFilePath
        self.ui.label_analyzer_file.setText(DataFilePath)
        self.analyzer.load_data()
       

    def choose_file_for_analyzer_plotting_parameters(self):
        FilePath= str(QFileDialog.getOpenFileName(
            self, "Select plotting parameters file",'','*.txt')).split("\',")[0].split("('")[1]
        if FilePath=='':
            FilePath=os.getcwd()+'\\plotting_parameters.txt'
        self.analyzer.plotting_parameters_file=FilePath
        self.ui.label_analyzer_plotting_file.setText(FilePath)
        
    def choose_single_spectrum_file_for_analyzer(self):
        DataFilePath= str(QFileDialog.getOpenFileName(self, "Select Data File",'','*.pkl *.laserdata' )).split("\',")[0].split("('")[1]
        if DataFilePath=='':
            self.logWarningText('file is not chosen or previous choice is preserved')
        self.analyzer.single_spectrum_path=DataFilePath
        self.ui.label_analyzer_single_spectrum_file.setText(DataFilePath)
        
                
    def choose_single_oscillogram_for_analyzer(self):
        DataFilePath= str(QFileDialog.getOpenFileName(self, "Select Data File",'','*.osc_pkl' )).split("\',")[0].split("('")[1]
        if DataFilePath=='':
            self.logWarningText('file is not chosen or previous choice is preserved')
        self.analyzer.single_oscillogram_path=DataFilePath
        self.ui.label_analyzer_single_oscillogram_file.setText(DataFilePath)

        
    def on_pushButton_set_analyzer_parameters(self):
        '''
        open dialog with analyzer parameters
        '''
        d = self.analyzer.get_parameters()
        from Windows.UIs.analyzer_dialogUI import Ui_Dialog
        analyzer_dialog = QDialog()
        ui = Ui_Dialog()
        ui.setupUi(analyzer_dialog)
        set_widget_values(analyzer_dialog,d)
        if analyzer_dialog.exec_() == QDialog.Accepted:
            params=get_widget_values(analyzer_dialog)
            self.analyzer.set_parameters(params)
   
    def on_pushButton_set_spectral_processor_parameters(self):
        '''
        open dialog with  parameters
        '''
        d=self.spectral_processor.get_parameters()
        from Windows.UIs.processing_dialogUI import Ui_Dialog
        dialog = QDialog()
        ui = Ui_Dialog()
        ui.setupUi(dialog)
        set_widget_values(dialog,d)
        if dialog.exec_() == QDialog.Accepted:
            params=get_widget_values(dialog)
            self.spectral_processor.set_parameters(params)
            
    def on_pushButton_set_scanning_parameters(self):
        '''
        open dialog with  parameters
        '''
        d=self.scanningProcess.get_parameters()
        from Windows.UIs.scanning_dialogUI import Ui_Dialog
        dialog = QDialog()
        ui = Ui_Dialog()
        ui.setupUi(dialog)
        set_widget_values(dialog,d)
        
        if dialog.exec_() == QDialog.Accepted:
            params=get_widget_values(dialog)
            self.scanningProcess.set_parameters(params)
            if self.scanningProcess.axis_to_scan=='Piezo':
                final_position='{:.4f}'.format((self.scanningProcess.stop_file_index-self.scanningProcess.current_file_index)*self.scanningProcess.scanning_step+self.piezo_stage.relative_position)
            else:
                final_position=(self.scanningProcess.stop_file_index-self.scanningProcess.current_file_index)*self.scanningProcess.scanning_step+self.stages.relative_position[self.scanningProcess.axis_to_scan]
            self.ui.label_scanning_final_position.setText(str(final_position))
            self.ui.label_scanning_axis.setText(self.scanningProcess.axis_to_scan)

            
    def delete_slice_from_spectrogram(self):
        msg=QMessageBox(2, 'Warning', 'Do you want to delete slice at {}?'.format(float(self.ui.lineEdit_slice_position.text())))
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msg.exec()
        if returnValue == QMessageBox.Ok:  
            self.analyzer.delete_slice(float(self.ui.lineEdit_slice_position.text()))
            msg=QMessageBox(2, 'Warning', 'Spectogram without slice is resaved')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        

    def delete_data_from_folders(self):
        msg=QMessageBox(2, 'Warning', 'Do you want to delete all raw data?')

        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msg.exec()
        if returnValue == QMessageBox.Ok:  
            dirs=['\\SpectralData\\','\\SpectralBinData\\']
            for directory in dirs:
                l=os.listdir(self.path_to_main+directory)
                if '.gitignore' in l:l.remove('.gitignore')
                for file in l:
                    os.remove(self.path_to_main+directory+file)
            self.logText('Raw data deleted')

        

    def closeEvent(self, event):
#         here you can terminate your threads and do other stuff
#        try:
        del self.stages
        print('Stages object is deleted')
        del self.OSA
        print('OSA object is deleted')
        del self.painter
        print('Painter object is deleted')
        del self.logger
        print('Logger is deleted')
        del self.analyzer
        print('Analyzer is deleted')
        try:
            del self.powermeter
            print('powermeter is deleted')
        except:
            pass    
        try:
            self.laser.setOff()
            del self.laser
            print('laser is deleted')
        except:
            pass
        try:
            del self.scanningProcess
            print('Scanning object is deleted')
        except:
            pass
        del self.spectral_processor
        try:
            del self.piezo_stage
            print('Piezo stage is deleted')
        except:
            pass
        print('Processing is deleted')
        super(QMainWindow, self).closeEvent(event)
        

def get_widget_values(window)->dict:
    '''
    collect all data from all widgets in a window
    '''
    D={}
    for w in window.findChildren(QLineEdit):
        s=w.text()
        key=w.objectName().split('lineEdit_')[1]
        try:
            f=int(s)
            
        except ValueError:
            
            try:
                f=float(s)
                
            except ValueError:
                f=s
        D[key]=f
    for w in window.findChildren(QCheckBox):
        f=w.isChecked()
        key=w.objectName().split('checkBox_')[1]
        D[key]=f
        
    for w in window.findChildren(QComboBox):
        s=w.currentText()
        key=w.objectName().split('comboBox_')[1]
        D[key]=s
    return D

def set_widget_values(window,d:dict)->None:
     for w in window.findChildren(QLineEdit):
         key=w.objectName().split('lineEdit_')[1]
         try:
             s=d[key]
             w.setText(str(s))
         except KeyError as e:
             print('Set widget values error: '+ str(e))
             pass
     for w in window.findChildren(QCheckBox):
         key=w.objectName().split('checkBox_')[1]
         try:
             s=d[key]
             w.setChecked(s)
             w.clicked.emit(s)
         except KeyError as e:
             print('Set widget values error: '+ str(e))
     for w in window.findChildren(QComboBox):
         key=w.objectName().split('comboBox_')[1]
         try:
             s=d[key]
             w.setCurrentText(s)
         except KeyError:
             pass
         
if __name__=='__main__':
    m=MainWindow()
    m.connect_scope()
    # m.on_pushButton_set_spectral_processor_parameters()
    # m.connect_laser()
    # from Hardware.PurePhotonicsLaser_pyvisa import Laser
    # l=Laser('COM12')
