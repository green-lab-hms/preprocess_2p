#! usr/bin/python

import os, glob
import numpy as np
from tifffile import imread, imsave
from ScanImageTiffReader import ScanImageTiffReader
import mouse_imaging.session as sess

def session_raw_mean(mouse=None, date=None, session='session_1', save=True):
    # Filenames
    path = sess.define_path(mouse=mouse, date=date, session=session)
    tif_files = sorted(glob.glob(os.path.join(path['preprocessed_dir'], '2P', '*.tif')))
    
    # Import tif image data
    tif = np.concatenate([ScanImageTiffReader(tif_file).data() for tif_file in tif_files])
    
    # Import tif metadata
    md = sess.parse_si_metadata(ScanImageTiffReader(tif_files[0]).metadata())
    z = int(md['SI.hFastZ.numFramesPerVolume'])
    c = int(md['SI.hChannels.channelsAvailable'])
    x = int(md['SI.hRoiManager.pixelsPerLine'])
    y = int(md['SI.hRoiManager.linesPerFrame'])
    t = len(tif) / c / z
    assert t%1 == 0 # Assert integer number of volumes
    t = int(t)
    
    # Take mean across time
    mean = tif.reshape((c, z, t, x, y), order='F').mean(axis=2)
    
    if save:
        save_file = '_'.join(tif_files[0].split('_')[:-1]) + '_mean.tiff'
        print(f'Saving to {save_file}.')
        imsave(save_file, mean)
    
    return mean

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute mean over time of raw session images.')
    parser.add_argument('--mouse', required=True)
    parser.add_argument('--date', required=True)
    parser.add_argument('--session', required=False, default='session_1')
    parser.add_argument('--save', required=False, default=True)
    args = parser.parse_args()
    
    session_raw_mean(**vars(args))