import numpy as np
import pandas as pd
import scipy.stats
import tempfile
import os, json, copy, time

# import caiman as cm
# from caiman.motion_correction import MotionCorrect, sliding_window
from normcorre import compute_pwrigid_transform, apply_pwrigid_transform
import cv2
from tifffile import imread

import anndata
from mouse_imaging.session import define_path, get_metadata, maze_id, adata_to_key, mousedates_to_keys, unpack_var_name
from functions import save_pickle, load_pickle, crop_img
import functions as fc

from scipy.ndimage.morphology import binary_dilation
from scipy.ndimage import gaussian_filter

import matplotlib.pyplot as plt
import matplotlib as mpl

# Compile data
def load_meanRefs(keys, iplane=0, filter_id='filter1', ichannel=1):
    arr2ds = []
    for key in keys:
        path = define_path(**key)
        img = imread(path['meanRef'][filter_id][iplane])[:, :, ichannel]
        arr2ds.append(img)
    arr3d = np.stack(arr2ds)
    return arr3d

def source_images(key, iplane, filter_id='filter1', ichannel=1, smooth_pix=0):
    path = define_path(**key)
    metadata = get_metadata(path)
    img = imread(path['meanRef'][filter_id][iplane])[:, :, ichannel]
    stat = np.load(path['stat_npy'].format(plane=iplane+1), allow_pickle=True)
    source_imgs = np.zeros((len(stat), metadata['Ly'], metadata['Lx']))
    if smooth_pix: mask0 = np.zeros((metadata['Ly'], metadata['Lx']))
    for i, stati in enumerate(stat):
        if smooth_pix:
            mask = mask0.copy()
            mask[stati['ypix'], stati['xpix']] = 1
            mask = binary_dilation(mask, iterations=smooth_pix).astype(float)
            mask = gaussian_filter(mask, smooth_pix)
            source_imgs[i] = img * mask
        else:
            source_imgs[i, stati['ypix'], stati['xpix']] = img[stati['ypix'], stati['xpix']]
    return source_imgs


# Check registration
def _center_of_mass(mask):
    yx = np.median(np.where(mask), axis=1)
    return yx

def center_of_mass(masks):
    yx = np.stack([_center_of_mass(mask) for mask in masks])
    return yx

def crop(img_stack, center, size=(50, 50)):
    if len(img_stack.shape) == 2:
        img_stack = np.expand_dims(img_stack, axis=0)
    assert len(img_stack.shape) == 3
    y, x = map(int, center)
    x_margin, y_margin = map(lambda x: int(x/2), size)
    Ly, Lx = img_stack[0].shape
    xmin = max(0, x-x_margin)
    xmax = min(Lx, x+x_margin)
    ymin = max(0, y-y_margin)
    ymax = min(Ly, y+y_margin)
    img_crop = img_stack[:, ymin:ymax, xmin:xmax]
    return img_crop

def _local_spatial_corr(ref_images, center, size=(50, 50)):
    assert len(ref_images) == 2
    img = crop(ref_images, center, size=size)
    corr, pvalue = scipy.stats.pearsonr(img[0].flatten(), img[1].flatten())
    return corr

def local_spatial_corr(ref_images, centers, size=(50, 50)):
    corr = np.array([_local_spatial_corr(ref_images, center, size=size) for center in centers])
    return corr

# Match sources
def match_source_to_ref(source, source_b, ref, ref_b, min_corr=0.7, ret_corr=False):
    if (source == 0).all() and not ret_corr:
        return np.nan
    ref = np.moveaxis(ref, 0, -1)
    ref_b = np.moveaxis(ref_b, 0, -1)
    center = list(map(np.mean, np.where(source)))

    crop = (60, 60)
    source_crop = fc.crop_img(source, center, crop=crop)
    source_b_crop = fc.crop_img(source_b, center, crop=crop)
    ref_crop = fc.crop_img(ref, center, crop=crop)
    ref_b_crop = fc.crop_img(ref_b, center, crop=crop)

    overlap = source_b_crop & np.moveaxis(ref_b_crop, -1, 0)
    if overlap.sum() == 0 and not ret_corr:
        return np.nan
    iref = np.argmax(overlap.sum(axis=(1, 2)))

    # Compute correlation
    corr = scipy.stats.pearsonr(source_crop.flatten(), ref_crop[:, :, iref].flatten())[0]
    if ret_corr:
        return corr
    else:
        if corr > min_corr:
            return iref
        else:
            return np.nan

