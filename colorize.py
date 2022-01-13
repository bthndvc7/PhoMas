
import argparse
import matplotlib.pyplot as plt
import os

from colorizers import *


class Colorizer:

	def __init__(self, username, filename):
		self.filename = filename
		self.username = username

	def colorize(self):
		parser = argparse.ArgumentParser()
		parser.add_argument('-i', '--img_path', type=str, default=f'static/uploaded_imgs/{self.username}/{self.filename}')
		parser.add_argument('--use_gpu', action='store_true', help='whether to use GPU')
		parser.add_argument('-o', '--save_prefix', type=str, default='colorized',
							help='will save into this file with {siggraph17.png} suffixes')
		opt = parser.parse_args()

		# load colorizer
		colorizer_siggraph17 = siggraph17(pretrained=True).eval()
		if opt.use_gpu:
			colorizer_siggraph17.cuda()

		# default size to process images is 256x256
		# grab L channel in both original ("orig") and resized ("rs") resolutions
		img = load_img(opt.img_path)
		(tens_l_orig, tens_l_rs) = preprocess_img(img, HW=(256, 256))
		if opt.use_gpu:
			tens_l_rs = tens_l_rs.cuda()

		# colorizer outputs 256x256 ab map
		# resize and concatenate to original L channel
		out_img_siggraph17 = postprocess_tens(tens_l_orig, colorizer_siggraph17(tens_l_rs).cpu())
		user_folder = os.path.join(f'static/imgs_out/', self.username)
		if not os.path.exists(user_folder):
			os.mkdir(user_folder)
		plt.imsave(f'static/imgs_out/{self.username}/%s_{self.filename}' % opt.save_prefix, out_img_siggraph17)
		return

