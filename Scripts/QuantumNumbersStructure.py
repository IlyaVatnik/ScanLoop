########
# Calculating spectra of WGM for different azimuthal and radial numbers 
#
#Using Demchenko, Y. A. and Gorodetsky, M. L., “Analytical estimates of eigenfrequencies, dispersion, and field distribution in whispering gallery resonators,” J. Opt. Soc. Am. B 30(11), 3056 (2013).
#
#See formula A3 for lambda_m_p
########

__version__='3.4'
__date__='2022.07.07'

 
import numpy as np
from scipy import special
from scipy import optimize
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import scipy.optimize as sciopt
from scipy.fftpack import rfft, irfft, fftfreq

c=299792458 # m/s

Sellmeier_coeffs={
    'SiO2':[0.6961663,0.4079426,0.8974794,0.0684043,0.1162414,9.896161],
    'MgF2':[0.48755108,0.39875031,2.3120353, 0.04338408, 0.09461442, 23.793604]}

def ref_ind(w,medium): # refractive index for quarzt versus wavelength, w in nm
    w=w*1e-3
    t=1
    medium
    for i in range(0,3):
       t+=Sellmeier_coeffs[medium][i]*w**2/(w**2-Sellmeier_coeffs[medium][i+3]**2) 
    return np.sqrt(t)




def airy_zero(p):
    t=[-2.338107410459767038489,-4.087949444130970616637,-5.52055982809555105913,-6.78670809007175899878,
       -7.944133587120853123138,-9.022650853340980380158,-10.0401743415580859306,-11.00852430373326289324]
    return t[p-1]

def T(m,p):
    a=airy_zero(p)
    T = m-a*(m/2)**(1/3)+3/20*a**2*(m/2)**(-1/3) \
        + (a**3+10)/1400*(m/2)**(-1)-a*(479*a**3-40)/504000*(m/2)**(-5/3)-a**2*(20231*a**3+55100)/129360000*(m/2)**(-7/3)
    return T

def lambda_m_p_simplified(m,p,polarization,n,R,dispersion=False,medium='SiO2'): #Using T. Hamidfar et al., “Suppl. Localization of light in an optical microcapillary induced by a droplet,” Optica, vol. 5, no. 4, p. 382, 2018.
    if not dispersion:    
        if polarization=='TE':
            temp=( 1 + airy_zero(p)*(2*m**2)**(-1/3)+ n/(m*(n**2-1)**0.5))
        elif polarization=='TM':
            temp=( 1 + airy_zero(p)*(2*m**2)**(-1/3) + 1/n/(m*(n**2-1)**(0.5)) )
        return 2*np.pi*n*R/m*temp
    else:
        if polarization=='TE':
            res=optimize.root(lambda x: x-2*np.pi*ref_ind(x,medium)*R/m*( 1 + airy_zero(p)*(2*m**2)**(-1/3)+ ref_ind(x,medium)/(m*(ref_ind(x,medium)**2-1)**0.5)),1550)
            return res.x[0]
        elif polarization=='TM':
            res=optimize.root(lambda x: x-2*np.pi*ref_ind(x,medium)*R/m*( 1 + airy_zero(p)*(2*m**2)**(-1/3) + 1/ref_ind(x,medium)/(m*(ref_ind(x,medium)**2-1)**(0.5))),1550)
            return res.x[0]
            
        


