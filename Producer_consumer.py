import queue
import threading
import cv2
import os
import numpy as np
import base64
import time

Empty = threading.Semaphore(1)
Full = threading.Semaphore(0)
Qlock = threading.Lock()

def extractFrames(fileName, outputBuffer):
    # Initialize frame count
    global Qlock

    count = 0

    # open video file
    vidcap = cv2.VideoCapture(fileName)

    # read first image
    success, image = vidcap.read()

    print("Reading frame {} {} ".format(count, success))
    while success:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)
        # encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)
        # add the frame to the buffer
        Empty.acquire()
        Qlock.acquire()
        outputBuffer.put(jpgAsText)
        Qlock.release()
        Full.release()
        success, image = vidcap.read()
        print('Reading frame {} {}'.format(count, success))
        count += 1
    print("Frame extraction complete")
    Empty.acquire()
    Qlock.acquire()
    outputBuffer.put("end")
    Qlock.release()
    Full.release()

def ConvertToGrayscale(Buffer):
    global Qlock
    # initialize frame count
    count = 0

    # load the next file
    Full.acquire()
    Qlock.acquire()
    frameAsText = Buffer.get()
    Qlock.release()
    Empty.release()
    # decode the frame
    jpgRawImage = base64.b64decode(frameAsText)
    # convert the raw frame to a numpy array
    jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)
    img = cv2.imdecode(jpgImage, cv2.IMREAD_UNCHANGED)
    while not frameAsText == "end":
        print("Converting frame {}".format(count))

        # convert the image to grayscale
        grayscaleFrame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        outFileName = "{}/grayscale_{:04d}.jpg".format("ass", count)
        cv2.imwrite(outFileName, grayscaleFrame)
        # generate output file name
        jpgAsText = base64.b64encode(grayscaleFrame)

        Empty.acquire()
        Qlock.acquire()
        Buffer.put(jpgAsText)
        Qlock.release()
        Full.release()
        count += 1

        Full.acquire()
        Qlock.acquire()
        frameAsText = Buffer.get()
        Qlock.release()
        Empty.release()

        # decode the frame
        jpgRawImage = base64.b64decode(frameAsText)
        # convert the raw frame to a numpy array
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)
        img = cv2.imdecode(jpgImage, cv2.IMREAD_UNCHANGED)


    Empty.acquire()
    Qlock.acquire()
    Buffer.put("end")
    Qlock.release()
    Full.release()


def displayFrames(inputBuffer):
    # initialize frame count
    global Qlock
    count = 0
    Full.acquire()
    Qlock.acquire()
    frameAsText = inputBuffer.get()
    Qlock.release()
    Empty.release()
    # go through each frame in the buffer until the buffer is empty
    while not frameAsText == "end":
        # get the next frame


        # decode the frame
        jpgRawImage = base64.b64decode(frameAsText)

        # convert the raw frame to a numpy array
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)

        # get a jpg encoded frame
        img = cv2.imdecode(jpgImage, cv2.IMREAD_UNCHANGED)

        print("Displaying frame {}".format(count))

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        cv2.imshow("Video", img)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break

        count += 1
        Full.acquire()
        Qlock.acquire()
        frameAsText = inputBuffer.get()
        Qlock.release()
        Empty.release()
    print("Finished displaying all frames")
    # cleanup the windows
    cv2.destroyAllWindows()


extractionQueue = queue.Queue()
filename = 'clip.mp4'

Extract = threading.Thread(target=extractFrames, args=(filename, extractionQueue,))
Convert = threading.Thread(target=ConvertToGrayscale, args=(extractionQueue,))
Display = threading.Thread(target=displayFrames, args=(extractionQueue,))
Extract.start()
time.sleep(1)
Convert.start()
Display.start()


# print ("main loop\n")