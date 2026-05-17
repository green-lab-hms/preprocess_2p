import mouse_imaging.session  as sess
import mouse_imaging.options  as options
from preprocess_2p.register_sessions import compute_pwrigid_transform, apply_pwrigid_transform
import numpy as np
from tifffile import imread, imsave

def register_meanref(image, source, target, ref_ichannel):
    assert source.shape[-1] == target.shape[-1]

    sourcetarget = np.stack([target[:, :, ref_ichannel], source[:, :, ref_ichannel]])
    mc = compute_pwrigid_transform(sourcetarget, iref=0)
    
    image_reg = np.concatenate([apply_pwrigid_transform(image[:, :, i], mc.x_shifts_els[1], mc.y_shifts_els[1], mc.overlaps, mc.strides) for i in range(image.shape[2])], axis=0)
    image_reg = np.moveaxis(image_reg, 0, -1)
    
    return image_reg
    
def register_meanrefs(path, params, ref_ichannel=0):
    nplanes = len(path['meanRef']['filter1'])
    for iplane in range(nplanes):
        image = imread(path['meanRef'][params['image']][iplane])
        source = imread(path['meanRef'][params['source']][iplane])
        target = imread(path['meanRef'][params['target']][iplane])
        image_reg = register_meanref(image, source, target, ref_ichannel=ref_ichannel)
        fileout = path['meanRef'][params['image']][iplane].split('.tif')[0] + '_reg.tiff'
        imsave(fileout, image_reg)

def main(mouse, date, image, source, target, ref_ichannel, session='session_1', ops=options.default_ops()):
	path = sess.define_path(mouse=mouse, date=date, session=session, ops=ops)
	params = dict(image=image, source=source, target=target)
	register_meanrefs(path, params=params, ref_ichannel=ref_ichannel)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Register reference images to main session.')
    parser.add_argument('--mouse', required=True, type=str)
    parser.add_argument('--date', required=True, type=str)
    parser.add_argument('--session', required=False, type=str, default='session_1')
    parser.add_argument('--ops', required=False, type=str, default='default_ops')
    parser.add_argument('--image', required=True, type=str)
    parser.add_argument('--source', required=True, type=str)
    parser.add_argument('--target', required=True, type=str)
    parser.add_argument('--ref_ichannel', required=True, type=int)
    args = parser.parse_args()
    args.ops = getattr(options, args.ops)()
    main(**vars(args))
