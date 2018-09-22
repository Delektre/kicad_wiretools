import pcbnew

print("Initializing kicad_wiretools version {}".format(1.0))

#import wiretools
import shielding

#import module_loader

#import wiretools_dumper

shielding.ShieldingHashGenerator.register()

print("done adding kicad_wiretools")
