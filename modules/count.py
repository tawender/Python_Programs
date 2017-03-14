import time

def count_sec(limit):
    limit = int(limit)
    for i in range(limit):
        print "%3d"%(i+1),
        time.sleep(1)
        if i < limit-1:
            print "%s%s%s%s%s"%(chr(8),chr(8),chr(8),chr(8),chr(8)),

def seconds_from_start(start_time,wait_sec):
##    print start_time
##    print wait_sec
    still_waiting = True
    secs_passed = int(time.clock() - start_time)

    print " ",

    while (still_waiting):

        _secs_passed = int(time.clock() - start_time)
##        print _secs_passed
##        print secs_passed
        if secs_passed < wait_sec:

            #check for another full second passing
            if _secs_passed == secs_passed + 1:
                secs_passed += 1
                print "%s%s%s%s%s"%(chr(8),chr(8),chr(8),chr(8),chr(8)),
                print "%3d"%(wait_sec - secs_passed),

        else:
            print
            still_waiting = False
        time.sleep(.1)

def main():
    max_sec = 10
    print "count to %d... "%max_sec,
    count_sec(max_sec)

if __name__ == '__main__':
    main()