def lambda_m_p_cylinder(m,p,polarization,n,R,dispersion=False,medium='SiO2',simplified=False): # following formula A3 from Demchenko and Gorodetsky
    if not simplified:
        if not dispersion:
            if polarization=='TE':
                P=1
            elif polarization=='TM':
                P=1/n**2
            temp=T(m,p)-n*P/np.sqrt(n**2-1)+airy_zero(p)*(3-2*P**2)*P*n**3*(m/2)**(-2/3)/6/(n**2-1)**(3/2) \
                 - n**2*P*(P-1)*(P**2*n**2+P*n**2-1)*(m/2)**(-1)/4/(n**2-1)**2
            return 2*np.pi*n*R/temp
        elif dispersion:
            if polarization=='TE':
                res=optimize.root(lambda x: x-2*np.pi*ref_ind(x,medium)*R/(T(m,p)-ref_ind(x,medium)/np.sqrt(ref_ind(x,medium)**2-1)+
                                                                    airy_zero(p)*(3-2)*ref_ind(x,medium)**3*(m/2)**(-2/3)/6/(ref_ind(x,medium)**2-1)**(3/2)-
                                                                    -0),2000)
                # print(res.success)
                return res.x[0]
            elif polarization=='TM':
                res=optimize.root(lambda x: x-2*np.pi*ref_ind(x,medium)*R/(T(m,p)-1/ref_ind(x,medium)/np.sqrt(ref_ind(x,medium)**2-1)+
                                                                    airy_zero(p)*(3-2*ref_ind(x,medium)**(-4))*ref_ind(x,medium)*(m/2)**(-2/3)/6/(ref_ind(x,medium)**2-1)**(3/2) \
                 - 1*(1/ref_ind(x,medium)**2-1)*(1/ref_ind(x,medium)**2)*(m/2)**(-1)/4/(ref_ind(x,medium)**2-1)**2),1550)
                # print(res.success)
                return res.x[0]
    else:
        return lambda_m_p_simplified(medium,m,p,polarization,n,R)
                
def lambda_m_p_spheroid(m,p,polarization,n,a,b,dispersion=False,medium='SiO2',simplified=False): # following formula (15),(17) from Demchenko and Gorodetsky
     if not dispersion:
         if polarization=='TE':
             P=1
         elif polarization=='TM':
             P=1/n**2
         temp=m-airy_zero(p)*(m/2)**(1/3)+(2*p+1)*a/2/b+3*airy_zero(p)**2/20*(m/2)**(-1/3)*airy_zero(p)/12*(2*p+1)*a**3/b**3*(m/2)**(-2/3)
         +(airy_zero(p)**3/1400)*(m/2)**(-1)
        
         return 2*np.pi*n*R/temp
     elif dispersion:
         if polarization=='TE':
             res=optimize.root(lambda x: x-2*np.pi*ref_ind(x,medium)*R/(T(m,p)-ref_ind(x,medium)/np.sqrt(ref_ind(x,medium)**2-1)+
                                                                 airy_zero(p)*(3-2)*ref_ind(x,medium)**3*(m/2)**(-2/3)/6/(ref_ind(x,medium)**2-1)**(3/2)-
                                                                 -0),2000)
             # print(res.success)
             return res.x[0]
         elif polarization=='TM':
             res=optimize.root(lambda x: x-2*np.pi*ref_ind(x,medium)*R/(T(m,p)-1/ref_ind(x,medium)/np.sqrt(ref_ind(x,medium)**2-1)+
                                                                 airy_zero(p)*(3-2*ref_ind(x,medium)**(-4))*ref_ind(x,medium)*(m/2)**(-2/3)/6/(ref_ind(x,medium)**2-1)**(3/2) \
              - 1*(1/ref_ind(x,medium)**2-1)*(1/ref_ind(x,medium)**2)*(m/2)**(-1)/4/(ref_ind(x,medium)**2-1)**2),1550)
             # print(res.success)
             return res.x[0]


