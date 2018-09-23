import pcbnew

__version__ = "0.2.1"

print("Initializing kicad_wiretools version {}".format(__version__))

#import wiretools
import shielding

#import module_loader

#import wiretools_dumper

shielding.HashShieldGenerator().register()

print("done adding kicad_wiretools")
