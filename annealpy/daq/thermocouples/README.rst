This folder contains parameters for thermocouple conversion.

Each file is expected to contain the coefficient of the polynomial used for
for conversion. The keys should be of the form 'Ci' where is is the degree of
the associated term. The voltage are expressed in mV and the temperature in
degree Celsius.

If depending on the range different polynomial should be used, the file should
contain multiple sections, each corresponding to a different range. The range
of validity in mV should be used as key in a comma separated format.

An example can be found for K type thermocouples.
