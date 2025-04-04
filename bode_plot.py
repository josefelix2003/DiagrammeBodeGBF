import pyvisa
import math
import time
import matplotlib.pyplot as plt
import re
import numpy as np

#-----------------------------Functions----------------------------------

#Changing frequencies and measuring voltage
def gain_meas(freq):
    gbf.write('SOUR1:FREQ {}'.format(freq)) #set frequency
    
    time.sleep(1) #Time for oscilloscope calibration
    
    #Measure the in and out voltage
    oscillo.write(':MEASure:SOURce1 CH1')
    
    volt_in, volt_out = measure_volt()
    print(volt_in,volt_out)
    
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
def find_port(instr_name):
    rm = pyvisa.ResourceManager()  # Assure-toi d'avoir bien importé pyvisa
    available_ports = rm.list_resources()  # Stocker la liste dans une variable locale
    
    for port in available_ports:
        try:
            instr = rm.open_resource(port)  # Essayer d'ouvrir le port
            idn = instr.query('*IDN?').strip()  # Lire l'identifiant et supprimer espaces/sauts de ligne
            print(f"Port {port} → Réponse IDN : {idn}")
            
            if re.search(instr_name, idn):
                print("ok")
                return port  # Retourner le bon port
            
        except (pyvisa.errors.VisaIOError, ValueError) as e:  
            print(f"Impossible d'interroger {port}: {e}")  # Éviter l'arrêt du programme
    
    raise ValueError(f"{instr_name} not found!")
    
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

#Measuring the in/out voltage
def measure_volt():
    try_count=0
    while try_count < 20:
        try:
            oscillo.write(':MEASure:SOURce1 CH1')
            volt_in=float(oscillo.query(':MEASure:AMPlitude?').strip())
            print("amp1 = ", volt_in)
            break
        
        except:
            time.sleep(1)
            try_count+=1
            
    try_count=0
    while try_count < 20:
         try:
             oscillo.write(':MEASure:SOURce1 CH2')
             volt_out=float(oscillo.query(':MEASure:AMPlitude?').strip())
             print("amp2 = ", volt_out)
             break
         except:
             time.sleep(1)
             try_count+=1
    return volt_in, volt_out

#Measuring the phase
def measure_phase():
    try_count=0
    while try_count < 20:
        try:
            oscillo.write(':MEASure:SOURce1 CH1')
            oscillo.write(':MEASure:SOURce2 CH2')
            phase=float(oscillo.query(':MEASure:Phase?').strip())
            print("phase = ", phase)
            break
        
        except:
            time.sleep(2)
            try_count+=1
    return phase 

#Main function; Executes the sweep and measures the gain and phase for each frequency
def gain_list(freq_inf, freq_sup, amplitude):
    gbf.write(':SOUR1:VOLT {}'.format(amplitude))
    time.sleep(1)
    
    oscillo.write('CHAN1:SCAL {}'.format(amplitude/3))
    oscillo.write('CHAN2:SCAL {}'.format(amplitude/3))


    while True:
        try:
            oscillo.read_raw()
        except pyvisa.errors.VisaIOError:
            print('buffer empty')
            break
        
    oscillo.write(':ACQUIRE:AVERAGE 8')
    freq_list = log_list(freq_inf, freq_sup) #Create the frequency log list for the inf and sup frequencies
    
    gbf.write('SOUR1:FREQ {}'.format(freq_inf)) #set frequency
    #oscillo.write('autoset')
    oscillo.write(':CHANnel1:POSition 0')
    oscillo.write(':CHANnel2:POSition 0')
   
    time.sleep(1) 
    
    gain_list = []
    phase_list=[]    
    
    
    previous_power = None
  
    for frequency in freq_list:
        current_power = power_freq(frequency)
        
        if current_power != previous_power:
            oscillo.write(f':TIMebase:SCALe 5E-{current_power+1}')
            previous_power = current_power
    
        oscillo.write(':TRIGger:SOURce CH1') 
        oscillo.write(':CHANnel1:POSition 0')
        oscillo.write(':CHANnel2:POSition 0')
        oscillo.write(':MEASure:SOURce1 CH1')
        amp1, amp2 = measure_volt()
        oscillo.write('CHAN1:SCAL {}'.format(amp1/3))
        oscillo.write('CHAN2:SCAL {}'.format(amp2/3))
            
        if current_power < 2:
            time.sleep(5)
        else:
            time.sleep(1)  
      
        phase_list.append(measure_phase())
        gain_list.append(gain_meas(frequency)) 
        print(frequency, gain_meas(frequency))
        
    return freq_list, gain_list, phase_list

