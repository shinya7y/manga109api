import os
import pickle
import argparse

import manga109api
from PIL import Image, ImageDraw


def draw_rectangle(img, x0, y0, x1, y1, annotation_type, width=5, outside=True):
    assert annotation_type in ["body", "face", "frame", "text"]
    color_dict = {"body": "#258039", "face": "#f5be41", "frame": "#31a9b8", "text": "#802214"}
    color = color_dict[annotation_type]
    if outside:
        x0 -= width
        y0 -= width
        x1 += width
        y1 += width

    draw = ImageDraw.Draw(img)
    draw.rectangle([x0, y0, x1, y1], outline=color, width=width)


def parse_args():
    default_test = [
        "Akuhamu", "BakuretsuKungFuGirl", "DollGun", "EvaLady", "HinagikuKenzan", "KyokugenCyclone", "LoveHina_vol01",
        "MomoyamaHaikagura", "TennenSenshiG", "UchiNoNyan'sDiary", "UnbalanceTokyo", "YamatoNoHane", "YoumaKourin",
        "YumeNoKayoiji", "YumeiroCooking"
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument('--manga109_root_dir', required=True, type=str)
    parser.add_argument('--predictions_pkl', default=None, type=str)
    parser.add_argument('--vis_dir', default=None, type=str)
    parser.add_argument('--vis_books', nargs='+', default=default_test, type=str)
    parser.add_argument('--vis_score_thr1', default=0.5, type=float)
    parser.add_argument('--vis_score_thr2', default=0.3, type=float)
    parser.add_argument('--rect_width1', default=7, type=int)
    parser.add_argument('--rect_width2', default=3, type=int)
    parser.add_argument('--draw_truth', action='store_true')

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    vis_dir = args.manga109_root_dir + "_vis_bbox" if args.vis_dir is None else args.vis_dir

    if args.predictions_pkl:
        with open(args.predictions_pkl, 'rb') as f:
            predictions = pickle.load(f)
        print(len(predictions))
    else:
        predictions = None

    prediction_index = 0
    p = manga109api.Parser(root_dir=args.manga109_root_dir)
    for book in args.vis_books:
        print('processing', book)
        vis_book_dir = os.path.join(vis_dir, book)
        os.makedirs(vis_book_dir, exist_ok=True)

        annotation = p.get_annotation(book=book)
        page_annotations = annotation['page']

        for page_index, page_annotation in enumerate(page_annotations):
            img = Image.open(p.img_path(book=book, index=page_index))

            num_annotations = 0
            for annotation_type in ["body", "face", "frame", "text"]:
                rois = page_annotation[annotation_type]
                num_annotations += len(rois)
                if args.draw_truth:
                    for roi in rois:
                        draw_rectangle(
                            img,
                            roi["@xmin"],
                            roi["@ymin"],
                            roi["@xmax"],
                            roi["@ymax"],
                            annotation_type,
                            width=args.rect_width1)

            if predictions and num_annotations > 0:
                page_predictions = predictions[prediction_index]
                for category_index, annotation_type in enumerate(["body", "face", "frame", "text"]):
                    for roi in page_predictions[category_index]:
                        xmin, ymin, xmax, ymax, score = roi
                        if score >= args.vis_score_thr1:
                            draw_rectangle(img, xmin, ymin, xmax, ymax, annotation_type, width=args.rect_width1)
                        elif score >= args.vis_score_thr2:
                            draw_rectangle(img, xmin, ymin, xmax, ymax, annotation_type, width=args.rect_width2)
                prediction_index += 1

            save_path = os.path.join(vis_book_dir, f"{page_index:03d}.jpg")
            img.save(save_path)
