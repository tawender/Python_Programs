import time
import sys
import os, fnmatch
import re

def find_text(filename):
    try:
        infile = open(filename,'r')
        for line in infile:
            if re.match("Loop Index =  0",line):
                freq = 0
            elif re.match("Loop Index =  1",line):
                freq = 1

            if re.match("Setpoint changed",line): 
                outfile.write("Temp = %s"%line[20:22])
	    elif re.match("PRB Ave Frequency",line): 
                outfile.write(",%s"%line[22:31])
            elif re.match("PRB Ave Power",line): 
                outfile.write(",%s"%line[20:24])
                if freq = 1
                    outfile.write("\n")
    except Exception as e:
        print "Exception in find_text(): " + repr(e)

def find_files(pattern, root=os.curdir):
    """Locate all files matching supplied filename pattern in and below
       supplied root directory.
    """
    try:
        num_files_found = 0
        for path, dirs, files in os.walk(root):
            for f_name in fnmatch.filter(files, pattern):
                filename = os.path.join(path, f_name)
                num_files_found += 1
                print "file found: " + repr(f_name)
                find_text(filename)
        if num_files_found == 0:
            print "No files found matching filter"

    except Exception as e:
        print "Exception found in find_files(): " + repr(e)

def main(cal_log_file):
    try:
        #********************************************
        # setup search parameters here
        filename_search_string = cal_log_file 
        root = "c:/python_programs/mics2/sicdVcoScript/"
        #********************************************

        global outfile
        now_text = time.strftime("%Y_%m_%d - %H_%M_%S")
        results_filename = root + "sicd_vco_results_" + now_text + ".csv"
        outfile = open(results_filename,'w')

        #write headings for results file
        outfile.write(",sn4851\n")
        outfile.write(",,,freq low,")
        outfile.write("freq high\n")
        
        find_files(filename_search_string,root)
        print "created output file: %s"%(results_filename)

    except Exception as e:
        print "Exception found in main(): " + repr(e)

if __name__ == '__main__':
    main(str(sys.argv[1]))


    

    

