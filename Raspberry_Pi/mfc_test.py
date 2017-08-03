#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Asus
#
# Created:     31/03/2017
# Copyright:   (c) Asus 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import alicat

def main():
    mfc = alicat.FlowController(port=2,address='B')
    print 'created mfc'
    ret = mfc.get()
    print "type(ret): ",type(ret)
    print "ret",ret
    for key in ret:
        print key,ret[key]

if __name__ == '__main__':
    main()