class Resonances():
    #########################
    ### Structure is as follows:
    ### {Polarization_dict-> list(p_number)-> np.array(m number)}
    
    colormap = plt.cm.gist_ncar #nipy_spectral, Set1,Paired   
    pmax=3
    dispersion=False
    
    def __init__(self,wave_min,wave_max,n,R,p_max=3,
                 material_dispersion=True,shape='cylinder',medium='SiO2', simplified=False):
        m0=np.floor(2*np.pi*n*R/wave_max)
        self.medium=medium
        self.pmax=p_max
        self.structure={'TE':[],'TM':[]}
        self.material_dispersion=material_dispersion
        self.simplified=simplified
        self.N_of_resonances={'TE':0,'TM':0,'Total':0}
        if shape=='cylinder':
            lambda_m_p=lambda_m_p_cylinder
        elif shape=='sphere':
            lambda_m_p=lambda_m_p_spheroid(b=R)
            
        for Pol in ['TE','TM']:
            
            p=1
            if Pol=='TE':
                m=int(np.floor(m0*( 1 + airy_zero(p)*(2*m0**2)**(-1/3)+ n/(m0*(n**2-1)**0.5))))-4
            else:
                m=int(np.floor(m0*( 1 + airy_zero(p)*(2*m0**2)**(-1/3)+ 1/n/(m0*(n**2-1)**0.5))))-4
            wave=lambda_m_p(m,p,Pol,n,R,self.material_dispersion,self.medium,simplified=self.simplified)
            
            while wave>wave_min and p<self.pmax+1: 
                resonance_temp_list=[]
                resonance_m_list=[]
                while wave>wave_min: 
                    if wave<wave_max:
                        resonance_temp_list.append(wave)
                        resonance_m_list.append(m)
                        self.N_of_resonances[Pol]+=1
                        self.N_of_resonances['Total']+=1
                    m+=1
                    wave=lambda_m_p(m,p,Pol,n,R,self.material_dispersion,self.medium,simplified=self.simplified)
                
                Temp=np.column_stack((np.array(resonance_temp_list),np.array(resonance_m_list)))
                self.structure[Pol].append(Temp)
                p+=1
                if Pol=='TE':
                    m=np.floor(m0*( 1 + airy_zero(p)*(2*m0**2)**(-1/3)+ n/(m0*(n**2-1)**0.5)))-3
                else:
                    m=np.floor(m0*( 1 + airy_zero(p)*(2*m0**2)**(-1/3)+ 1/n/(m0*(n**2-1)**0.5)))-3
                wave=lambda_m_p(m,p,Pol,n,R,self.material_dispersion,self.medium,simplified=self.simplified)
        
                
    def create_unstructured_list(self,Polarizations_to_account):  
        if Polarizations_to_account=='both' or Polarizations_to_account=='single':
            Polarizations=['TE','TM']
        elif Polarizations_to_account=='TE':
            Polarizations=['TE']
        elif Polarizations_to_account=='TM':
            Polarizations=['TM']
        list_of_resonances=[]
        list_of_labels=[]
        for Pol in Polarizations:
            for p,L in enumerate(self.structure[Pol]):
                for wave,m in L:
                    list_of_resonances.append(wave)
                    list_of_labels.append(Pol+','+str(int(m))+','+str(p+1))
                    
        labels=[x for _,x in sorted(zip(list_of_resonances,list_of_labels))]#, key=lambda pair: pair[0])]
        resonances=sorted(list_of_resonances)
        return np.array(resonances),labels
    
                       
    # def find_max_distance(self):
    #     res,_=self.create_unstructured_list(Polarizations)
    #     return np.max(np.diff(res))
    
    def plot_all(self,y_min,y_max,Polarizations_to_account):
#        plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, num_plots)])
        resonances,labels=self.create_unstructured_list(Polarizations_to_account)
        for i,wave in enumerate(resonances):
            if labels[i].split(',')[0]=='TM':
                color='blue'
            else:
                color='red'
            plt.axvline(wave,0,1,color=color)
            y=y_min+(y_max-y_min)/self.pmax*float(labels[i].split(',')[2])
            plt.annotate(labels[i],(wave,y))
            
    def get_int_dispersion(self, polarization='TE',p=1):
        '''
        using D_int=omega_i-omega_0-D_1*i
        D_1=averaged FSR
        '''
        if p>self.pmax:
            print('error:radial quantum number p > p_max ')
        else:
            wavelengths=self.structure[polarization][p-1][:,0]
            N=np.shape(wavelengths)[0]
            freqs=c/wavelengths*1e9
            N_central=N//2
            FSR=np.abs(freqs[N_central+1]-freqs[N_central-1])/2
            D_int=freqs-freqs[N_central]-FSR*(np.arange(0, N)-N_central)
            return freqs,D_int
        
    def plot_int_dispersion(self, polarization='TE',p=1):
        freqs,D_int=self.get_int_dispersion(polarization,p)
        plt.figure()
        plt.plot(freqs*1e-12, D_int*1e-6)
        plt.xlabel('Frequency, THz')
        plt.ylabel('Dispersion $D_{int}$, MHz')
        plt.tight_layout()
            
            
        
        
            
     
     
