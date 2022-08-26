# gr-stamina

This is the stamina-write-a-block package meant as a guide to building GNU RAdio out-of-tree packages. To use the stamina blocks, the Python  namespaces is in 'stamina', which is imported as:

    import stamina

See the Doxygen documentation for details about the blocks available in this package. A quick listing of the details can be found in Python after importing by using:

    help(stamina)

## Getting Started

This repository contains an out-of-tree GNU Radio module with two blocks that control the beams of a mmWave RF front-end: 
- The ```beam_mapper``` block converts beam indexes (from 1 to 63) to the GPIO bank configuration that selects the given beams of the mmWave RF front-end. 
- The ```manual_beam``` block lets users manually select beam indexes to feed the beam_mapper, be it using variables or a Qt range block.
- The ```beam_sweep``` block sweeps over different beams with configurable beam patterns, duration and cadence.
- The ```rss_calculator``` block calculates the received signal strength of received signal and sends this information to the kpi_gg.
- The ```kpi_agg``` block labels the received signal strength information with the current beam and forwards this to the beam selector.
- The ```beam_selector``` block receives KPIs of the different beams and decide the best beam to use for data transmission.

Note: The ```beam_mapper``` block leverages an USRP GPIO interface to control a physical mmWave RF front-end. However, different mmWave RF front-ends may have different control APIs over the GPIO interface, e.g., toggling different ranges of pins to carry out similar operations. Therefore, to support a wider range of mmWave RF front-ends, we expose this configuration for the ```beam_mapper``` block using a ```gpio_config.json``` file, and include an example of how it can be used in the ```examples/``` folder. 


### Dependencies

* uhd-host
* libuhd-dev
* swig
* cmake
* gnuradio-dev

### Installation

```
mkdir build;
cd build;
cmake ../
make
sudo make install
sudo ldconfig
```

### Examples

Example scripts located in the ```examples/``` directory.
- The ```complete_initial_access.grc``` file demonstrates all the components of the initial access procedure.
- The ```manual_beam_control.grc``` file allow users to manually select beams of their mmWave front-end.
