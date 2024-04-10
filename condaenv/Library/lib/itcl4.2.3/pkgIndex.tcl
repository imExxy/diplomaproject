# -*- tcl -*-
# Tcl package index file, version 1.1
#

if {![package vsatisfies [package provide Tcl] 8.6-]} {return}

if {[package vsatisfies [package provide Tcl] 9.0-]} {
    package ifneeded itcl 4.2.3 \
	    [list load [file join $dir tcl9itcl423.dll] Itcl]
} else {
    package ifneeded itcl 4.2.3 \
	    [list load [file join $dir itcl423.dll] Itcl]
}
package ifneeded Itcl 4.2.3 [list package require -exact itcl 4.2.3]