def closest_argmin(A, B): # from https://stackoverflow.com/questions/45349561/find-nearest-indices-for-one-array-against-all-values-in-another-array-python
    L = B.size
    sidx_B = B.argsort()
    sorted_B = B[sidx_B]
    sorted_idx = np.searchsorted(sorted_B, A)
    sorted_idx[sorted_idx==L] = L-1
    mask = (sorted_idx > 0) & \
    ((np.abs(A - sorted_B[sorted_idx-1]) < np.abs(A - sorted_B[sorted_idx])) )
    return sidx_B[sorted_idx-mask]       


def FFTFilter(y_array):
    FilterLowFreqEdge=0.00
    FilterHighFreqEdge=0.01
    W=fftfreq(y_array.size)
    f_array = rfft(y_array)
    Indexes=[i for  i,w  in enumerate(W) if all([abs(w)>FilterLowFreqEdge,abs(w)<FilterHighFreqEdge])]
    f_array[Indexes] = 0
#        f_array[] = 0
    return irfft(f_array)
     
class Fitter():
    
    def __init__(self,
                 wavelengths,signal,peak_depth,peak_distance,wave_min=None,wave_max=None,
                 p_guess_array=None,dispersion=True,simplified=False,polarization='both',
                 FFT_filter=False, type_of_optimizer='bruteforce' ):
        
        p_guess_max=5
        
        if wave_min is not None:
            self.wave_min=wave_min
        else:
            self.wave_min=min(wavelengths)
        if wave_max is not None:
            self.wave_max=wave_max
        else:
            self.wave_max=max(wavelengths)
        
        
        index_min=np.argmin(abs(wavelengths-self.wave_min))
        index_max=np.argmin(abs(wavelengths-self.wave_max))
        self.wavelengths=wavelengths[index_min:index_max]
        self.signal=signal[index_min:index_max]
        if FFT_filter:
            self.signal=FFTFilter(self.signal)
        self.resonances_indexes,_=find_peaks(abs(self.signal-np.nanmean(self.signal)),height=peak_depth,distance=peak_distance)
        self.exp_resonances=self.wavelengths[self.resonances_indexes]
        self.polarizations=polarization
        self.material_dispersion=dispersion
        self.type_of_optimizer=type_of_optimizer
        
        self.cost_best=1e3
        self.n_best,self.R_best,self.p_best,self.th_resonances=None,None,None,None
       
        if p_guess_array is not None:
            self.p_guess_array=p_guess_array
        else:
            self.p_guess_array=np.arange(1,p_guess_max)
        
    def run(self):
        for p in self.p_guess_array:
            if self.type_of_optimizer=='Nelder-Mead':
                res=sciopt.minimize(self.cost_function,((1.4445,62.5e3)),bounds=((1.443,1.4447),(62e3,63e3)),
                            args=p,method='Nelder-Mead',options={'maxiter':1000},tol=1e-11)
            elif self.type_of_optimizer=='bruteforce':
                res=bruteforce_optimizer(self.cost_function,args=(p,1.4445),R_bounds=(61.8e3,63.2e3),R_step=2)
                
            # res=sciopt.least_squares(func_to_minimize,((1.43,62.5e3)),bounds=((1.4,1.5),(62e3,63e3)),
            #                 args=(Wavelength_min,Wavelength_max,Resonances_exp,p),xtol=1e-10,ftol=1e-10)
            # res=sciopt.least_squares(func_to_minimize,(62.5e3),bounds=(62e3,63e3),
                            # args=(Wavelength_min,Wavelength_max,Resonances_exp,p),xtol=1e-8,ftol=1e-8)
            
            print('p={}'.format(p),res)
            if res['fun']<self.cost_best:
                self.cost_best=res['fun']
                self.n_best=res['x'][0]
                self.R_best=res['x'][1]
                self.p_best=p
        self.th_resonances=Resonances(self.wave_min,self.wave_max,self.n_best,self.R_best,self.p_best,self.material_dispersion)
                
        

                
    def cost_function(self,param,p_max): # try one and another polarization
        def measure(exp,theory):
            closest_indexes=closest_argmin(exp,theory)
            return sum((exp-theory[closest_indexes])**2)
        
        n,R=param
        # (p_max)=p
        resonances=Resonances(self.wave_min,self.wave_max,n,R,p_max,self.material_dispersion)
        
        if self.polarizations=='both':
            if resonances.N_of_resonances['Total']>0:
                th_resonances,labels=resonances.create_unstructured_list('both')
                return measure(self.exp_resonances,th_resonances)
            else:
                return 1e3
            
        elif self.polarizations=='single':
            if resonances.N_of_resonances['TE']>0:
                th_resonances,labels=resonances.create_unstructured_list('TE')
                cost_TE=measure(self.exp_resonances,th_resonances)
            else:
                cost_TE=1e3
            if resonances.N_of_resonances['TM']>0:
                th_resonances,labels=resonances.create_unstructured_list('TM')
                cost_TM=measure(self.exp_resonances,th_resonances)
            else:
                cost_TM=1e3
            return min([cost_TE,cost_TM])    
        
    
        
    def plot_results(self):
        # fig, axs = plt.subplots(2, 1, sharex=True)
        fig, axs = plt.subplots(1, 1)
        axs.plot(self.wavelengths,self.signal)
        axs.plot(self.exp_resonances,self.signal[self.resonances_indexes],'.')
        # axs.set_title('N=%d' % len(self.exp_resonances))

        
        # plt.sca(axs[1])
        self.th_resonances.plot_all(min(self.signal),max(self.signal),'both')
        axs.set_title('N_exp=%d , N_th=%d,n=%f,R=%f,p_max=%d, cost_function=%f' % (len(self.exp_resonances),self.th_resonances.N_of_resonances['Total'],self.n_best,self.R_best,self.p_best, self.cost_best))
        plt.xlabel('Wavelength,nm')
    
    
