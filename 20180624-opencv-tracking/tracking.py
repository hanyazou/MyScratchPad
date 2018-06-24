import cv2
import av
import sys

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

def create_tracker(tracker_type):
    if int(minor_ver) < 3:
        tracker = cv2.Tracker_create(tracker_type)
    else:
        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        if tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        if tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        if tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        if tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        if tracker_type == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
    return tracker

if __name__ == '__main__' :

    output = av.open('/tmp/output.mp4', 'w')
    stream = output.add_stream('mpeg4', 30)
    stream.bit_rate = 8000000
    stream.pix_fmt = 'yuv420p'

    # Set up tracker.
    # Instead of MIL, you can also use

    tracker_types = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN']
    tracker_type = tracker_types[2]
    tracker = create_tracker(tracker_type)
 
    # Read video
    # video = cv2.VideoCapture(0)
    video = cv2.VideoCapture("/tmp/clip3.mp4")
 
    # Exit if video not opened.
    if not video.isOpened():
        print "Could not open video"
        sys.exit()
 
    # Read first frame.
    ok, frame = video.read()
    if not ok:
        print 'Cannot read video file'
        sys.exit()
     
    # Define an initial bounding box
    # bbox = (287, 23, 86, 320)
    bbox = (611, 249, 88, 160)
 
    # Uncomment the line below to select a different bounding box
    # bbox = cv2.selectROI(frame, False)
    print bbox
 
    # Initialize tracker with first frame and bounding box
    ok = tracker.init(frame, bbox)

    frame_count = 0
    fail_count = 0
    history = []
    history.append((bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2))
 
    while True:
        # Read a new frame
        ok, frame = video.read()
        if not ok:
            break
        frame_count = frame_count + 1
         
        # Start timer
        timer = cv2.getTickCount()
 
        # Update tracker
        prev_bbox = bbox
        ok, bbox = tracker.update(frame)
 
        # Calculate Frames per second (FPS)
        fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);

        #
        # XXX, force update bounding box if tracker failed
        #
        bbox_color = (255,0,0)
        if not ok:
            fail_count = fail_count + 1
            bbox = prev_bbox
            if 1 < len(history):
                dx = history[-1][0] - history[-2][0]
                dy = history[-1][1] - history[-2][1]
                bbox = (bbox[0] + dx, bbox[1] + dy, bbox[2], bbox[3])
            tracker = create_tracker(tracker_type)
            ok = tracker.init(frame, bbox)

            #ok, bbox = tracker.update(frame)
            if not ok:
                print 'XXX, force update bounding box FILED'
            bbox_color = (0,0, 255)

        history.append((bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2))
        if 1 < len(history):
            p1 = (int(history[-2][0]), int(history[-2][1]))
            p2 = (int(history[-1][0]), int(history[-1][1]))
            cv2.line(frame, p1, p2, (0, 255, 255), 2, 1)

        # Draw bounding box
        if ok:
            # Tracking success
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, bbox_color, 2, 1)

        # Tracking failure
        if 0 < fail_count:
            cv2.putText(frame, "Tracking failure detected : " + str(fail_count), (100,80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
 
        # Display tracker type on frame
        cv2.putText(frame, tracker_type + " Tracker", (100,20), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (50,170,50),2);
     
        # Display FPS on frame
        #cv2.putText(frame, "FPS : " + str(int(fps)), (100,50), cv2.FONT_HERSHEY_SIMPLEX,
        #            0.75, (50,170,50), 2);

        # Display frame no
        cv2.putText(frame, "Frame : " + str(int(frame_count)), (100,50), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (50,170,50), 2);
 
        # Display result
        cv2.imshow("Tracking", frame)


        stream.height = frame.shape[0]
        stream.width = frame.shape[1]
        output.mux(stream.encode(av.VideoFrame.from_ndarray(frame, format='bgr24')))
  
   
        # Exit if ESC pressed
        k = cv2.waitKey(1) & 0xff
        if k == 27 : break

    output.close()
