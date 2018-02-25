"""
Updated on Sat Feb 24 15:24 2018
- tkinter library used to enable file selection dialogues for loading data and saving output
- options now specified with a dialogue box rather than a command line
Created on Thu Feb 06 17:29 2015

This program takes csv files containing voltage readings
(20,000 of them per file) and removes the extraneous and noisy data leaving
just the key points - those denoting the peak and trough of each spike.

The output is written to a new file.

The output csv file has the following format:
File, mV minimum, mV maximum, Hz

It's been useful to me if not anyone else. 

Please note:
* The lowest range (default 0-50mV) of spike amplitudes is very, very noise-
prone. This means that the data, where it appears, should probably not be 
trusted. 

* This program has very little error handling and is liable to crash without 
explanation if given bad data (such as csv files containing certain data). For
the envisioned use cases it should be okay but no promises are made.

Feel free to use, modify, etc. this code as you see fit.

@author: mj261
"""

import csv, math, os, re, time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

""" 
    Function definitions. 
    
    The actual program gets more comments, promise.
    
"""


def writeStuff(listToWrite, fileToWriteTo):
    # writes a list to a file - UNUSED
    with open(fileToWriteTo, 'wt', newline = '') as file:
        write = csv.writer(file)
        for data in listToWrite:
            write.writerow([data])

        return


def getCSVs(folderPath):
    # returns a list of non-'clean_' CSV files for inspection
    returnlist = []
    i = 0
    print("Searching for .csv files in " + folderPath)
    for dirpath, dirnames, files in os.walk(folderPath):
        for file in files:
            if re.match('^(?!clean_).+\\.csv$', file):
                returnlist.append(os.path.join(dirpath, file))
                i += 1
    print("Found " + str(i) + " files.")
    return returnlist


def getSpikeList(aFile):
    # return a list of points for data in aFile
    print(" Accessing...")
    # open file
    with open(aFile, 'rt', encoding='utf-8-sig') as csvfile:
        textlines = []
        #print("Access granted.")
        myfile = csv.reader(csvfile)

        # read file contents into a list
        for line in myfile:
            linelist = "".join(line)
            textlines.append(linelist)
            #print("Found line: " + linelist)

        #print("Done.")
    return textlines


def cleanPointList(pointlist, thMax, thMin):
    print("  Cleaning...")
    spikelist = []
    # strip out useless sub-threshold data    
    for lineval in pointlist:
        lineval = float(lineval) * 1000.0
        if lineval > thMax or lineval < thMin:
            spikelist.append(str(lineval))

    return spikelist


def findExtremes(spikelist):
    # returns a list containing only the high and low points of spikes
    print("   Finding spike points...")
    returnList = []
    pending = 0.0
    lastval = 0.0
    # i = 0
    mode = 1 # 1: expecting larger; -1: expecting smaller
    # loop through looking for extreme points
    for lineval in spikelist:
        lineval = float(lineval)
        # find the high point
        if mode == 1:
            if lineval > pending:
                #print("Pending: " + str(lineval)) 
                pending = lineval
        # find the low point        
        elif mode != 1:
            if lineval < pending:
                #print("Pending: " + str(lineval))  
                pending = lineval
        # when crossing the origin switch modes
        if math.copysign(1, lineval) != math.copysign(1, lastval):
            if pending != 0:
                #print("Writing: " + str(pending) + " as point " + str(i))
                #i += 1
                returnList.append(str(pending))
                pending = lineval
            if mode == -1:
                mode = 1
                #print("Now looking for high point.")
            else:
                mode = -1
                #print("Now looking for low point.")

        lastval = lineval

    return returnList


def Analyse(points, binSize = 50):
    # returns a dictionary of binSize keys pointing to the # of spikes of that magnitude
    print("    Producing summary...")
    amplitudes = {}
    lastpoint = 0
    amp = 0
    write = 0
    ampBin = 0

    for point in points:
        point = float(point)
        if write == 1:
            write = 0
            amp = abs(point) + abs(lastpoint)
            # enter the amplitude into the list
            ampBin = amp // binSize
            ampBin = int(ampBin)
            if ampBin not in amplitudes:
                amplitudes[ampBin] = 1
            else:
                amplitudes[ampBin] += 1
            #print("Incementing amplitudes[" + str(ampBin) + "] (" + str(amp) + "//" + str(binSize) + " = " + str(ampBin) + ")")
        else:
            write = 1
            lastpoint = point

    return amplitudes


def printAnalysis(analysis, binFactor = 50, includeHeading = True):
    # Prints a nice, readable summary of an analysis dictionary
    value = ""
    binFactor = int(binFactor)
    binBound = 0

    if includeHeading:
        print("Spike readout: [amplitude range | frequency]")

    for key in analysis:
        value = analysis[key]
        binBound = binFactor * int(key)
        print(str(binBound) + "-" + str(binBound + binFactor-1) + "mV | " + str(value) + "Hz")

    return


def writeOutputToCSV(analysis, outputFile, fromFile, binFactor = 50):
    # Writes data in a nice csv format for analysis to output to a spreadsheet
    headersWritten = os.path.isfile(outputFile)

    with open(outputFile, 'at', newline='') as file:
        write = csv.writer(file)
        # Write the headers
        if not headersWritten:
            write.writerow(["File", "mV minimum", "mV maximum", "Hz"])

        for key in analysis:
            write.writerow([fromFile, str(int(key * binFactor)), str(int((key+1) * binFactor)-1), analysis[key]])

    file.close()
    print("Wrote summary to file " + outputFile)


