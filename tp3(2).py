import pyvisa
import math
import time
import matplotlib.pyplot as plt
import re

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


    

#Creating the gain list
def gain_list(freq_inf, freq_sup, amplitude):
    
    oscillo.write('CHAN1:SCAL {}'.format(amplitude/3))
    oscillo.write('CHAN2:SCAL {}'.format(amplitude/3))
        
    
    gbf.write(':SOUR1:VOLT {}'.format(amplitude))

    while True:
        try:
            oscillo.read_raw()
        except pyvisa.errors.VisaIOError:
            print('buffer empty')
            break
        
    oscillo.write(':ACQUIRE:AVERAGE 8')
    freq_list = log_list(freq_inf, freq_sup) #Create the frequency log list for the inf and sup frequencies
    
    
    gbf.write('SOUR1:FREQ {}'.format(freq_inf)) #set frequency
    oscillo.write('autoset')
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
        #oscillo.write(':TIMebase:SCALe {}'.format(0.5*(frequency)**-1))
        oscillo.write(':MEASure:SOURce1 CH1')
        
            
           
        amp1, amp2 = measure_volt()
        
        oscillo.write('CHAN1:SCAL {}'.format(amp1/3))
        oscillo.write('CHAN2:SCAL {}'.format(amp2/3))
            
        if current_power < 2:
            time.sleep(5)
        else:
            time.sleep(1)  
      
        phase_list.append(measure_phase())
        gain_list.append(gain_meas(frequency)) #For each frequency, measure and stock the gain
        print(frequency, gain_meas(frequency))
        
      
        
    return freq_list, gain_list, phase_list

def save_file(freq_list, gain_list, phase_list):
    
  try:
    if question_YorN("Do you wish to save the data [Y/N]?") == "Y": #Si on veut sauvegarder les données
      nom_fichier = input("File name : (extension .txt) :\n")
      if not (nom_fichier.endswith(".txt")): #Si le nom ne finit pas par .txt
        nom_fichier+=".txt"
        print("L'extension .txt a été ajouté automatiquement")
              
      with open(nom_fichier, 'a') as fichier:
        fichier.write("#La premiere colonne correspond aux longueurs d'onde et la deuxieme colonne correspond aux intensités.\n#Voici les mesures pour l'intervalle specifié\n>>>>>>>>>>>>>Debut<<<<<<<<<<<<<<\n")
      
        for frequency, gain in zip(freq_list, gain_list):
            fichier.write("{} {}\n".format(frequency, gain))
          
        fichier.write(">>>>>>>>>>>>>Fin<<<<<<<<<<<<<<\n\n#Voici les informations des pics trouvés\n>>>>>>>>>>>>>Debut<<<<<<<<<<<<<<\n")
    
        for frequency, phase in zip(freq_list, phase_list):
            fichier.write("{} {}\n".format(frequency, phase))
            
        fichier.write(">>>>>>>>>>>>>Fin<<<<<<<<<<<<<<\n")

      print("Les données ont été ajoutées a {}".format(nom_fichier))
      
  except:
    print("Une erreur est survenue lors de l'écriture du fichier")
    
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
                print("Veuillez répondre Y pour Oui ou N pour Non")




#------------------------------Sweep---------------------------------

rm = pyvisa.ResourceManager()
rm.list_resources()



#amp=2

#print(gbf.query('*IDN?'))
#oscillo.write('CHAN1:SCAL {}'.format(amp))

#f=1000
#amp=1
#gbf.write('SOUR1:FREQ {}'.format(f))
#gbf.write('SOUR1:FREQ {}'.format(f))

#oscillo.write('autoset')
#oscillo.write(':MEASure:SOURce1 CH1')


#oscillo = find_port(oscillo_IDN)
#gbf = find_port(gbf_IDN)

oscillo_IDN = "GW,GDS"
gbf_IDN = "Rigol"

oscillo=rm.open_resource(find_port(oscillo_IDN))
gbf=rm.open_resource(find_port(gbf_IDN))

freq_min=float(input("Minimal frequency : "))
freq_max=float(input("Maximal frequency : "))
amplitude =float(input("Output voltage : "))


freq_list, gain_list, phase_list = gain_list(freq_min,freq_max,amplitude)

save_file(freq_list, gain_list, phase_list)
plt.plot(freq_list, gain_list, marker='o', linestyle='-', color='b')
plt.xscale('log')
plt.xlabel('Fréquence (Hz)')
plt.ylabel('Gain (Vout/Vin)')
plt.title('Réponse en fréquence')
plt.grid(True, which='both', linestyle='--')
plt.show()

#oscillo.close()    
#gbf.close()
rm.close()




    
            
        
    
    
    
    
