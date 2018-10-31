# kicad_wiretools
Wire toolset for KiCad

* Shielding tool for creating web of shielding

## Code of conduct

New features should be created in new branch, so that 'master' branch is always stable. When new features are tested, they can be joined to master branch.

## TODO

** Wire & simulation tools

* [ ] Automatic naming of nets
* [ ] Trace length for each net
* [ ] Trace resistance, sum of (piecewise length * resistance); for each net
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
  
** Shielding

  * [x] Free angle selection for hash
  * [ ] Calculate the procentual coverage of shielding
