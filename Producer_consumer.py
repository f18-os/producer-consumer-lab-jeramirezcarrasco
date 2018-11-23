import queue
import threading
import cv2
import os
import numpy as np
import base64
import time


def extractFrames(fileName, outputBuffer, Qlock):
    # Keep track of the current frame for printing purposes
    count = 0
    #Read file
    vidcap = cv2.VideoCapture(fileName)
    success, image = vidcap.read()

    print("Reading frame {} {} ".format(count, success))
    while success:
        #Translate video frames into jpg
        success, jpgImage = cv2.imencode('.jpg', image)
        #grabs lock, acquires empty and releases full semaphores
        EmptyExtract.acquire()
        Qlock.acquire()
        #Puts jpg into buffer
        outputBuffer.put(jpgImage)
        Qlock.release()
        FullExtract.release()
        success, image = vidcap.read()
        count += 1
        print('Reading frame {} {}'.format(count, success))
    #After the video is finish the producer outputs end to signal end of transmission
    print("Frame extraction complete")
    EmptyExtract.acquire()
    Qlock.acquire()
    outputBuffer.put("end")
    Qlock.release()
    FullExtract.release()

def ConvertToGrayscale(extractionQueue,DisplayQueue,QlockExtract,QlockDisplay):

    count = 0
    #Grabs lock, acquires full and releases emtpy semaphore in the producer side
    FullExtract.acquire()
    QlockExtract.acquire()
    frameAsText = extractionQueue.get()
    QlockExtract.release()
    EmptyExtract.release()

    while not frameAsText == "end":
        # Translates jpg
        jpgImage = np.asarray(bytearray(frameAsText), dtype=np.uint8)
        img = cv2.imdecode(jpgImage, cv2.IMREAD_UNCHANGED)
        print("Converting frame {}".format(count))
        grayscaleFrame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #Puts the Jpg into consumer side
        EmptyDisplay.acquire()
        QlockDisplay.acquire()
        DisplayQueue.put(grayscaleFrame)
        QlockDisplay.release()
        FullDisplay.release()
        count += 1
        FullExtract.acquire()
        QlockExtract.acquire()
        frameAsText = extractionQueue.get()
        QlockExtract.release()
        EmptyExtract.release()
        #After the convertion its done it signals the displayer that the transmiton is finish
    EmptyDisplay.acquire()
    QlockDisplay.acquire()
    DisplayQueue.put("end")
    QlockDisplay.release()
    FullDisplay.release()

def displayFrames(DisplayQueue,QlockDisplay):
    count = 0
    FullDisplay.acquire()
    QlockDisplay.acquire()
    frameAsText = DisplayQueue.get()
    QlockDisplay.release()
    EmptyDisplay.release()
    while not frameAsText == "end":
        print("Displaying frame {}".format(count))
        cv2.imshow("Video", frameAsText)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break
        count += 1
        FullDisplay.acquire()
        QlockDisplay.acquire()
        frameAsText = DisplayQueue.get()
        QlockDisplay.release()
        EmptyDisplay.release()
    print("Finished displaying all frames")
    cv2.destroyAllWindows()

#Here i separated the semaphores into an extract side and a display side to have 2 producer/consumer working at the same time
#I did the same for locks
EmptyExtract = threading.Semaphore(1)
FullExtract = threading.Semaphore(0)
EmptyDisplay = threading.Semaphore(1)
FullDisplay = threading.Semaphore(0)
QlockExtract = threading.Lock()
QlockDisplay = threading.Lock()
extractionQueue = queue.Queue()
DisplayQueue = queue.Queue()
filename = 'clip.mp4'
#Call the threads
Extract = threading.Thread(target=extractFrames, args=(filename, extractionQueue,QlockExtract))
Convert = threading.Thread(target=ConvertToGrayscale, args=(extractionQueue,DisplayQueue,QlockExtract,QlockDisplay))
Display = threading.Thread(target=displayFrames, args=(DisplayQueue,QlockDisplay))
Extract.start()
Convert.start()
Display.start()


