# -*- coding: UTF-8 -*-
import os
import sys
import skimage.io
import skimage.transform
import time
import glob
import numpy as np
from natsort import natsorted
from mrcnn.config import Config
import mrcnn.model as modellib
from mrcnn import visualize
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Root directory of the project
ROOT_DIR = os.path.abspath("./")
sys.path.append(ROOT_DIR)  # To find local version of the library

# ● Directory to save logs and trained model
MODEL_DIR = os.path.join(ROOT_DIR, "logs_")

# ● Local path to trained weights file
NUM_MODEL_PATH = os.path.join(ROOT_DIR, "model", "mask_rcnn_num.h5")


class NUMConfig(Config):
    """Configuration for training on the NUM dataset.
    Derives from the base Config class and overrides values specific
    to the toy NUM dataset.
    """
    # Give the configuration a recognizable name
    NAME = "NUM"

    # Train on 1 GPU and 1 images per GPU. We can put multiple images on each
    # GPU because the images are small. Batch size is 1 (GPUs * images/GPU).
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

    # ● Number of classes (including background)
    NUM_CLASSES = 1 + 35  # background + myClass NUM

    # ● the same with training
    # Use small images for faster training. Set the limits of the small side
    # the large side, and that determines the image shape.
    # Image size must be dividable by 2 at least 6 times to avoid fractions
    # when downscaling and upscaling.For example, use 256, 320, 384, 448, 512, ... etc.
    IMAGE_MIN_DIM = 512  # 768  # 640  # 512
    IMAGE_MAX_DIM = 512  # 768  # 640  # 512
    # scale_max = 1024 // IMAGE_MAX_DIM
    # scale_min = 1024 // IMAGE_MIN_DIM

    # Use smaller anchors because our image and objects are small
    # RPN_ANCHOR_SCALES = (32 // scale_max, 64 // scale_max, 128 // scale_max, 256 // scale_max, 512 // scale_max)
    RPN_ANCHOR_SCALES = (8 * 6, 16 * 6, 32 * 6, 64 * 6, 128 * 6)  # anchor side in pixels


class NUMMrcnn:
    """Mask-RCNN to detect NUM in receipt image.
    Based on the model which has been trained.
    Attributes:
        config: Configuration for training on the NUM dataset.
        self.model: Model object in inference mode.
        self.model.load_weights: Weights trained on MS-COCO.
        self.model.keras_model._make_predict_function()
    """

    def __init__(self):
        self.config = NUMConfig()

        # Create model object in inference mode.
        self.model = modellib.MaskRCNN(mode="inference", model_dir=MODEL_DIR, config=self.config)

        # Load weights trained on MS-COCO
        self.model.load_weights(NUM_MODEL_PATH, by_name=True)

        # keep model loaded while running detection in a web service
        # https://github.com/matterport/Mask_RCNN/issues/600
        self.model.keras_model._make_predict_function()

    def test_image(self, img, filename):
        """Use Mask-RCNN to detect NUM in the image.
        Use model.detect functio.
        Args:= skimage.
            img: The image of Receipt.
            filename: The image name.
        Returns:
            list: The scores of each NUM. Set to [0] if NUM is not found.
        """
        # image = skimage.io.imread(img)
        # image = skimage.transform.rescale(image, 0.5, 3)
        # image = skimage.transform.resize(image, (1024, 1024, 3))
        image = img

        # Run detection
        results = self.model.detect([image], verbose=1)
        r = results[0]

        # For show: Visualize results
        # COCO Class names: Index of the class in the list is its ID.
        class_names = ['BG', '.', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                       '-', '%', '才', '基礎代謝量', '筋肉量', '男性', '女性', '内蔵脂肪', '体内年齢',
                       '体脂肪率', '生年月日', '体重', 'BMI', '年', 'cm', 'kcal/日', 'kg', 'レベル',
                       '体年齢', '皮下脂肪率', '骨格筋率', "基礎代謝", "kcal", "内蔵脂肪レベル"]
        # visualize.display_instances(image, filename, r['rois'], r['masks'], r['class_ids'], class_names, r['scores'])

        # TODO: return the list of numbers
        if r['class_ids'].size:
            centerdict = np.array([])
            for value in results[0]['rois']:
                (y1, x1, y2, x2) = value
                (rectcenter_x, rectcenter_y) = ((x1 + x2) / 2, (y1 + y2) / 2)
                centerdict = np.append(centerdict, [rectcenter_x])
            tmp_sort = np.argsort(centerdict)

            class_list_1 = []
            class_list_2 = []
            class_list_3 = []
            for x in tmp_sort:
                class_name_result = class_names[r['class_ids'][x]]
                if class_name_result.isdigit() or class_name_result in [".", '-']:
                    class_list_2.append(class_name_result)
                elif class_name_result in ['%', '才', '年', 'cm', 'kcal/日', 'kg', 'レベル', "kcal"]:
                    class_list_3.append(class_name_result)
                else:
                    class_list_1.append(class_name_result)
            return class_list_1 + class_list_2 + class_list_3
        else:
            return []


if __name__ == '__main__':
    # test
    test_directory = os.path.join(ROOT_DIR, '_test_images')
    result_directory = os.path.join(ROOT_DIR, '_test_result')
    mask_rcnn = NUMMrcnn()
    list_of_files = sorted(glob.glob(os.path.join(test_directory, '*.jpg')))

    test_start = time.time()
    print("***** The start time:", test_start)
    # for file in list_of_files:
    for file in natsorted(list_of_files):
        print("\nImage name:", file)
        label_list = mask_rcnn.test_image(file, file)
        print("Label_list:", label_list)
    test_end = time.time()
    print("***** The end time:", test_end)
    print("***** The testing Time for every image:.%s Seconds" % ((test_end - test_start)/len(list_of_files)))
