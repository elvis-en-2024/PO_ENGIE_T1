import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator
from engine.arera_tariffs import AreraTariffs

arera = AreraTariffs()
print(arera.ELE['residente'])
