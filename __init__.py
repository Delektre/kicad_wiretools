import pcbnew

__version__ = "0.2.3"

print("Initializing kicad_wiretools version {}".format(__version__))

#import wiretools
from . import shielding

#import module_loader

#import wiretools_dumper
print("Register shielding tools")
shielding.HashShieldGenerator().register()

#print("Register Wiretools")
#wiretools.WireTools().register()

#print("done adding kicad_wiretools")

from . import traceinfo

print("Register TraceInfo tools")

traceinfo.TraceTools().register()