def invert_mapping(map_, n):
    map_inv = [np.nan] * n
    for key, val in enumerate(map_):
        if not np.isnan(val):
            map_inv[int(val)] = key
    return map_inv

def match_sources_to_ref(sources, ref, min_corr=0.7, ret_corr=False, keep_source='mean'):
    # Precompute binary sources
    ref_b = ref > 0
    sources_b = sources > 0

    # Compute source-to-ref mapping
    src_to_ref = [match_source_to_ref(source, source_b, ref, ref_b, min_corr=min_corr, ret_corr=ret_corr)
                 for source, source_b in zip(sources, sources_b)]

    # Invert source-to-ref mapping
    ref_to_src = invert_mapping(src_to_ref, len(ref))
    
    # Add unmapped sources
    src_ids = range(len(sources))
    src_ids_unmapped = list(set(src_ids) - set(ref_to_src))
    mapping = pd.Series(ref_to_src+src_ids_unmapped)

    # Replace source images
    ref_new = ref.copy()
    ref_to_src = np.array(ref_to_src)
    if keep_source == 'first':
        # Do not replace
        pass
    elif keep_source == 'last':
        # mapped_inds = np.where(np.isnan(ref_to_src) == False)[0]
        mapped_inds = (np.isnan(ref_to_src) == False)
        ref_new[mapped_inds] = sources[ref_to_src[mapped_inds].astype(int)]
    elif keep_source == 'mean':
        # Weighs older sources exponentially lower
        mapped_inds = np.where(np.isnan(ref_to_src) == False)[0]
        sources_mapped_new = sources[ref_to_src[mapped_inds].astype(int)]
        sources_mapped_old = ref[mapped_inds]
        ref_new[mapped_inds] = np.stack([sources_mapped_old, sources_mapped_new]).mean(axis=0)
    else:
        raise ValueError('Argument keep_source must equal "first" , "last" or "mean".')
    
    # Append unmatched sources
    ref_new = np.concatenate([ref_new, sources[src_ids_unmapped]], axis=0)
    
    assert mapping.max() == len(sources)-1
    assert len(mapping) == len(ref_new)

    return mapping, ref_new

def match_sources(sources, min_corr=0.5, keep_source='mean'):
    keys = list(sources.keys())
    df = pd.DataFrame()

    # Initialize reference with first session
    ref = sources[keys[0]]
    df[keys[0]] = range(len(ref))

    # Recursively build reference by matching to each session
    for key in keys[1:]:
        print(f'Matching sources from {key}.')
        sr, ref = match_sources_to_ref(sources[key], ref, min_corr=min_corr, keep_source=keep_source)
        df = pd.concat([df, sr.rename(key)], axis=1)

    return df

def label_sources(df, plane):
    prefix = f'plane{plane}_source'
    def to_cell_index(sr):
        return sr.apply(lambda x: np.nan if np.isnan(x) else f'{prefix}{int(x)}')
    df = df.apply(to_cell_index)
    df.index = f'plane{plane}_usource' + df.index.astype(str)
    return df

# Merge sessions
def match_var_names(adata, sourcemap):
    key = adata_to_key(adata)
    date = adata.uns['metadata']['date']
    # ref_to_adata = sourcemap[str(key)].dropna()
    ref_to_adata = sourcemap[str(key)].dropna()
    adata_to_ref = pd.Series(ref_to_adata.index.values, index=ref_to_adata)
    var_names = adata.var_names.map(adata_to_ref)
    return var_names

def mean_vars_col(adatas, col):
    df = pd.DataFrame()
    for i, adata in enumerate(adatas):
        df = pd.concat([df, adata.var[col]], axis=1)
    
    sr = df.astype(float).mean(axis=1, skipna=True)
    return sr

def mean_vars(adatas, var_names, columns):
    var = pd.DataFrame(index=var_names)
    for col in columns:
        var[col] = mean_vars_col(adatas, col)
    return var

