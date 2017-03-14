#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Asus
#
# Created:     02/04/2015
# Copyright:   (c) Asus 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from datetime import datetime

def main():

    debug = True
    target_line_found = False
    num_components_found = 0
    components_list = []


    #****************************************************
    # change these values to change the target file
    _filepath = "C:/test_data/"
    _filename = "test_schematic.sch"
##    _text_to_find = "F 2 "
##    _text_to_replace = "0000"
##    _replacement_text = "0001"
    #****************************************************



    backup_path ="C:/kicad file backups/"
    extension_position = _filename.rfind(".")
    timestamp = datetime.now().strftime(" %Y-%m-%d %H_%M_%S")
    backup_name = _filename[:extension_position]+"_backup_"+timestamp+_filename[extension_position:]

    if debug:
        print "input file: " + _filepath + _filename
        print "backup file: " + backup_path + backup_name



    infile = open(_filepath+_filename,'r')
    backupfile = open(backup_path+backup_name,'w')

    lines = infile.readlines()
    infile.close()
    if debug: print "Input file read and closed..."


    for line in lines:
        backupfile.write(line)
    backupfile.close()
    if debug: print "Backup file created and closed..."




    for line in lines:

        if line.strip("\n") == "$Comp":
            current_component = dict()
            num_components_found += 1


        elif line.strip("\n") == "$EndComp":
            components_list.append(current_component)

        else:

            line_elements = line.strip('\n').split(' ')

            #main component identifier line
            if line_elements[0] == "L":
                current_component['lib_reference'] = line_elements[1]
                current_component['designator'] = line_elements[2]

            #field 1 for value
            elif (line_elements[0] == "F") and (line_elements[1] == "1"):
                current_component['value'] = line_elements[2].strip('"')

            #field 2 for footprint
            elif (line_elements[0] == "F") and (line_elements[1] == "2"):
                current_component['footprint'] = line_elements[2].strip('"')

            #field 4 and up are user defined
            elif (line_elements[0] == "F") and (int(line_elements[1]) >= 4):
                field_label = line_elements[11]
                current_component[field_label] = line_elements[2].strip('"')




    print "number of components found: %d"%(num_components_found)

    component_count = 1

    for component in components_list:
        print '\ncomponent number: %d'%(component_count)
        for _property in component:
            print "%s: %s"%(_property,component[_property])

        component_count += 1






##    if target_line_found:
##        infile = open(_filepath+_filename,'w')
##        if debug: print "file reopened for writing..."
##        for line in lines:
##            #print line
##            infile.write(line)
##        infile.close()
##        if debug: print "  %d lines changed in file before closing"%(num_target_lines_found)
##
##    else:
##        if debug: print "Target string of %s not found in file"%(_text_to_find)



if __name__ == '__main__':
    main()