#Saving the data into a new file; the file will be created in txt format in the folder containing this script
def save_file(freq_list, gain_list, phase_list):
    
  try:
    if question_YorN("Do you wish to save the data [Y/N]?") == "Y": #Si on veut sauvegarder les données
      nom_fichier = input("File name : (extension .txt) :\n")
      if not (nom_fichier.endswith(".txt")): #Si le nom ne finit pas par .txt
        nom_fichier+=".txt"
        print("The .txt extension was added automatically\n")
              
      with open(nom_fichier, 'a') as fichier:
        fichier.write("#First column represents the frequency, second column represents the gain/phase\n#Gain data\n>>>>>>>>>>>>>Begin<<<<<<<<<<<<<<\n")
      
        for frequency, gain in zip(freq_list, gain_list):
            fichier.write("{} {}\n".format(frequency, gain))
          
        fichier.write(">>>>>>>>>>>>>End<<<<<<<<<<<<<<\n\n#Phase data\n>>>>>>>>>>>>>Begin<<<<<<<<<<<<<<\n")
    
        for frequency, phase in zip(freq_list, phase_list):
            fichier.write("{} {}\n".format(frequency, phase))
            
        fichier.write(">>>>>>>>>>>>>End<<<<<<<<<<<<<<\n")

      print("The data was saved in {}".format(nom_fichier))
      
  except:
    print("Error while writing the file")

#Asking the user a yes or no question 
def question_YorN(question):
        reponse_valide = False
        while reponse_valide == False:
            print(question)
            reponse_clavier = input()
            if reponse_clavier == "Y" or reponse_clavier == "N":
                reponse_valide = True
                if reponse_clavier == "Y":
                    return "Y"
                else :
                    return "N"
            else:
                print("Answer with Y for yes or N for no")




#------------------------------Main---------------------------------

rm = pyvisa.ResourceManager()
rm.list_resources()

#DEFINE THE INSTRUMENT NAME
#///////////////////////////////////////////////////////////////////
oscillo_IDN = "GW,GDS"
gbf_IDN = "Rigol"
#///////////////////////////////////////////////////////////////////

#Finding the location of the specified instruments
oscillo=rm.open_resource(find_port(oscillo_IDN))
gbf=rm.open_resource(find_port(gbf_IDN))

#Asking the user for the frequency range and output voltage 
freq_min=float(input("Minimal frequency : "))
freq_max=float(input("Maximal frequency : "))
amplitude =float(input("Output voltage : "))

#Retrieving the the gain and phase lists for the specified range
freq_list, gain_list, phase_list = gain_list(freq_min,freq_max,amplitude)

#Saving the data 
save_file(freq_list, gain_list, phase_list)

#Plotting the Bode plot
plt.figure()
plt.title('Bode Plot')

plt.subplot(2,1,1)
plt.plot(freq_list, 20*np.log10(gain_list), marker='o', linestyle='-', color='b')
plt.xscale('log')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Gain (Vout/Vin)')
plt.grid(True, which='both', linestyle='--')

plt.subplot(2,1,2)
plt.plot(freq_list, phase_list, marker='o', linestyle='-', color='g')
plt.xscale('log')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Phase (Degrees)')
plt.grid(True, which='both', linestyle='--')

plt.show()

rm.close()

#----------------------------------------------------------------




    
            
        
    
    
    
    