def concat_sessions(adatas, sourcemap):
    # Assert all from same region
    regions = [adata.uns['metadata']['region'] for adata in adatas]
    assert len(set(regions)) == 1

    # Match var_names
    adatas = adatas.copy()
    for adata in adatas:
        adata.var_names = match_var_names(adata, sourcemap)
    
    # Concatenate along obs axis, append session id to obs
    sessions = [f"{adata.uns['metadata']['date']}_{adata.uns['metadata']['session']}" for adata in adatas]
    adata_m = anndata.concat(adatas, join='outer', axis=0, keys=sessions, label='session', fill_value=np.nan, merge=None)
    adata_m.obs_names_make_unique()  
    
    # Append maze to obs
    mazes = [maze_id(adata.uns['path']) for adata in adatas]    
    for session, maze in zip(sessions, mazes):
        adata_m.obs.loc[adata_m.obs.session==session, 'maze'] = maze
    
    # Take mean of vars, excluding UMAP projection
    columns = [col for col in adatas[0].var.columns if not col.startswith('Xumap')]
    adata_m.var = mean_vars(adatas, adata_m.var_names, columns)
    
    return adata_m

# Plot source images for quality control
def load_stat(key, plane=1):
    path = define_path(**key)
    stat = np.load(path['stat_npy'].format(plane=plane), allow_pickle=True)
    return stat

def load_stats(keys, plane=1):
    stats = [load_stat(key, plane=plane) for key in keys]
    return stats

def stat2img(stati, Ly=512, Lx=512):
    img = np.zeros((Ly, Lx))
    img[stati['ypix'], stati['xpix']] = stati['lam']
    return img
    
def stat2border(stati, **kwargs):
    img = stat2img(stati, **kwargs) > 0
    border = scipy.ndimage.morphology.binary_dilation(img, iterations=1)
    border[img] = False
    return border

def crop_slice(stati, crop=(100, 100)):
    y_margin, x_margin = map(int, np.array(crop)/2)
    y_center, x_center = map(int, stati['med'])
    y_slice = slice(y_center-y_margin, y_center+y_margin)
    x_slice = slice(x_center-x_margin, x_center+x_margin)
    return y_slice, x_slice

def crop(img, stati, crop=(100, 100)):
    y_slice, x_slice = crop_slice(stati, crop=crop)
    return img[y_slice, x_slice]

def add_border(img, border):
    img = img.copy()
    img[border] = img.max()
    return img

def plot_registered_sources(mouse, dates, sourcemap_i, filter_id='filter1', ichannel=1, vmax=99.5):
    path = define_path(mouse=mouse, date=dates[0])
    md = get_metadata(path)
    planes = range(1, md['nslices']+1)
    keys = mousedates_to_keys(mouse, dates)
    stats = {plane: {date: stat for date, stat in zip(dates, load_stats(keys, plane=plane))} for plane in planes}
    imgs = {plane: {date: img for date, img in zip(dates, load_meanRefs(keys, iplane=plane-1, filter_id=filter_id, ichannel=ichannel))} for plane in planes}

    plt.figure(figsize=(3*len(dates), 3))
    gs = mpl.gridspec.GridSpec(nrows=1, ncols=len(dates))

    for idate, (key_str, source_id) in enumerate(zip(sourcemap_i.index, sourcemap_i)):
        ax = plt.subplot(gs[0, idate]) 
        if type(source_id) is str:
            plane, isource = unpack_var_name(source_id)
            key = str_to_key(key_str)
            date = key['date']
            img = imgs[plane][date].copy()
            stati = stats[plane][date][isource]
            img = add_border(img, stat2border(stati))
            img_cropped = crop(img, stati['med'])

            if len(img_cropped.flatten()):
                vmax_abs = np.percentile(img_cropped.flatten(), vmax)
                ax.imshow(img_cropped, vmax=vmax_abs)
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)
                footprint = stati['footprint']
                compact = stati['compact']
                ax.set_title(f'{date}\n{source_id}\nfootprint: {footprint}\ncompact: {compact}')
        else:
            ax.axis('off')
            ax.set_title(f'{date}\nno match')

# Check local alignment for each cell
def _center_of_mass(mask):
    yx = np.median(np.where(mask), axis=1)
    return yx

