import io
import json
import os
import re
import sys
import getopt
from typing import Union, Optional, Dict, Tuple
from uuid import uuid4

from PIL import Image
from pathlib import Path
from psd_tools import PSDImage
from psd_tools.api.layers import Layer, SmartObjectLayer
from psd_tools.api.smart_object import SmartObject
from psd_tools.constants import BlendMode
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.psd.tagged_blocks import TaggedBlock, PlacedLayerData

from psd_tools import compose

def truncate_prefix(name: str) -> str:
    return re.sub('mm_[^:]+:', '', name)


def get_transformation_dots(layer: Layer):
    if layer.has_clip_layers():
        for clip_layer in layer.clip_layers:
            coords = extract_smart_object(clip_layer)

            if coords is not None:
                if len(coords) > 0:
                    return coords


def extract_layer(layer: Layer) -> Dict[str, str]:
    item = {'id': str(uuid4()),
            'backgroundColor': '',
            'bounds': [layer.right,
                       layer.top,
                       layer.width,
                       layer.height],
            'layername': layer.name,
            'name': truncate_prefix(layer.name),
            'opacity': layer.opacity,
            'size': {
                'height': layer.height,
                'width': layer.width
            },
            'src': '',
            'type': 'normal',
            'visibility': layer.visible,
            'blendMode': layer.blend_mode.name,
            'position': {
                'x': layer.left,
                'y': layer.top
            },
            'transformation_dots': get_transformation_dots(layer)}

    if layer.has_clip_layers():
        item['child_objects'] = []
        for clip_layer in layer.clip_layers:
            item['child_objects'].append(extract_layer(clip_layer))

    return item


def unpack_placed_layer_data(item: PlacedLayerData) -> Tuple[float]:
    return item.transform


def unpack_tagged_block(block: TaggedBlock) -> Tuple[float]:
    if type(block.data) is PlacedLayerData:
        coords = unpack_placed_layer_data(block.data)

        if coords is not None:
            if len(coords) > 0:
                return coords


def extract_transformation_points(record: LayerRecord):
    for tagged_block_id, tagged_block in record.tagged_blocks.items():
        coords = unpack_tagged_block(tagged_block)

        if coords is not None:
            if len(coords) > 0:
                return coords


def extract_smart_object(layer: SmartObjectLayer):
    coords = extract_transformation_points(layer._record)

    if coords is not None:
        if len(coords) > 0:
            return coords


def save_layer_as_png(layer, dir_path: Path = Path('.')):
    if not dir_path.exists():
        dir_path.mkdir()

    if isinstance(layer, SmartObjectLayer):
        image = layer.topil()

        file_name = truncate_prefix(layer.name)
        image.save(f'{dir_path}/{file_name}.png')


def main(input_file: str, output_file: Optional[str] = None, dir_name: Path = Path('.')):
    image = PSDImage.open(input_file)

    data = {}
    data['layers'] = []
    for layer in image:
        item = extract_layer(layer)
        data['layers'].append(item)

        if layer.has_clip_layers():
            for clip_layer in layer.clip_layers:
                # if isinstance(clip_layer, SmartObjectLayer):
                save_layer_as_png(clip_layer, dir_name)
                # image = clip_layer.topil()
                # print(clip_layer.name)
                # print(image.save(f'data/{clip_layer.name}.png'))
                # clip_image = compose(clip_layer.smart_object)
                # print(clip_layer.)
                # clip_layer.save('data/image.png')



    if output_file:
        with open(output_file, 'w') as file:
            json.dump(data, file)
    else:
        print(json.dumps(data, indent=4, sort_keys=True))


if __name__ == "__main__":
    opts, argv = getopt.getopt(sys.argv[1:], "i:o:d:")

    input_file_name = None
    data_file_name = None
    output_dir_name = Path('.')

    for option, value in opts:
        if option == '-i':
            input_file_name = value
        if option == '-o':
            data_file_name = value
        if option == '-d':
            output_dir_name = Path(value)

    if not input_file_name:
        print('Type input file: -i example.psd')
    else:
        main(input_file_name, data_file_name, output_dir_name)
