#! usr/bin/python

import os, glob

import numpy as np
import scipy.stats

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from mouse_imaging.session import chan_dict, load_hyperstack
from suite2p.io.tiff import imread, save_tiff

def demix_channel(hyperstack, demix_chan, donor_chan, donor_max=None, ret_hyperstack=True, scatter=False, s=3, xlim=None, ylim=None, nbins=20, x_lower_frac=0.5, binwise_percentile=50):
    if type(demix_chan) is not int:
        demix_ichan = chan_dict[demix_chan]
    else:
        demix_ichan = demix_chan
    if type(donor_chan) is not int:
        donor_ichan = chan_dict[donor_chan]
    else:
        donor_ichan = donor_chan
    donor_stack = hyperstack[:, donor_ichan]
    mixed_stack = hyperstack[:, demix_ichan]
    demixed_stack = np.zeros_like(mixed_stack)

    def select_pixels_to_regress(x, y, nbins=20, x_lower_frac=0.5, binwise_percentile=50):
        bins = np.linspace(x.max() * x_lower_frac, x.max(), nbins)
        digitized = np.digitize(x, bins)
        x_regress = []
        y_regress = []
        for ibin in np.unique(digitized)[1:]:
            xi = x[digitized == ibin]
            yi = y[digitized == ibin]
            if binwise_percentile is not None:
                idx = yi <= np.percentile(yi, binwise_percentile)
                yi = yi[idx]
                xi = xi[idx]
            x_regress.append(xi)
            y_regress.append(yi)
        x_regress = np.concatenate(x_regress, axis=0)
        y_regress = np.concatenate(y_regress, axis=0)
        # print(len(x_regress))
        # Add origin
        x_regress = np.concatenate([np.repeat(0, int(len(x_regress)*0.2)), x_regress])
        y_regress = np.concatenate([np.repeat(0, int(len(y_regress)*0.2)), y_regress])
        return x_regress, y_regress

    slope = np.zeros(len(mixed_stack))
    slope[:] = np.nan
    intercept = np.zeros(len(mixed_stack))
    intercept[:] = np.nan
    for islice in range(len(mixed_stack)):
        donor_pixels = donor_stack[islice].flatten()
        demix_pixels = mixed_stack[islice].flatten()

        if donor_max:
            # Some recordings have values that increase nonlinearly after a certain point
            cutoff_idx = donor_pixels < donor_max
            donor_pixels = donor_pixels[cutoff_idx]
            demix_pixels = demix_pixels[cutoff_idx]

        x_regress, y_regress = select_pixels_to_regress(donor_pixels, demix_pixels, nbins=nbins, x_lower_frac=x_lower_frac, binwise_percentile=binwise_percentile)
        
        slopei, intercepti, rvalue, pvalue, stderr = scipy.stats.linregress(x_regress, y_regress)
        intercepti = 0
        slope[islice] = slopei
        intercept[islice] = intercepti

        # Demix
        demixed_stack[islice] = mixed_stack[islice] - (donor_stack[islice] * slopei + intercepti)

    if scatter:
        nslices = len(hyperstack)
        plt.figure(figsize=(5*nslices, nslices))
        gs = gridspec.GridSpec(ncols=nslices, nrows=1)
        for plane in range(1, nslices+1):
            ax = plt.subplot(gs[0, plane-1])
            ax.set_title(f'slice {plane}')
            plt.scatter(donor_stack[plane-1].flatten(), mixed_stack[plane-1].flatten(), s=s)
            x = np.arange(0, donor_stack[plane-1].max())
            y = x * slope[plane-1] + intercept[plane-1]
            plt.plot(x, y, color='red')
            plt.xlabel(donor_chan)
            plt.ylabel(demix_chan)
            if xlim: plt.xlim(xlim)
            if ylim: plt.ylim(ylim)

    if ret_hyperstack:
        hyperstack = hyperstack.copy()
        hyperstack[:, demix_ichan] = demixed_stack
        return hyperstack
    else:
        return demixed_stack

def imshow_channel_demixing(self, demix_chan, donor_chan, filter_id=None, plane=1, crop=slice(None), vmax_donor=None, vmax_demix=None):
    donor_stack = self.img[filter_id][:, chan_dict[donor_chan]]
    mixed_stack = self.img[filter_id][:, chan_dict[demix_chan]]        
    demixed_stack = demix_channel(self.img[filter_id], demix_chan, donor_chan, ret_hyperstack=True)[:, chan_dict[demix_chan]]
    print(mixed_stack.shape)
    print(demixed_stack.shape)

    fig = plt.figure(figsize=(30, 10))
    gs = gridspec.GridSpec(ncols=3, nrows=1, figure=fig)
    for iax, (chan, vmax) in enumerate(zip([donor_chan, demix_chan], [vmax_donor, vmax_demix])):
        ax = fig.add_subplot(gs[0, iax])
        img = self.get_img(chan, plane=plane, filter_key=filter_id)[crop]
        plt.imshow(img, vmax=vmax)
        plt.colorbar(ax=ax, shrink=0.5)
        ax.set_title(chan)

    ax3 = fig.add_subplot(gs[0, 2])
    img = demixed_stack[plane-1][crop]
    plt.imshow(img, vmax=vmax_demix)
    plt.colorbar(ax=ax3, shrink=0.5)
    ax3.set_title(demix_chan + ' demixed')

def main(tif_dir, demix_chan, donor_chan, filename='*.tiff'):
    tif_dir = tif_dir.rstrip(os.path.sep)
    files_raw = sorted(glob.glob(os.path.join(tif_dir, filename)))
    files_demixed = ['.'.join(file_raw.split('.')[:-1]) + '_demixed.tiff' for file_raw in files_raw]
    hyperstack_raw = load_hyperstack(files_raw)
    # donor_max = None if metadata['date'] > '200912' else 4000
    hyperstack_demixed = demix_channel(hyperstack_raw, demix_chan, donor_chan, donor_max=None)
    os.makedirs(os.path.dirname(files_demixed[0]), exist_ok=True)
    for iplane in range(len(hyperstack_demixed)):
        img = np.moveaxis(hyperstack_demixed[iplane], 0, -1)
        save_tiff(img, files_demixed[iplane])

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Demix signal contamination between channels.')
    parser.add_argument('--tif_dir', required=True)
    parser.add_argument('--demix_chan', required=True)
    parser.add_argument('--donor_chan', required=True)
    parser.add_argument('--filename', default='*.tiff', required=False)
    args = parser.parse_args()
    
    main(**vars(args))