def center_of_mass(masks):
    yx = np.stack([_center_of_mass(mask) for mask in masks])
    return yx

def crop(img_stack, center, size=(50, 50)):
    y, x = map(int, center)
    x_margin, y_margin = map(lambda x: int(x/2), size)
    Ly, Lx = img_stack.shape[-2:]
    xmin = max(0, x-x_margin)
    xmax = min(Lx, x+x_margin)
    ymin = max(0, y-y_margin)
    ymax = min(Ly, y+y_margin)
    if len(img_stack.shape) == 3:
        img_crop = img_stack[:, ymin:ymax, xmin:xmax]
    else:
        img_crop = img_stack[ymin:ymax, xmin:xmax]
    return img_crop

def _local_spatial_corr1(ref_images, center, size=(50, 50)):
    if np.isnan(center).any():
        return np.nan
    assert len(ref_images) == 2
    img = crop(ref_images, center, size=size)
    corr, pvalue = scipy.stats.pearsonr(img[0].flatten(), img[1].flatten())
    return corr

def _local_spatial_corr(ref_images, centers, size=(50, 50)):
    corr = np.array([_local_spatial_corr1(ref_images, center, size=size) for center in centers])
    return corr
    
def local_spatial_corr(sourcemap, isessions, size=(50, 50),):
    # Unpack metadata
    assert len(isessions) == 2
    mc = sourcemap.attrs['mc']
    ops = sourcemap.attrs['ops']
    
    # Compute registered sources and mean refs using ops that were used for sourcemap
    sources_reg = register_sources(ops['keys'], ops['plane'], mc, filter_id=ops['filter_id_source'], ichannel=ops['ichannel_source'])
    ref_images_reg = register_ref_images(ops['keys'], ops['plane'], mc, filter_id=ops['filter_id_ref'], ichannel=ops['ichannel_ref'])
    
    # For each cell in first session id, what is corr between first and second session mean refs
    yx = center_of_mass(list(sources_reg.values())[isessions[0]]>0)
    corr = _local_spatial_corr(ref_images_reg[isessions], yx)
    return corr


# Scripts
def filepath(keys, plane=None, min_corr=None, makedir=False):
    dates = [key['date'] for key in keys]
    path = define_path(**keys[0])
    metadata = get_metadata(path)

    mouse = keys[0]['mouse']
    filedir = os.path.join(path['preprocessed_root'], mouse, 'multisession_registration')
    if makedir:
        os.makedirs(filedir, exist_ok=True)

    if min_corr is None:
        mincorr_txt = ''
    else:
        mincorr_txt = f'_mincorr{min_corr}'
    filename = f'source_mapping_{mouse}_{metadata["region"]}_{"-".join(dates)}_mincorr{min_corr}' + '_plane{plane}.pickle'
    if plane is None:
        filename = filename.format(plane='').replace('_plane', '') 
    elif type(plane) is int:
        filename = filename.format(plane=plane)
        
    filepath = os.path.join(filedir, filename)
    return filepath

def str_to_key(key_str):
    return json.loads(key_str.replace("'", '"'))

def sourcemap_keys(sourcemap):
    keys = [str_to_key(key_str) for key_str in sourcemap.columns]
    return keys

def dates_to_keys(mouse, dates):
    keys = []
    for date in dates:
        if date[0] == '{':
            key = dict(mouse=mouse, **json.loads(date))
        else:
            key = dict(mouse=mouse, date=date, session='session_1')
        keys.append(key)
    return keys

def compute_transform(keys, plane, filter_id='filter1', ichannel=1):
    iplane = plane - 1
    # Load meanRefs
    print('Loading mean references...')
    ref_images = load_meanRefs(keys, iplane=iplane, filter_id=filter_id, ichannel=ichannel)

    # Compute transform for each day
    print('Computing piecewise rigid transform...')
    mc = compute_pwrigid_transform(ref_images, iref=int(len(keys)/2))
    return mc

def register_sources(keys, plane, mc, filter_id='filter1', ichannel=1,):
    iplane = plane - 1

    # Compile source images
    print('Compiling source images...')
    sources_orig = [source_images(key, iplane, filter_id=filter_id, ichannel=ichannel) for key in keys]

    # Apply transform
    print('Applying transform to source images...')
    sources_reg = {str(key): apply_pwrigid_transform(orig, mc.x_shifts_els[i], mc.y_shifts_els[i], mc.overlaps, mc.strides)
                  for i, (key, orig) in enumerate(zip(keys, sources_orig))}
    return sources_reg

