import datetime
import os
import shutil
import time
from natsort import natsorted

import numpy as np
from scipy.io import savemat

from suite2p import io
from suite2p.extraction.extract import extract_traces

def check_if_binaries_exist(ops):
    if 'save_path0' not in ops or len(ops['save_path0'])==0:
    if ('h5py' in ops) and len(ops['h5py'])>0:
        ops['save_path0'], tail = os.path.split(ops['h5py'])
    else:
        ops['save_path0'] = ops['data_path'][0]
    
    # check if there are binaries already made
    if 'save_folder' not in ops or len(ops['save_folder'])==0:
        ops['save_folder'] = 'suite2p'
    save_folder = os.path.join(ops['save_path0'], ops['save_folder'])
    os.makedirs(save_folder, exist_ok=True)
    fpathops1 = os.path.join(save_folder, 'ops1.npy')
    plane_folders = natsorted([ f.path for f in os.scandir(save_folder) if f.is_dir() and f.name[:5]=='plane'])
    if len(plane_folders) > 0:
        ops_paths = [os.path.join(f, 'ops.npy') for f in plane_folders]
        ops_found_flag = all([os.path.isfile(ops_path) for ops_path in ops_paths])
        binaries_found_flag = all([os.path.isfile(os.path.join(f, 'data_raw.bin')) or os.path.isfile(os.path.join(f, 'data.bin')) 
                                    for f in plane_folders])
        files_found_flag = ops_found_flag and binaries_found_flag
        print(f'FOUND BINARIES AND OPS IN {ops_paths}')
    else:
        files_found_flag = False
    return files_found_flag

def run_s2p_extraction(ops={}, db={}):
    """ run suite2p pipeline

        need to provide a 'data_path' or 'h5py'+'h5py_key' in db or ops

        Parameters
        ----------
        ops : :obj:`dict`, optional
            specify 'nplanes', 'nchannels', 'tau', 'fs'
        db : :obj:`dict`, optional
            specify 'data_path' or 'h5py'+'h5py_key' here or in ops

        Returns
        -------
            ops1 : list
                list of ops for each plane

    """
    t0 = time.time()
    ops = {**default_ops(), **ops, **db}
    # files_found_flag = check_if_binaries_exist(ops)
    print(db)
    ops1 = io.tiff_to_binary(ops.copy())
    print('time {:4.2f} sec. Wrote {} tiff frames to binaries for {} planes'.format(
          time.time() - t0, ops1[0]['nframes'], len(ops1)))
    F, Fneu, ops1 = extract_traces(ops1, cell_masks, neuropil_masks, ops1[0]['reg_file'])
    print('Plane %d processed in %0.2f sec (can open in GUI).'%(ipl,time.time()-t1))

    np.save(os.path.join(ops['save_folder'], 'F.npy'), F)
    np.save(os.path.join(ops['save_folder'], 'F_neu.npy'), F_neu)
    np.save(os.path.join(ops['save_folder'], 'ops.npy'), ops1)

    print('TOTAL RUNTIME %0.2f sec' % (time.time()-t0))
    return ops1


