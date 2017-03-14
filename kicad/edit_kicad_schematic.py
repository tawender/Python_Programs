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
    num_target_lines_found = 0
    line_index = 0


    #****************************************************
    # change these values to change the target file
    _filepath = "C:/Users/Asus/Documents/kicad projects/CSS127_burn_in/"
    _filename = "CSS127_burn_in.sch"
    _text_to_find = "F 2 "
    _text_to_replace = "0000"
    _replacement_text = "0001"
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
    #if debug: print lines

    for line in lines:
        backupfile.write(line)
    backupfile.close()
    if debug: print "Backup file created and closed..."


    for line in lines:

        if debug: print line.strip("\n")

        if (_text_to_find in line) and (_text_to_replace in line):
            if debug: print "target line(%s) and text to replace(%s) found in this line"%(_text_to_find,_text_to_replace)

            if num_target_lines_found == 0:
                target_line_found = True
            num_target_lines_found += 1

            lines[line_index] = line.replace(_text_to_replace,_replacement_text)
            if debug: print "line now reads: %s"%(line)

        else:
            if debug: print "No match found in this line\n"

        line_index += 1


    if target_line_found:
        infile = open(_filepath+_filename,'w')
        if debug: print "file reopened for writing..."
        for line in lines:
            #print line
            infile.write(line)
        infile.close()
        if debug: print "  %d lines changed in file before closing"%(num_target_lines_found)

    else:
        if debug: print "Target string of %s not found in file"%(_text_to_find)



if __name__ == '__main__':
    main()
