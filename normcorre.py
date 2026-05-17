import numpy as np
import tempfile

import caiman as cm
from caiman.motion_correction import MotionCorrect, sliding_window
import cv2


# Piecewise rigid registration (normcorre)
def compute_pwrigid_transform(images, iref=None, **kwargs):
    tmp = tempfile.NamedTemporaryFile()
    orig_file = tmp.name + '.tif'
    m_orig = cm.movie(images)
    m_orig.save(orig_file)
    
    # Run rigid, then piecewise rigid registration
    c, dview, n_processes = cm.cluster.setup_cluster(
        backend='local', n_processes=None, single_thread=False)
    mc_params = dict(dview=dview,
                     max_shifts=(6, 6),
                     strides=(96, 96), #(48, 48)
                     overlaps=(32, 32), #(24, 24)
                     num_frames_split=1,
                     max_deviation_rigid=6,
                     pw_rigid=False,
                     shifts_opencv=True,
                     border_nan='copy',
                     nonneg_movie=True,
                     splits_rig=1,
                    splits_els=1)
    mc_params.update(**kwargs)
    if iref is None:
        iref = int(len(images)/2)
    mc = MotionCorrect([orig_file], **mc_params)
    mc.motion_correct(template=m_orig[iref])
    mc.pw_rigid=True
    mc.motion_correct(template=m_orig[iref])
    dview.terminate()
    return mc
        
def apply_pwrigid_transform(images, x_shifts, y_shifts, overlaps, strides):
    if len(images.shape) == 2:
        images = images.reshape((1, *images.shape))
    xy_grid = [(it[0], it[1]) for it in sliding_window(images[0], overlaps, strides)]
    dims_grid = tuple(np.max(np.stack(xy_grid, axis=1), axis=1) - 
                      np.min(np.stack(xy_grid, axis=1), axis=1) + 1)
    shiftX = np.reshape(x_shifts, dims_grid, order='C').astype(np.float32)
    shiftY = np.reshape(x_shifts, dims_grid, order='C').astype(np.float32)
    dims = images.shape[1:]
    x_grid, y_grid = np.meshgrid(np.arange(0., dims[1]).astype(np.float32), 
                                 np.arange(0., dims[0]).astype(np.float32))
    images_reg = np.stack([cv2.remap(img, -cv2.resize(shiftY, dims[::-1]) + x_grid,
                       -cv2.resize(shiftX, dims[::-1]) + y_grid,
                       cv2.INTER_CUBIC, borderMode=0) #borderMode=cv2.BORDER_REPLICATE
             for img in images], axis=0)
    images_reg[images_reg<0] = 0
    return images_reg