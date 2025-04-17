'''
Mode distributions are derived following Demchenko, Y. A. and Gorodetsky, M. L., “Analytical estimates of eigenfrequencies, dispersion, and field distribution in whispering gallery resonators,” J. Opt. Soc. Am. B 30(11), 3056 (2013).
eq(23)

'''


__version__='2'
__date__='2025.03.28'



import numpy as np
from scipy import special 
import matplotlib.pyplot as plt

n=1.445

def E(x,R,m,p=1,pol='TE'): #phase not considered
    T_mp=special.jn_zeros(m,p)[p-1]
    if pol=='TE':
        P=1
    elif pol=='TM':
        P=1/n**2
    k_0=m/R/n
    gamma=np.sqrt(n**2-1)*k_0
    R_eff=R+P/gamma
    
   
    if x<R:
        return special.jn(m,x/R_eff*T_mp)
    else:
        return 1/P *special.jn(m,R/R_eff*T_mp)*np.exp(-gamma*(x-R))




def get_cross_section(R,m,p=1,pol='TE'):
    '''
    

    Parameters
    ----------
    R : cavity radius in microns

    Returns
    -------
    integral e(r,\phi)**2 d2r with max(e(r,\phi)**2)=1 in m*2

    '''
    '''

    '''
       
    step=R*0.001 # Number of points
    r_min=R*0.7
    r_max=R*1.1
    
    F = np.vectorize(E)
    Rarray=np.arange(r_min,r_max,step)
    Intenisty_array=abs(F(Rarray,pol=pol, R=R,m=m,p=p))**2
    Integral=sum(Intenisty_array*Rarray*2*np.pi)*step
    return Integral/max(Intenisty_array)*1e-12 # in m**2 , here we consider distributions normilized as max(I(r))=1

def get_cross_section_2(R,m,p=1,pol='TE'):
    '''
    integral e(r,\phi)**4 d2r with max(e(r,\phi)**2)=1
    '''
   
    step=R*0.001 # Number of points
    r_min=R*0.7
    r_max=R*1.1
    F = np.vectorize(E)
    Rarray=np.arange(r_min,r_max,step)
    Intenisty_array=abs(F(Rarray,pol=pol, R=R,m=m,p=p))**2
    # Intenisty_TE_Array=abs(F(Rarray,pol='TE',R=R_0))**2
    Integral=sum(Intenisty_array**2*Rarray*2*np.pi)*step
    return Integral/max(Intenisty_array**2)*1e-12 # in m**2 , here we consider distributions normilized as max(I(r))=1


def get_S_jj(R,m,p=1,pol='TE'):
    return (get_cross_section(R,m,p,pol))**2/get_cross_section_2(R,m,p,pol) # in m**2


def get_V_jj(R,length,m,p=1,pol='TE',axial_distribution='Gauss'):
    '''
    length, mkm, is in Intensity(z)=exp(-2*(z/length)**2)
    '''
    if axial_distribution=='Gauss':
        return get_S_jj(R,m,p,pol)*length*np.sqrt(np.pi)*1e-6 # in m**3
    
def get_Veff(R,length,m,p=1,pol='TE',axial_distribution='Gauss'):
    '''
    length, mkm, is in Intensity(z)=exp(-2*(z/length)**2)
    '''
    if axial_distribution=='Gauss':
        return get_cross_section(R,m,p,pol)*length*1e-6*np.sqrt(np.pi) # in m**3
    
if __name__=='__main__':
    R=62.5
    m=350
    p=1
    pol='TE'
    # plt.plot
    
    step=R*0.001 # Number of points
    r_min=R*0.7
    r_max=R*1.1
    # F = np.vectorize(np.power(E,2))
    F = np.vectorize(E)
    Rarray=np.arange(r_min,r_max,step)
    
    plt.figure()
    plt.plot(Rarray,F(Rarray,R=R,m=m,pol=pol,p=p)**2)
    plt.axvline(R,linestyle='--',color='red')
    plt.xlabel('Radius, mkm')
    plt.ylabel('Intensity, arb.u.')
    