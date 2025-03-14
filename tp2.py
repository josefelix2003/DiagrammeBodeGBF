import pyvisa
import math
import time

#-----------------------------Functions----------------------------------

#Changing frequencies and measuring voltage
def gain_meas(freq):
    gbf.write('SOUR1:FREQ {}'.format(freq)) #set frequency
    
    time.sleep(1) #Time for oscilloscope calibration
    
    #Measure the in and out voltage
    oscillo.write(':MEASure:SOURce1 CH1')
    volt_in=float(oscillo.query(':MEASure:AMPlitude?'))
    
    oscillo.write(':MEASure:SOURce1 CH2')
    volt_out=float(oscillo.query(':MEASure:AMPlitude?'))
    
    #Calculate the gain for the specified frequency
    gain = volt_out/volt_in
    
    return gain

#Calculating the power of a frequency 
def power_freq(freq):
    if freq < 0:
        raise ValueError("Frequency must be positive!")
    elif freq>0 and freq<1:
        raise ValueError("Frequency can't be between 0Hz and 1Hz!")
        
    if freq == 0: #Special case: frequency = 0Hz
        return 0
    return math.floor(math.log10(freq)) 

#Finding the GBF/Oscilloscope port
#Oscilloscope IDN: [COMPLETER]
#GBF IDN: [COMPLETER]
def find_port(instr_name):
    for port in rm.list_resources(): #Pour optimiser : Au lieu de demander la liste au rm, le stocker prelablement dans une variable locale,puis l'apeller
        instr=rm.open_resource("{}".format(port))
        idn=instr.query('*IDN?')
        
        if idn == instr_name:
            return port
    raise ValueError("{} not found!".format(instr_name))
    
#Creating the frequency sweep list
def log_list(freq_inf, freq_sup):
    power_inf, power_sup = power_freq(freq_inf), power_freq(freq_sup) #Calculate the powers of the inf and sup frequencies
    loglist=[]
    
    for power in range(power_inf, power_sup+1):
        for i in range (1,10):
            new_freq_value=i*10**power
            if new_freq_value>=freq_inf: #If we reached the inferior frequency
                if new_freq_value<=freq_sup: #If we haven't reached the superior frequency
                    loglist.append(new_freq_value)
                else:
                    break #If we reached the superior frequency, then exit 
            
    return loglist

#Creating the gain list
def gain_list(freq_inf, freq_sup):
    
    freq_list = log_list(freq_inf, freq_sup) #Create the frequency log list for the inf and sup frequencies
    gain_list = []
    
    for frequency in freq_list:
        gain_list.append(gain_meas(frequency)) #For each frequency, measure and stock the gain
    




#------------------------------Sweep---------------------------------

rm = pyvisa.ResourceManager()
rm.list_resources()

oscillo=rm.open_resource('ASRL3::INSTR')
gbf=rm.open_resource('USB0::0x1AB1::0x0642::DG1ZA184750870::INSTR')


amp=2

print(oscillo.query('*IDN?'))
#oscillo.write('CHAN1:SCAL {}'.format(amp))

f=1000
amp=1
#gbf.write('SOUR1:FREQ {}'.format(f))
gbf.write('SOUR1:FREQ {}'.format(f))
gbf.write(':SOUR1:VOLT {}'.format(amp))
#oscillo.write('autoset')
#oscillo.write(':MEASure:SOURce1 CH1')

#print(oscillo.query(':MEASure:AMPlitude?'))
        
oscillo.close()    
gbf.close()
rm.close()


    
            
        
    
    
    
    
