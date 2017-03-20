import cv2
import train
import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt



TRAIN = False

svc_filename = 'svc_model.p'
if TRAIN:
    svc_pickle = train.train_data()
    train.save_train_model(svc_pickle,svc_filename)
else:
    svc_pickle = train.load_svc_model(svc_filename)


print(svc_pickle)

def find_cars(img, ystart, ystop, scale, svc, X_scaler, orient, pix_per_cell, cell_per_block, spatial_size, hist_bins):
    draw_img = np.copy(img)
    img = img.astype(np.float32) / 255

    boxes = []

    img_tosearch = img[ystart:ystop, :, :]
    ctrans_tosearch = cv2.cvtColor(img_tosearch, cv2.COLOR_RGB2HLS)
    if scale != 1:
        imshape = ctrans_tosearch.shape
        ctrans_tosearch = cv2.resize(ctrans_tosearch, (np.int(imshape[1] / scale), np.int(imshape[0] / scale)))

    ch1 = ctrans_tosearch[:, :, 0]
    ch2 = ctrans_tosearch[:, :, 1]
    ch3 = ctrans_tosearch[:, :, 2]

    # Define blocks and steps as above
    nxblocks = (ch1.shape[1] // pix_per_cell) - 1
    nyblocks = (ch1.shape[0] // pix_per_cell) - 1
    nfeat_per_block = orient * cell_per_block ** 2
    # 64 was the orginal sampling rate, with 8 cells and 8 pix per cell
    window = 64
    nblocks_per_window = (window // pix_per_cell) - 1
    cells_per_step = 2  # Instead of overlap, define how many cells to step
    nxsteps = (nxblocks - nblocks_per_window) // cells_per_step
    nysteps = (nyblocks - nblocks_per_window) // cells_per_step

    # Compute individual channel HOG features for the entire image
    hog1 = train.get_hog_features(ch1, orient, pix_per_cell, cell_per_block, feature_vec=False)
    hog2 = train.get_hog_features(ch2, orient, pix_per_cell, cell_per_block, feature_vec=False)
    hog3 = train.get_hog_features(ch3, orient, pix_per_cell, cell_per_block, feature_vec=False)

    for xb in range(nxsteps):
        for yb in range(nysteps):
            ypos = yb * cells_per_step
            xpos = xb * cells_per_step
            # Extract HOG for this patch
            hog_feat1 = hog1[ypos:ypos + nblocks_per_window, xpos:xpos + nblocks_per_window].ravel()
            hog_feat2 = hog2[ypos:ypos + nblocks_per_window, xpos:xpos + nblocks_per_window].ravel()
            hog_feat3 = hog3[ypos:ypos + nblocks_per_window, xpos:xpos + nblocks_per_window].ravel()
            hog_features = np.hstack((hog_feat1, hog_feat2, hog_feat3))

            xleft = xpos * pix_per_cell
            ytop = ypos * pix_per_cell

            # Extract the image patch
            subimg = cv2.resize(ctrans_tosearch[ytop:ytop + window, xleft:xleft + window], (64, 64))

            # Get color features
            spatial_features = train.bin_spatial(subimg, size=spatial_size)
            hist_features = train.color_hist(subimg, nbins=hist_bins)

            # Scale features and make a prediction
            #features.append(np.concatenate((spatial_features, hist_features, hog_features)))
            test_features = X_scaler.transform(
                np.hstack((spatial_features, hist_features, hog_features)).reshape(1, -1))
            # test_features = X_scaler.transform(np.hstack((shape_feat, hist_feat)).reshape(1, -1))
            test_prediction = svc.predict(test_features)

            if test_prediction == 1:
                xbox_left = np.int(xleft * scale)
                ytop_draw = np.int(ytop * scale)
                win_draw = np.int(window * scale)
                #cv2.rectangle(draw_img, (xbox_left, ytop_draw + ystart), (xbox_left + win_draw, ytop_draw + win_draw + ystart), (0, 0, 255), 6)
                boxes.append([(xbox_left, ytop_draw + ystart),
                              (xbox_left + win_draw, ytop_draw + win_draw + ystart)])

    return draw_img, boxes


def draw_boxes(img, bboxes, color=(0, 0, 255), thick=3):
    # Make a copy of the image
    draw_img = np.copy(img)
    # Iterate through the bounding boxes
    for bbox in bboxes:
        # Draw a rectangle given bbox coordinates
        cv2.rectangle(draw_img, bbox[0], bbox[1], color, thick)
    # Return the image copy with boxes drawn
    return draw_img


def history_to_single_list():
    bbox_list = []
    for history in heatmap_history:
        for box in history:
            bbox_list.append(box)
    return bbox_list


cap = cv2.VideoCapture('project_video.mp4')
cap = cv2.VideoCapture('test_video.mp4')
# cap = cv2.VideoCapture('harder_challenge_video.mp4')
#cap = cv2.VideoCapture('challenge_video.mp4')

ystart = 400
ystop = 656
scale = 1.5

img = mpimg.imread("report/sample1.png")

svc = svc_pickle["svc"]
X_scaler = svc_pickle["scaler"]
orient = svc_pickle["orient"]
pix_per_cell = svc_pickle["pix_per_cell"]
cell_per_block = svc_pickle["cell_per_block"]
spatial_size = svc_pickle["spatial_size"]
hist_bins = svc_pickle["hist_bins"]

out_img,boxes = find_cars(img, ystart, ystop, scale, svc, X_scaler, orient, pix_per_cell, cell_per_block, spatial_size, hist_bins)

print(boxes)




out = draw_boxes(out_img,boxes)

heat = np.zeros_like(out[:,:,0]).astype(np.float)

def add_heat(heatmap, bbox_list):
    # Iterate through list of bboxes
    for box in bbox_list:
        # Add += 1 for all pixels inside each bbox
        # Assuming each "box" takes the form ((x1, y1), (x2, y2))
        heatmap[box[0][1]:box[1][1], box[0][0]:box[1][0]] += 1

    # Return updated heatmap
    return heatmap# Iterate through list of bboxes

def apply_threshold(heatmap, threshold):
    # Zero out pixels below the threshold
    heatmap[heatmap <= threshold] = 0
    # Return thresholded map
    return heatmap



def draw_labeled_bboxes(img, labels):
    # Iterate through all detected cars
    for car_number in range(1, labels[1]+1):
        # Find pixels with each car_number label value
        nonzero = (labels[0] == car_number).nonzero()
        # Identify x and y values of those pixels
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])
        # Define a bounding box based on min/max x and y
        bbox = ((np.min(nonzerox), np.min(nonzeroy)), (np.max(nonzerox), np.max(nonzeroy)))
        # Draw the box on the image
        cv2.rectangle(img, bbox[0], bbox[1], (0,0,255), 6)
    # Return the image
    return img

from scipy.ndimage.measurements import label

heat = add_heat(heat,boxes)
heat = apply_threshold(heat,3)

heatmap = np.clip(heat, 0, 255)

labels = label(heatmap)

draw_img = draw_labeled_bboxes(np.copy(out_img), labels)

plt.imshow(draw_img)
plt.show()

heatmap_history = []
heatmap_history_length = 12

def append_heatmap_history(bboxes):
    heatmap_history.append(bboxes)
    if len(heatmap_history) > heatmap_history_length:
        del heatmap_history[0]



frame_id = 0
while(cap.isOpened()):


    ret, out = cap.read()
    in_img = out
    if ret==True:

        ystart = 400
        ystop = 656
        scale = 1.5

        out,boxes = find_cars(out, ystart, ystop, scale, svc, X_scaler, orient, pix_per_cell, cell_per_block,
                            spatial_size, hist_bins)

        append_heatmap_history(boxes)

        ystart = 380
        ystop = 480
        scale = 1

        out,boxes = find_cars(out, ystart, ystop, scale, svc, X_scaler, orient, pix_per_cell, cell_per_block,
                            spatial_size, hist_bins)


        append_heatmap_history(boxes)

        ystart = 500
        ystop = 700
        scale = 2.5

        out,boxes = find_cars(out, ystart, ystop, scale, svc, X_scaler, orient, pix_per_cell, cell_per_block,
                            spatial_size, hist_bins)



        append_heatmap_history(boxes)

        boxes = history_to_single_list()

        heat = np.zeros_like(out[:, :, 0]).astype(np.float)
        heat = add_heat(heat, boxes)
        cv2.imshow('heatmap', heat)
        heat = apply_threshold(heat, 12)

        heatmap = np.clip(heat, 0, 255)

        labels = label(heatmap)

        draw_img = draw_labeled_bboxes(np.copy(out), labels)


        cv2.imshow('result', draw_img )

        print("heatmap points:", boxes)

        filename = ("video/frame_{:04d}.png".format(frame_id))
        cv2.imwrite(filename,draw_img)
        frame_id += 1


        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.imwrite("report/sample_pre.png", in_img)
            cv2.imwrite("report/sample_out.png", out)
            break
    else:
        break

cap.release()
#cv2.destroyAllWindows()