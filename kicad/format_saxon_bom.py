#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Asus
#
# Created:     09/05/2017
# Copyright:   (c) Asus 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys
DEBUG = False

class Component(object):
    def __init__(self,attribs):
        self.attributes = dict()
        for a in attribs:
            self.set_attribute(a)

    def set_attribute(self,key,value=None):
        self.attributes[key]=value

    def get_attribute(self,key):
        if self.attributes.has_key(key):
            return self.attributes[key]
        else:
            raise RuntimeError("Component instance has no key '%s'")%(key)

    def get_attributes(self):
        return self.attributes

    def get_keys(self):
        return self.attributes.keys()

    def print_component(self):
        print str(self.attributes)

    def print_component2(self,c='-'):
        print "%s%s%s%s%s%s%s"%(c,c,c,c,c,c,c)
        for k in self.attributes.keys():
            print "   %s:%s"%(k,self.attributes[k])

    def sort_refs(self):
        l=self.attributes['Reference'].split(',')
        l.sort()
        s = ""
        for index in range(len(l)):
            s += l[index]
            if index < len(l)-1:
                s += ","
        self.attributes['Reference']=s


def main(infileName,outfileName):

    print "***********"
    print "Infile: ",infileName
    with open(infileName,'r') as infile:
        lines = infile.readlines()

    print "found %d lines from input file"%(len(lines))

    #list of different fields for each component
    fields = lines[0].rstrip().split(",")
    fields = [f.lstrip() for f in fields]
    print "fields:",fields

    #list to hold each Component class instance
    components = []

    #pull values from each line in the BOM
    for line in lines[1:len(lines)]:

        #create a list of values from this line in the BOM
        values = line.rstrip().split(",")

        #create a new component to hold this line of values
        newComponent = Component(fields)

        #populate the values into this component's dictionary of attributes
        for index in range(len(values)):
            newComponent.set_attribute(fields[index],values[index])

        #add to the list of components
        components.append(newComponent)

    if outfileName == None:
        outfileName = infileName[:len(infileName)-4]+".BOM"

    #for the output BOM file - a list of component classes
    line_items = []

##    if DEBUG:
##        print "len(components): %d"%(len(components))
##        for i in range(10):
##            components[i].print_component2()
##    for component in components:
##        print "--: ",component.print_component()

    for component in components:

        if DEBUG: component.print_component2()

        #deal with the first component in the list here
        if len(line_items) == 0:
            component.set_attribute('quantity',1)
            line_items.append(component)

        #after first component has been added to BOM line items check all others for an existing match
        else:
            if DEBUG:
                print "<<<< Line Items:"
                for item in line_items:
                    item.print_component2("*")

            for line_item in line_items:

                new_unique_component = True
                if component.get_attributes()['supplier pn'] == line_item.get_attributes()['supplier pn']:

                    new_unique_component = False
                    line_item.set_attribute('quantity',int(line_item.get_attribute('quantity'))+1)
                    line_item.set_attribute('Reference',line_item.get_attribute('Reference') + "," + component.get_attribute('Reference'))
                    break

            if new_unique_component:

                component.set_attribute('quantity',1)
                line_items.append(component)

    print "Number of unique BOM line items found: %d"%(len(line_items))


##
###*******************************************************
##    print components[3].print_component2()
##    components[3].sort_refs()
##    print components[3].print_component2()
###*******************************************************
##

    print "Outfile: ",outfileName
    with open(outfileName,'w') as outfile:
        #get field names from first line item
        fieldNames = line_items[0].get_keys()
        fieldNames = ['Reference','quantity','Value','description','Datasheet','Footprint',
                        'supplier','supplier pn','manufacturer','manufacturer pn']
        #write title
        outfile.write("Reformatted Saxon BOM\n\n")
        #write field names at top of file
        for field in fieldNames:
            outfile.write("%s\t"%(field))
        outfile.write("\n")

        #write each component's values in a separate line
        for item in line_items:
            item.sort_refs()
            for index in range(len(fieldNames)):
                outfile.write("%s"%(item.get_attribute(fieldNames[index])))
                if index < len(fieldNames)-1: outfile.write("\t")
            outfile.write("\n")


if __name__ == '__main__':

    #only input file name given
    if (len(sys.argv) == 2):
        main(sys.argv[1],None)

    #input and output file names given
    elif (len(sys.argv) == 3):
        main(sys.argv[1],sys.argv[2])

    else:
        sys.stderr.write("Usage: python %s inputFilename [outputFilename]\n"%sys.argv[0])
        raise SystemExit(1)

