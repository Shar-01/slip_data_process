'''

modified on June 27 2021 by Sharmita

'''



import rosbag, sys, csv
import time
import string
import os #for file management make directory
import shutil #for file management, copy file
import numpy as np

bag_folder = "../category_bags/states"
topic_names = ['/spot1/joint_states', '/spot2/joint_states','/spot3/joint_states' ] #
csv_folder = "/home/deysh/rosbag_analysis_pipeline/csvs/joint_states"

#verify correct input arguments: 1 or 2
if (len(sys.argv) > 2):
    print "invalid number of arguments:   " + str(len(sys.argv))
    print "should be 2: 'bag2csv.py' and 'bagName'"
    print "or just 1  : 'bag2csv.py'"
    sys.exit(1)
elif (len(sys.argv) == 2):
    listOfBagFiles = [sys.argv(1)]
    print "reading only 1 bagfile: " + str(listOfBagFiles(0))
elif (len(sys.argv) == 1):
    listOfBagFiles = [os.path.join(bag_folder, f) for f in os.listdir(bag_folder) if f[-4:] == ".bag"]    #get list of only bag files in current dir.
    numberOfFiles = str(len(listOfBagFiles))
    print "reading all " + numberOfFiles + " bagfiles in current directory: \n"
    for f in listOfBagFiles:
        print f
    print "\n press ctrl+c in the next 10 seconds to cancel \n"
    time.sleep(10)
else:
    print "bad argument(s): " + str(sys.argv)    #shouldnt really come up
    sys.exit(1)

count = 0
for bagFile in listOfBagFiles:
    count += 1
    print "reading file " + str(count) + " of  " + numberOfFiles + ": " + bagFile
    #access bag
    bag = rosbag.Bag(bagFile)
    bagContents = bag.read_messages()
    bagName = bag.filename


    #create a new directory for saving csvs
    if csv_folder is None:
        
        csv_folder = string.rstrip(bagName, ".bag")
    try:    #else already exists
        os.makedirs(csv_folder)
    except:
        pass
    #shutil.copyfile(bagName, os.path.join(csv_folder, bagName))


    #get list of topics from the bag
    listOfTopics = []
    for topic, msg, t in bagContents:
        if topic not in listOfTopics:
            listOfTopics.append(topic)


    for topicName in listOfTopics:
        if topic_names is not None:
            if topicName not in topic_names:
                continue
        #Create a new CSV file for each topic
        filename = os.path.join(
                csv_folder, os.path.basename(bagName)[:-4] + 
                string.replace(topicName, '/', '_') + '.csv')
        with open(filename, 'w+') as csvfile:
            filewriter = csv.writer(csvfile, delimiter = ',')
            firstIteration = True    #allows header row
            for subtopic, msg, t in bag.read_messages(topicName):    # for each instant in time that has data for topicName
                #parse data from this instant, which is of the form of multiple lines of "Name: value\n"
                #    - put it in the form of a list of 2-element lists
                msgString = str(msg)
                msgList = string.split(msgString, '\n')
                instantaneousListOfData = []
                for nameValuePair in msgList:
                    splitPair = string.split(nameValuePair, ':')
                    for i in range(len(splitPair)):    #should be 0 to 1
                        splitPair[i] = string.strip(splitPair[i])
                    instantaneousListOfData.append(splitPair)
                #write the first row from the first element of each pair
                if firstIteration:    # header
                    headers = ["rosbagTimestamp"]    #first column header
                    for pair in instantaneousListOfData:
                        if pair[1].startswith('[') and pair[1].endswith(']'):
                            value = map(str, pair[1].rstrip(']').lstrip('[').split(','))
                            for i, v in enumerate(value):
                                headers.append(pair[0]+'.'+str(i))
                        else:
                            headers.append(pair[0])
                        
                    filewriter.writerow(headers)
                    firstIteration = False
                # write the value from each pair to the file
                values = [str(t)]    #first column will have rosbag timestamp
                for pair in instantaneousListOfData:
                    if pair[1].startswith('[') and pair[1].endswith(']'):
                        try:
                            value = map(float, pair[1].rstrip(']').lstrip('[').split(','))
                        except:
                            value = map(str, pair[1].rstrip(']').lstrip('[').split(','))
                        for i, v in enumerate(value):
                            values.append(v)
                    else:
                        values.append(pair[1])
                filewriter.writerow(values)
    bag.close()
print "Done reading all " + numberOfFiles + " bag files."