def register_ref_images(keys, plane, mc, filter_id='filter1', ichannel=1):
    iplane = plane - 1

    # Compile ref images
    print('Compiling source images...')
    ref_images = load_meanRefs(keys, iplane=iplane, filter_id=filter_id, ichannel=ichannel)

    # Apply transform 
    print('Applying transform to source images...')
    ref_images_reg = np.concatenate([apply_pwrigid_transform(ref_image, mc.x_shifts_els[i], mc.y_shifts_els[i], mc.overlaps, mc.strides)
              for i, ref_image in enumerate(ref_images)])
    return ref_images_reg

def register_plane(keys, plane, filter_id_source='filter1', ichannel_source=1, filter_id_ref='filter1', ichannel_ref=1, min_corr=0.4, keep_source='last'):
    t0 = time.perf_counter()
    mouse = keys[0]['mouse']
    print(f'Processing {mouse} plane {plane}.')
    mc = compute_transform(keys, plane, filter_id=filter_id_ref, ichannel=ichannel_ref)
    sources_reg = register_sources(keys, plane, mc, filter_id=filter_id_source, ichannel=ichannel_source)

    # Match sources across days
    print('Matching sources across days...')
    sourcemap = match_sources(sources_reg, min_corr=min_corr, keep_source=keep_source)
    sourcemap = label_sources(sourcemap, plane)

    # Add metadata
    sourcemap.attrs['ops'] = dict(keys=keys, plane=plane, filter_id_source=filter_id_source, ichannel_source=ichannel_source, filter_id_ref=filter_id_ref, ichannel_ref=ichannel_ref, min_corr=min_corr, keep_source=keep_source)
    delattr(mc, 'dview')

    # Write mapping
    print('Saving source mapping...')
    sourcemap_file = filepath(keys, plane, min_corr=min_corr, makedir=True)
    save_pickle(sourcemap, sourcemap_file)
    t1 = time.perf_counter()
    print(f'Time to process plane {plane}: %i s' %(t1-t0))

    return sourcemap

def register_sessions(mouse, dates, min_corr=0.4, **kwargs):
    keys = dates_to_keys(mouse, dates)
    path = define_path(**keys[0])
    metadata = get_metadata(path)
    
    planes = range(1, metadata['nslices']+1)
    sourcemaps = []
    for plane in planes:
        sourcemap_planei = register_plane(keys, plane, min_corr=min_corr, **kwargs)
        sourcemaps.append(sourcemap_planei)
    sourcemap = pd.concat(sourcemaps, axis=0)
    sourcemap.attrs = sourcemap_planei.attrs
    
    # Write
    filename = filepath(keys, plane=None, min_corr=min_corr)
    fc.save_pickle(sourcemap, filename)

    return sourcemap

def concatenate_planes(keys, min_corr=0.7):
    path = define_path(**keys[0])
    metadata = get_metadata(path)

    sourcemap_concat = pd.concat([
        load_pickle(filepath(keys, plane=plane, min_corr=min_corr)) 
        for plane in range(1, metadata['nslices']+1)], axis=0)
    
    # Write
    filepath_concat = filepath(keys, plane=None, min_corr=min_corr)
    save_pickle(sourcemap_concat, filepath_concat)

    return sourcemap_concat

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Map sources across sessions.')
    parser.add_argument('--mouse', required=True, type=str)
    parser.add_argument('--dates', required=True, nargs='+')
    parser.add_argument('--filter_id_source', required=False, type=str, default='filter1')
    parser.add_argument('--filter_id_ref', required=False, type=str, default='filter1')
    parser.add_argument('--ichannel_source', required=False, type=int, default=1)
    parser.add_argument('--ichannel_ref', required=False, type=int, default=1)
    parser.add_argument('--min_corr', required=False, type=float, default=0.4)
    parser.add_argument('--keep_source', required=False, type=str, default='last')
    args = parser.parse_args()
    arg_dict = vars(args)
    print(arg_dict)
    register_sessions(**arg_dict)

