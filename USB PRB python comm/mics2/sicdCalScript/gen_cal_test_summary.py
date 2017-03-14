import time
import sys
import os, fnmatch
import re

def find_text(filename):
    try:
        infile = open(filename,'r')
        for line in infile:
#            if re.match(find_strings[0][0],line): 
            if re.match("Setpoint changed",line): 
                outfile.write("Temp = %s"%line[20:22])
            if re.match("Candidate Frequency",line): 
                outfile.write(",%s"%line[22:38])
            if re.match("Candi4ate Frequency",line): 
                outfile.write(",%s"%line[22:38])
            if re.match("  S-ICD CC1000 Tx Test2",line): 
                outfile.write(",%s,"%line[27:29])
            if re.match("  S-ICD CC1000 Tx Test0",line): 
                outfile.write("%s,"%line[27])
            if re.match("  S-ICD CC1000 Rx Test2",line): 
                outfile.write("%s,"%line[27:29])
            if re.match("  S-ICD CC1000 Rx Test0",line): 
                outfile.write("%s"%line[27])
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
#        filename_search_string = "sicdCalScript_sn4851_run2.log"
        filename_search_string = cal_log_file 
        root = "c:/python_programs/mics2/sicdCalScript/"
#        global find_strings
#        find_strings = [ ["Candi*ate Frequency ",22,38],        
#                         ["  S-ICD CC1000 Tx Test2",27,29],    
#                         ["  S-ICD CC1000 Tx Test0",27,29],   
#                         ["  S-ICD CC1000 Rx Test2",27,29],  
#                         ["  S-ICD CC1000 Rx Test0",27,29]]   
        #********************************************

        global outfile
        now_text = time.strftime("%Y_%m_%d - %H_%M_%S")
        results_filename = root + "sicd_cal_results_" + now_text + ".csv"
        outfile = open(results_filename,'w')

        #write headings for results file
        outfile.write(",sn4851\n")
        outfile.write(",,,Tx Test2,")
        outfile.write("Tx Test0,")
        outfile.write("Rx Test2,")
        outfile.write("Rx Test0\n")
        
        find_files(filename_search_string,root)
        print "created output file: %s"%(results_filename)

    except Exception as e:
        print "Exception found in main(): " + repr(e)

if __name__ == '__main__':
    main(str(sys.argv[1]))


    

    

