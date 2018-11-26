import pcbnew

__version__ = "0.2.3"

print("Initializing kicad_wiretools version {}".format(__version__))

#import wiretools

from .shielding import HashShieldGenerator

#import module_loader

#import wiretools_dumper

# -----------------------------------------------------------
print("Register shielding tools")
HashShieldGenerator().register()
print(" HashShieldGenerator registration compeleted.")
# -----------------------------------------------------------

#print("Register Wiretools")
#wiretools.WireTools().register()

#print("done adding kicad_wiretools")

# -----------------------------------------------------------
print("Register TraceInfo tools")

from .traceinfo import TraceInfoGenerator
TraceInfoGenerator().register()

print(" TraceInfoGenerator registration completed.")
# -----------------------------------------------------------