def bruteforce_optimizer(f,args,R_bounds,R_step):
    p,n=args
    cost_best=1e5
    R_best=None
    for current_R in np.arange(R_bounds[0],R_bounds[1],R_step):
        cost=f((n,current_R),p)
        if cost<cost_best:
            cost_best=cost
            R_best=current_R
        print('R={}, Cost={}'.format(current_R,cost))
    return {'x':(n,R_best),'fun':cost_best}
        
            
if __name__=='__main__': 
    
    # print(lambda_m_p(m=354,p=1,polarization='TM',n=1.445,R=62.5e3,dispersion=True))
    # wave_min=900
    # wave_max=2500
    # n=1.446
    # R=62.5e3
    # p_max=2
    # medium='SiO2'
    # shape='cylinder'
    # material_dispersion=True
    # resonances=Resonances(wave_min,wave_max,n,R,p_max,material_dispersion,shape,medium)
    # resonances.plot_int_dispersion(polarization='TM',p=1)


    #%%
    
    filename="F:\!Projects\!SNAP system\Modifications\Wire heating\dump_data_at_-2600.0.pkl"
    import pickle
    with open(filename,'rb') as f:
        Temp=pickle.load(f)
    fitter=Fitter(Temp[:,0],Temp[:,1],0.8,100,p_guess_array=[3],polarization='single',dispersion=False)
    fitter.run()
    fitter.plot_results()


