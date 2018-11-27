# kicad_wiretools
Wire toolset for KiCad

* Shielding tool for creating web of shielding

## Code of conduct

New features should be created in new branch, so that 'master' branch is always stable. When new features are tested, they can be joined to master branch.

## TODO

** Wire & simulation tools

* [ ] Automatic naming of nets
* [ ] Frequency behaviour for each net; Resistance, impedance, ...
* [ ] Damping per net
* [ ] Trace-trace capacitance -> damping
* [ ] Shielding efficiency -> dB / Hz
* [ ] EMI radiance
* [ ] Digital pulse response per net
* [ ] Capacitance between net (trace) and shielding
* [ ] Graphically select traces
  * cut traces
  * delete traces
  * rename nets
* [ ] Calculations
  * [ ] Voltage drop
  * [x] Trace length per net
  * [ ] Trace inductance per net
  * [ ] Trace impedance
  * [ ] Power loss per trace
  * [ ] IPC 2221 maximum current per trace I = K * dT^0.44 * (W*H)^0.725; K=[0.024, 0.048]
  * [ ] Trace comparisation
  
** Shielding

  * [x] Free angle selection for hash
  * [x] Calculate the procentual coverage of shielding

