

def transpose_csv(infile):
    try:
        if type(infile) is file:
            if infile.closed:
                i_f = open(infile.name, 'r')
            elif infile.mode == 'r':
                i_f = infile
            else:
                raise RuntimeError("expected file object opened for reading")
        elif type(infile) is str:
            i_f = open(infile, 'r')
        else:
            raise RuntimeError("argument must be type string or file")
        o_f = open(i_f.name[0:len(i_f.name)-4] + "_transposed.csv", 'w')
        columns = 0
        max_entries = 0
        list2D = []
        for line in i_f:
            columns += 1
            item_begin = 0
            line = line.strip()
            l = line.split(",")
            list2D.append(l)

        for col in range(columns):
            if len(list2D[col]) > max_entries: max_entries = len(list2D[col])

        for j in range(max_entries):
            
            for k in range(columns):
                if j < len(list2D[k]):
                    o_f.write("%s,"%list2D[k][j])
                else:
                    o_f.write(",")
            o_f.write("\n")

        i_f.close()
        o_f.close()
            
    except Exception as e:
        print "Exception in transpose: " + repr(e)

if __name__ == "__main__":
    transpose_csv("democsv.csv")