class MyDialog(simpledialog.Dialog):

    def body(self, master):

        self.answered = False
        self.title("spikeAnalyser")
        intro = "Welcome to spikeAnalyser.\n\n"
        intro += "This program extracts spikes from a series of voltage readings.\n\n"
        intro += "First, you may specify options in this pane. " \
                 "Blank options are replaced with the default (in parentheses).\n"
        intro += "Next, you will be prompted to open a file: select ALL files you want analysed.\n"
        intro += "After selecting input files, you will choose where to save the output.\n"
        intro += "Finally, once the program has completed, you will see a summary of its performance.\n"
        simpledialog.Message(master, text=intro, justify=simpledialog.LEFT, aspect=250)\
            .grid(row=1, columnspan=3)
        simpledialog.Label(master, text="queries -> matt.jaquiery@psy.ox.ac.uk")\
            .grid(row=0, column=1, columnspan=2)
        simpledialog.Label(master, text="Ignore upward spikes below:").grid(row=2, sticky=simpledialog.W)
        simpledialog.Label(master, text="mV (default = 30)").grid(row=2, column=2, sticky=simpledialog.W)
        simpledialog.Label(master, text="Ignore downward spikes above:").grid(row=3, sticky=simpledialog.W)
        simpledialog.Label(master, text="mV (default = -20)").grid(row=3, column=2, sticky=simpledialog.W)
        simpledialog.Label(master, text="Bin width:").grid(row=4, sticky=simpledialog.W)
        simpledialog.Label(master, text="mV (default = 25)").grid(row=4, column=2, sticky=simpledialog.W)

        self.e1 = simpledialog.Entry(master)
        self.e2 = simpledialog.Entry(master)
        self.e3 = simpledialog.Entry(master)

        self.e1.grid(row=2, column=1)
        self.e2.grid(row=3, column=1)
        self.e3.grid(row=4, column=1)

        return self.e1  # initial focus

    def apply(self):
        self.answered = True
        self.threshMax = self.e1.get() if len(self.e1.get()) else threshMax
        self.threshMin = self.e2.get() if len(self.e2.get()) else threshMin
        self.binSize = self.e3.get() if len(self.e3.get()) else binSize



"""

    Actual program starts here. 
    I know I probably should have done this using object-oriented stuff but 
    hey, this is Python, not C#.

"""

# The default variables
threshMax = 30 # ignore spikes less than this high above x axis
threshMin = -20 # ignore spikes less than this low below x axis
binSize = 25 # how big (in Volts) should the bins be?

# Get options
root = tk.Tk()
root.withdraw()
d = MyDialog(root)

if not d.answered:
    raise SystemExit(0)

threshMax = d.threshMax
threshMin = d.threshMin
binSize = d.binSize

# Get .csv files to work with
fileList = filedialog.askopenfilenames(parent=root, title="Select raw data files",
                                        filetypes=(("comma-separated values", "*.csv"), ("all files","*.*")))

if not len(fileList) > 0:
    print("No input files provided - exiting.")
    raise SystemExit(0)

# Select save location for output
outputFile = filedialog.asksaveasfilename(title="Save output file as", defaultextension=".csv",
                                       filetypes=(("comma-separated values", "*.csv"), ("all files","*.*")))

if not outputFile:
    print("No output file - exiting.")
    raise SystemExit(0)

# initalise some variables - why do I do this in python? Habit, I guess.
cleanlines = []  # list for csv entries
summary = {}  # dictionary for bins and their sizes
i = 0  # track # of files so we can look cool
skippedFiles = []  # files we couldn't process

startTime = time.time() # we'll record the time so we can look really smug at the end

for someFile in fileList: # iterate the file list
    print("Processing " + os.path.basename(someFile))
    cleanlines = getSpikeList(someFile) # get a list of the spikes
    if type(cleanlines) is not list: # make sure we actually got a list
        print("  Error.")
        skippedFiles.append(someFile)
        continue
    cleanlines = cleanPointList(cleanlines, threshMax, threshMin) # strip out the noise
    # writeStuff(cleanlines, os.path.join(os.path.basename, "clean_cleaned.csv"))
    cleanlines = findExtremes(cleanlines) # strip out everything but high and low points
    # writeStuff(cleanlines, os.path.join(os.path.basename, "clean_extremes.csv"))
    summary = Analyse(cleanlines, binSize) # generate the analysis of amplitude and Hz
    # writeStuff(cleanlines, os.path.join(os.path.basename, "clean_summary.csv"))
    printAnalysis(summary, binSize) # show our results
    # and provide a copy in a doggy-bag for the user to enjoy later
    writeOutputToCSV(summary, outputFile, os.path.basename(someFile), binSize)
    i += 1  # tracking # of files to look professional

endTime = time.time()
elapsedTime = str(endTime - startTime)
# the payoff of the professional look - job and time-to-complete
msg = f"Success.\n\nSettings:\nThresholds: [{threshMin},{threshMax}]mV\n" \
      f"Bin size: {binSize}mV\nFiles processed: {str(i)}\nTime taken: {elapsedTime[:4]}s\n\n" \
      f"Output saved in {outputFile}\n"
if len(skippedFiles):
    msg += f"\nSkipped files:"
    for f in skippedFiles:
        msg += "\nf"
    msg += "\n"
msg += f"\nThank you for using spikeAnalyser."
messagebox.showinfo("Summary", msg)
