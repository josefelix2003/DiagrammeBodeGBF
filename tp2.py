import pyvisa
import math

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



freq_min=100
freq_max=100000
exp_max = math.floor(math.log10(freq_max))
exp_min = math.floor(math.log10(freq_min))
for exp in range(exp_min, exp_max+1):
    for i in range(1,10):
        break

        
        
oscillo.close()    
rm.close()
