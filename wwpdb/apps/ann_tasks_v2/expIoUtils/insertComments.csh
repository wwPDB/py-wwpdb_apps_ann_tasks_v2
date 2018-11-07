#!/bin/csh
#
#  Odd but portable solution 
sed 's/\\ndata_/BIGdata_/g'  $1 > $2

