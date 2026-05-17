#! usr/bin/python

import suite2p
import numpy as np
import glob, os, pickle
from ScanImageTiffReader import ScanImageTiffReader
from mouse_imaging.session import define_path, get_metadata, chan_dict
import mouse_imaging.options as options
import scipy.io
import subprocess
import pandas as pd
from scipy import sparse

import importlib
importlib.reload(suite2p)

def define_ops(path, metadata, plane=0, makedir=True, ops=None):
    if ops is None:
        ops = suite2p.default_ops()
    
    ops['fast_disk'] = path['corrected_dir']
    ops['save_folder'] = os.path.join(path['preprocessed_dir'], f'slice_{plane}')
    if makedir:
        os.makedirs(ops['save_folder'], exist_ok=True)

    ops['fs'] = metadata['SI.hRoiManager.scanVolumeRate'] # volumetric frame rate
    ops['spatial_scale'] = ops['spatial_scale_factor'] * metadata['SI.hRoiManager.scanZoomFactor']
    print(f"spatial_scale: {ops['spatial_scale']}")

    return ops

def define_db(path, functional_channel_num, plane=0):
    regex = f'*_Slice0{plane}_Channel0{functional_channel_num}_*.tif'
    tiff_files = sorted([os.path.basename(f) for f in glob.glob(os.path.join(path['corrected_dir'], regex))])

    db = {'data_path': [path['corrected_dir']], 
          'tiff_list': tiff_files
        }
    return db

def save_pickle(obj, filename):
    with open(filename, 'wb') as fh:
        pickle.dump(obj, fh)

def background_neuropil_mask(dim, stat):
    mask = np.ones(dim).astype(bool)
    for stati in stat:
        mask[stati['ypix'], stati['xpix']] = False
    return mask
    
def _mask(path, metadata, mask_fcn, plane):
    Ly = int(metadata['SI.hRoiManager.linesPerFrame'])
    Lx = int(metadata['SI.hRoiManager.pixelsPerLine'])
    stat = np.load(path['stat_npy'].format(plane=plane), allow_pickle=True)
    mask = mask_fcn((Ly, Lx), stat)
    return mask

def _extract_F_slicei(filelist, mask, length):
    result = np.zeros((1, length))
    result[:] = np.nan
    i = 0
    for filei in filelist:
        tiff_stack = ScanImageTiffReader(filei)
        for tiff in tiff_stack.data():
            result[0, i] = tiff[mask].mean()
            i += 1
    return result

def save_F(mask, filename, opsEnd):
    F = _extract_F_slicei(opsEnd['filelist'], mask, length=opsEnd['nframes'])
    np.save(filename, F)

def suite2p_to_source_images(path, plane, functional_channel='G'):
    functional_channel_num = chan_dict[functional_channel]
    metadata = get_metadata(path)
    primary_tif = path['meanRef']['filter1'][plane-1]
    ops = np.load(path['ops_npy'].format(plane=plane), allow_pickle=True).item()
    Ly, Lx = ops['Ly'], ops['Lx']
    stat = np.load(path['stat_npy'].format(plane=plane), allow_pickle=True)

    sources = np.zeros((Ly*Lx, len(stat))).astype(np.float64)
    img_planei = suite2p.io.tiff.imread(primary_tif)[:, :, functional_channel_num]
    for istat, stati in enumerate(stat):
        maski = np.zeros((Ly, Lx)).astype(np.float64)
        maski[stati['ypix'], stati['xpix']] = img_planei[stati['ypix'], stati['xpix']]
        sources[:, istat] = maski.flatten()
    return sources

def classify_sources_convnet(path, plane, functional_chan):
    io = dict(source_images_mat=path['source_images_mat'].format(plane=plane),
                 convnet_labels_csv=path['convnet_labels_csv'].format(plane=plane),
                 convnet_mat=path['convnet_mat'],
                 iscell_convnet_npy=path['iscell_convnet_npy'].format(plane=plane))
    
    # Export suite2p sources to images in mat file
    sources = suite2p_to_source_images(path, plane=plane, functional_channel = functional_chan)
    nonzero = (sources.sum(axis=0) > 0)
    mdict = {'A': sparse.csr_matrix(sources[:, nonzero])}
    scipy.io.savemat(io['source_images_mat'], mdict)
    
    # Run source classifier in matlab, export labels to csv
    shell_script = """
    module load matlab/2020a
    export MATLABPATH=$CODE/source_classifier_syt
    matlab -batch "runSourceClassifier('{source_images_mat}', '{convnet_labels_csv}', '{convnet_mat}')"
    rm {source_images_mat}
    """.format(**io)
    out = subprocess.call(shell_script, shell=True)
    
    # Import labels
    labels = np.ones(sources.shape[1]) * 4 # label for 'garbage'
    labels[nonzero] = np.array(pd.read_csv(io['convnet_labels_csv'], header=None)[0])
    iscell_convnet = labels == 1
    np.save(io['iscell_convnet_npy'], iscell_convnet)
    
    return labels
  
def main(session_dir, ops='default_ops'):
    path = define_path(session_dir=session_dir, makedir=True)
    metadata = get_metadata(path)
    suite2p_ops = getattr(options, ops)()['suite2p_ops']
    
    functional_chan = getattr(options, ops)()['functional_chan']
    functional_channel_num = metadata['filter1']['channels'].index(functional_chan) + 1
    
    n_planes = int(metadata['nslices'])
    for plane in range(1, n_planes+1):
        db = define_db(path, functional_channel_num, plane)
        ops = define_ops(path, metadata, plane=plane, makedir=True, ops=suite2p_ops)
        opsEnd = suite2p.run_s2p(ops=ops, db=db)

        opsout = np.load(path['ops_npy'].format(plane=plane), allow_pickle=True).item()
        # mask_bkg = _mask(path, metadata, background_neuropil_mask, plane)
        # save_F(mask_bkg, path['Fbkg_npy'].format(plane=plane), opsout)
        classify_sources_convnet(path, plane, functional_chan)

    save_pickle(path, path['path_pickle'])
    save_pickle(metadata, path['metadata_pickle'])

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run Suite2P on motion-corrected data.')
    parser.add_argument('session_dir')
    parser.add_argument('ops')
    args = parser.parse_args()
    print(args.session_dir)
    main(**vars(args))

